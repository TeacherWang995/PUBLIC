"""
Course Scheduling System Integration
Complete system for managing and scheduling courses with real-time updates
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import threading
from abc import ABC, abstractmethod


# ============================================================================
# Enums and Constants
# ============================================================================

class CourseLevel(Enum):
    """Course difficulty levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ScheduleStatus(Enum):
    """Status of scheduled courses"""
    SCHEDULED = "scheduled"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ResourceType(Enum):
    """Types of resources needed for courses"""
    CLASSROOM = "classroom"
    LABORATORY = "laboratory"
    ONLINE = "online"
    HYBRID = "hybrid"


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class TimeSlot:
    """Represents a time slot for scheduling"""
    day_of_week: int  # 0-6 (Monday-Sunday)
    start_time: str  # HH:MM format
    end_time: str    # HH:MM format
    
    def to_dict(self):
        return asdict(self)
    
    @staticmethod
    def from_dict(data):
        return TimeSlot(**data)


@dataclass
class Resource:
    """Physical or virtual resource required for a course"""
    resource_id: str
    name: str
    resource_type: ResourceType
    capacity: int
    availability_hours: List[TimeSlot] = field(default_factory=list)
    
    def to_dict(self):
        data = asdict(self)
        data['resource_type'] = self.resource_type.value
        data['availability_hours'] = [ts.to_dict() for ts in self.availability_hours]
        return data
    
    @staticmethod
    def from_dict(data):
        resource_type = ResourceType(data['resource_type'])
        availability_hours = [TimeSlot.from_dict(ts) for ts in data.get('availability_hours', [])]
        return Resource(
            resource_id=data['resource_id'],
            name=data['name'],
            resource_type=resource_type,
            capacity=data['capacity'],
            availability_hours=availability_hours
        )


@dataclass
class Instructor:
    """Course instructor information"""
    instructor_id: str
    name: str
    email: str
    specialization: str
    available_slots: List[TimeSlot] = field(default_factory=list)
    max_students: int = 50
    
    def to_dict(self):
        return {
            'instructor_id': self.instructor_id,
            'name': self.name,
            'email': self.email,
            'specialization': self.specialization,
            'available_slots': [ts.to_dict() for ts in self.available_slots],
            'max_students': self.max_students
        }
    
    @staticmethod
    def from_dict(data):
        available_slots = [TimeSlot.from_dict(ts) for ts in data.get('available_slots', [])]
        return Instructor(
            instructor_id=data['instructor_id'],
            name=data['name'],
            email=data['email'],
            specialization=data['specialization'],
            available_slots=available_slots,
            max_students=data.get('max_students', 50)
        )


@dataclass
class Course:
    """Course information and metadata"""
    course_id: str
    name: str
    description: str
    level: CourseLevel
    instructor: Instructor
    duration_weeks: int
    capacity: int
    required_resources: List[Resource] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    schedule: Optional[TimeSlot] = None
    status: ScheduleStatus = ScheduleStatus.SCHEDULED
    enrolled_students: int = 0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self):
        return {
            'course_id': self.course_id,
            'name': self.name,
            'description': self.description,
            'level': self.level.value,
            'instructor': self.instructor.to_dict(),
            'duration_weeks': self.duration_weeks,
            'capacity': self.capacity,
            'required_resources': [r.to_dict() for r in self.required_resources],
            'prerequisites': self.prerequisites,
            'schedule': self.schedule.to_dict() if self.schedule else None,
            'status': self.status.value,
            'enrolled_students': self.enrolled_students,
            'created_at': self.created_at
        }
    
    @staticmethod
    def from_dict(data):
        level = CourseLevel(data['level'])
        status = ScheduleStatus(data['status'])
        instructor = Instructor.from_dict(data['instructor'])
        resources = [Resource.from_dict(r) for r in data.get('required_resources', [])]
        schedule = TimeSlot.from_dict(data['schedule']) if data.get('schedule') else None
        
        return Course(
            course_id=data['course_id'],
            name=data['name'],
            description=data['description'],
            level=level,
            instructor=instructor,
            duration_weeks=data['duration_weeks'],
            capacity=data['capacity'],
            required_resources=resources,
            prerequisites=data.get('prerequisites', []),
            schedule=schedule,
            status=status,
            enrolled_students=data.get('enrolled_students', 0),
            created_at=data.get('created_at', datetime.utcnow().isoformat())
        )


@dataclass
class ScheduleConflict:
    """Represents a scheduling conflict"""
    course_id: str
    conflict_type: str
    description: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# ============================================================================
# Abstract Base Classes
# ============================================================================

class Scheduler(ABC):
    """Abstract base class for scheduling algorithms"""
    
    @abstractmethod
    def schedule_course(self, course: Course, available_slots: List[TimeSlot]) -> Optional[TimeSlot]:
        """Schedule a course in an available time slot"""
        pass
    
    @abstractmethod
    def detect_conflicts(self, course: Course) -> List[ScheduleConflict]:
        """Detect scheduling conflicts for a course"""
        pass


class NotificationHandler(ABC):
    """Abstract base class for notifications"""
    
    @abstractmethod
    def notify(self, message: str, recipient: str):
        """Send notification to recipient"""
        pass


# ============================================================================
# Concrete Implementations
# ============================================================================

class GreedyScheduler(Scheduler):
    """Greedy scheduling algorithm - assigns first available slot"""
    
    def __init__(self):
        self.scheduled_slots = {}
    
    def schedule_course(self, course: Course, available_slots: List[TimeSlot]) -> Optional[TimeSlot]:
        """Schedule course to first available slot"""
        for slot in available_slots:
            if self._check_availability(course, slot):
                self.scheduled_slots[course.course_id] = slot
                return slot
        return None
    
    def _check_availability(self, course: Course, slot: TimeSlot) -> bool:
        """Check if slot is available for all requirements"""
        # Check instructor availability
        instructor_available = any(
            self._slots_overlap(slot, instr_slot) 
            for instr_slot in course.instructor.available_slots
        )
        
        if not instructor_available:
            return False
        
        # Check resource availability
        for resource in course.required_resources:
            resource_available = any(
                self._slots_overlap(slot, res_slot)
                for res_slot in resource.availability_hours
            )
            if not resource_available:
                return False
        
        return True
    
    def _slots_overlap(self, slot1: TimeSlot, slot2: TimeSlot) -> bool:
        """Check if two time slots overlap"""
        if slot1.day_of_week != slot2.day_of_week:
            return False
        return not (slot1.end_time <= slot2.start_time or slot1.start_time >= slot2.end_time)
    
    def detect_conflicts(self, course: Course) -> List[ScheduleConflict]:
        """Detect conflicts for the course"""
        conflicts = []
        
        if not course.schedule:
            conflicts.append(ScheduleConflict(
                course.course_id,
                "no_schedule",
                "Course has no schedule assigned"
            ))
            return conflicts
        
        # Check instructor conflict
        if course.instructor.available_slots:
            if not any(self._slots_overlap(course.schedule, slot) 
                      for slot in course.instructor.available_slots):
                conflicts.append(ScheduleConflict(
                    course.course_id,
                    "instructor_unavailable",
                    f"Instructor {course.instructor.name} is not available at scheduled time"
                ))
        
        # Check resource conflicts
        for resource in course.required_resources:
            if resource.availability_hours:
                if not any(self._slots_overlap(course.schedule, slot)
                          for slot in resource.availability_hours):
                    conflicts.append(ScheduleConflict(
                        course.course_id,
                        "resource_unavailable",
                        f"Resource '{resource.name}' is not available at scheduled time"
                    ))
        
        return conflicts


class EmailNotificationHandler(NotificationHandler):
    """Email-based notification handler"""
    
    def __init__(self):
        self.sent_notifications = []
    
    def notify(self, message: str, recipient: str):
        """Send email notification"""
        notification = {
            'timestamp': datetime.utcnow().isoformat(),
            'recipient': recipient,
            'message': message,
            'medium': 'email'
        }
        self.sent_notifications.append(notification)
        print(f"[EMAIL] To: {recipient}\n{message}")


class SlackNotificationHandler(NotificationHandler):
    """Slack-based notification handler"""
    
    def __init__(self):
        self.sent_notifications = []
    
    def notify(self, message: str, recipient: str):
        """Send Slack notification"""
        notification = {
            'timestamp': datetime.utcnow().isoformat(),
            'recipient': recipient,
            'message': message,
            'medium': 'slack'
        }
        self.sent_notifications.append(notification)
        print(f"[SLACK] To: {recipient}\n{message}")


# ============================================================================
# Main Scheduling System
# ============================================================================

class CourseSchedulingSystem:
    """Main system for managing course scheduling"""
    
    def __init__(self, scheduler: Scheduler = None):
        self.courses: Dict[str, Course] = {}
        self.resources: Dict[str, Resource] = {}
        self.instructors: Dict[str, Instructor] = {}
        self.scheduler = scheduler or GreedyScheduler()
        self.notification_handlers: List[NotificationHandler] = []
        self.conflict_history: List[ScheduleConflict] = []
        self.lock = threading.RLock()
    
    # ========================================================================
    # Resource Management
    # ========================================================================
    
    def add_resource(self, resource: Resource) -> bool:
        """Add a resource to the system"""
        with self.lock:
            if resource.resource_id in self.resources:
                print(f"Resource {resource.resource_id} already exists")
                return False
            self.resources[resource.resource_id] = resource
            print(f"Resource '{resource.name}' added successfully")
            return True
    
    def get_resource(self, resource_id: str) -> Optional[Resource]:
        """Get resource by ID"""
        return self.resources.get(resource_id)
    
    def list_resources(self, resource_type: Optional[ResourceType] = None) -> List[Resource]:
        """List all resources or filter by type"""
        resources = list(self.resources.values())
        if resource_type:
            resources = [r for r in resources if r.resource_type == resource_type]
        return resources
    
    # ========================================================================
    # Instructor Management
    # ========================================================================
    
    def register_instructor(self, instructor: Instructor) -> bool:
        """Register a new instructor"""
        with self.lock:
            if instructor.instructor_id in self.instructors:
                print(f"Instructor {instructor.instructor_id} already registered")
                return False
            self.instructors[instructor.instructor_id] = instructor
            print(f"Instructor '{instructor.name}' registered successfully")
            return True
    
    def get_instructor(self, instructor_id: str) -> Optional[Instructor]:
        """Get instructor by ID"""
        return self.instructors.get(instructor_id)
    
    def update_instructor_availability(self, instructor_id: str, slots: List[TimeSlot]) -> bool:
        """Update instructor availability"""
        with self.lock:
            instructor = self.instructors.get(instructor_id)
            if not instructor:
                print(f"Instructor {instructor_id} not found")
                return False
            instructor.available_slots = slots
            print(f"Updated availability for instructor {instructor_id}")
            return True
    
    # ========================================================================
    # Course Management
    # ========================================================================
    
    def create_course(self, name: str, description: str, level: CourseLevel,
                     instructor: Instructor, duration_weeks: int,
                     capacity: int, resources: List[Resource] = None) -> Course:
        """Create a new course"""
        with self.lock:
            course_id = str(uuid.uuid4())
            course = Course(
                course_id=course_id,
                name=name,
                description=description,
                level=level,
                instructor=instructor,
                duration_weeks=duration_weeks,
                capacity=capacity,
                required_resources=resources or []
            )
            self.courses[course_id] = course
            print(f"Course '{name}' created with ID {course_id}")
            return course
    
    def get_course(self, course_id: str) -> Optional[Course]:
        """Get course by ID"""
        return self.courses.get(course_id)
    
    def list_courses(self, level: Optional[CourseLevel] = None,
                    status: Optional[ScheduleStatus] = None) -> List[Course]:
        """List courses with optional filtering"""
        courses = list(self.courses.values())
        if level:
            courses = [c for c in courses if c.level == level]
        if status:
            courses = [c for c in courses if c.status == status]
        return courses
    
    # ========================================================================
    # Scheduling Operations
    # ========================================================================
    
    def schedule_course(self, course_id: str, preferred_slot: TimeSlot = None) -> Tuple[bool, str]:
        """Schedule a course and check for conflicts"""
        with self.lock:
            course = self.courses.get(course_id)
            if not course:
                return False, "Course not found"
            
            if course.status != ScheduleStatus.SCHEDULED:
                return False, f"Course status is {course.status.value}, cannot reschedule"
            
            # Generate available slots
            available_slots = self._generate_available_slots()
            
            # Schedule the course
            assigned_slot = self.scheduler.schedule_course(course, available_slots)
            
            if not assigned_slot:
                return False, "No available time slot found for this course"
            
            course.schedule = assigned_slot
            
            # Check for conflicts
            conflicts = self.scheduler.detect_conflicts(course)
            
            if conflicts:
                self.conflict_history.extend(conflicts)
                conflict_summary = "; ".join([c.description for c in conflicts])
                return False, f"Scheduling conflicts detected: {conflict_summary}"
            
            # Notify about successful scheduling
            self._notify_all(
                f"Course '{course.name}' has been scheduled successfully",
                course.instructor.email
            )
            
            return True, f"Course scheduled for {assigned_slot.day_of_week} {assigned_slot.start_time}-{assigned_slot.end_time}"
    
    def reschedule_course(self, course_id: str, new_slot: TimeSlot) -> Tuple[bool, str]:
        """Reschedule an existing course"""
        with self.lock:
            course = self.courses.get(course_id)
            if not course:
                return False, "Course not found"
            
            old_slot = course.schedule
            course.schedule = new_slot
            
            # Check for conflicts
            conflicts = self.scheduler.detect_conflicts(course)
            
            if conflicts:
                # Revert to old schedule
                course.schedule = old_slot
                self.conflict_history.extend(conflicts)
                return False, "Cannot reschedule: conflicts detected"
            
            # Notify about rescheduling
            self._notify_all(
                f"Course '{course.name}' has been rescheduled from {old_slot} to {new_slot}",
                course.instructor.email
            )
            
            return True, "Course rescheduled successfully"
    
    def start_course(self, course_id: str) -> Tuple[bool, str]:
        """Mark course as ongoing"""
        with self.lock:
            course = self.courses.get(course_id)
            if not course:
                return False, "Course not found"
            
            if course.status != ScheduleStatus.SCHEDULED:
                return False, f"Cannot start course with status {course.status.value}"
            
            course.status = ScheduleStatus.ONGOING
            self._notify_all(
                f"Course '{course.name}' has started",
                course.instructor.email
            )
            return True, "Course started successfully"
    
    def complete_course(self, course_id: str) -> Tuple[bool, str]:
        """Mark course as completed"""
        with self.lock:
            course = self.courses.get(course_id)
            if not course:
                return False, "Course not found"
            
            if course.status != ScheduleStatus.ONGOING:
                return False, f"Cannot complete course with status {course.status.value}"
            
            course.status = ScheduleStatus.COMPLETED
            self._notify_all(
                f"Course '{course.name}' has been completed",
                course.instructor.email
            )
            return True, "Course completed successfully"
    
    def cancel_course(self, course_id: str, reason: str = "") -> Tuple[bool, str]:
        """Cancel a course"""
        with self.lock:
            course = self.courses.get(course_id)
            if not course:
                return False, "Course not found"
            
            course.status = ScheduleStatus.CANCELLED
            message = f"Course '{course.name}' has been cancelled"
            if reason:
                message += f": {reason}"
            
            self._notify_all(message, course.instructor.email)
            return True, "Course cancelled successfully"
    
    # ========================================================================
    # Enrollment Management
    # ========================================================================
    
    def enroll_student(self, course_id: str, student_id: str) -> Tuple[bool, str]:
        """Enroll a student in a course"""
        with self.lock:
            course = self.courses.get(course_id)
            if not course:
                return False, "Course not found"
            
            if course.enrolled_students >= course.capacity:
                return False, "Course is at full capacity"
            
            course.enrolled_students += 1
            return True, f"Student {student_id} enrolled successfully"
    
    def get_course_capacity_info(self, course_id: str) -> Optional[Dict]:
        """Get capacity information for a course"""
        course = self.courses.get(course_id)
        if not course:
            return None
        
        return {
            'course_id': course_id,
            'course_name': course.name,
            'total_capacity': course.capacity,
            'enrolled_students': course.enrolled_students,
            'available_slots': course.capacity - course.enrolled_students,
            'occupancy_percent': (course.enrolled_students / course.capacity * 100)
        }
    
    # ========================================================================
    # Notification Management
    # ========================================================================
    
    def register_notification_handler(self, handler: NotificationHandler):
        """Register a notification handler"""
        self.notification_handlers.append(handler)
    
    def _notify_all(self, message: str, recipient: str):
        """Send notification through all registered handlers"""
        for handler in self.notification_handlers:
            handler.notify(message, recipient)
    
    # ========================================================================
    # Conflict Detection and Reporting
    # ========================================================================
    
    def get_course_conflicts(self, course_id: str) -> List[ScheduleConflict]:
        """Get all conflicts for a specific course"""
        return [c for c in self.conflict_history if c.course_id == course_id]
    
    def generate_conflict_report(self) -> Dict:
        """Generate a comprehensive conflict report"""
        conflicts_by_type = {}
        for conflict in self.conflict_history:
            conflict_type = conflict.conflict_type
            if conflict_type not in conflicts_by_type:
                conflicts_by_type[conflict_type] = []
            conflicts_by_type[conflict_type].append(conflict)
        
        return {
            'total_conflicts': len(self.conflict_history),
            'conflicts_by_type': {k: len(v) for k, v in conflicts_by_type.items()},
            'details': [asdict(c) for c in self.conflict_history]
        }
    
    # ========================================================================
    # Analytics and Reporting
    # ========================================================================
    
    def get_system_statistics(self) -> Dict:
        """Get overall system statistics"""
        total_capacity = sum(c.capacity for c in self.courses.values())
        total_enrolled = sum(c.enrolled_students for c in self.courses.values())
        
        status_counts = {}
        for course in self.courses.values():
            status = course.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        level_counts = {}
        for course in self.courses.values():
            level = course.level.value
            level_counts[level] = level_counts.get(level, 0) + 1
        
        return {
            'total_courses': len(self.courses),
            'total_instructors': len(self.instructors),
            'total_resources': len(self.resources),
            'total_capacity': total_capacity,
            'total_enrolled': total_enrolled,
            'occupancy_rate': total_enrolled / total_capacity * 100 if total_capacity > 0 else 0,
            'courses_by_status': status_counts,
            'courses_by_level': level_counts,
            'total_conflicts': len(self.conflict_history)
        }
    
    def export_system_state(self, filepath: str = "system_state.json"):
        """Export complete system state to JSON"""
        state = {
            'timestamp': datetime.utcnow().isoformat(),
            'courses': {cid: c.to_dict() for cid, c in self.courses.items()},
            'instructors': {iid: i.to_dict() for iid, i in self.instructors.items()},
            'resources': {rid: r.to_dict() for rid, r in self.resources.items()},
            'statistics': self.get_system_statistics(),
            'conflicts': self.generate_conflict_report()
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        print(f"System state exported to {filepath}")
        return state
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    def _generate_available_slots(self) -> List[TimeSlot]:
        """Generate list of potential time slots"""
        slots = []
        for day in range(5):  # Monday to Friday
            for hour in range(8, 18):  # 8 AM to 6 PM
                start_time = f"{hour:02d}:00"
                end_time = f"{hour + 1:02d}:00"
                slots.append(TimeSlot(day, start_time, end_time))
        return slots


# ============================================================================
# Usage Example and Demo
# ============================================================================

def demonstrate_system():
    """Demonstrate the course scheduling system"""
    
    print("=" * 80)
    print("COURSE SCHEDULING SYSTEM DEMO")
    print("=" * 80)
    
    # Initialize system
    system = CourseSchedulingSystem(scheduler=GreedyScheduler())
    
    # Register notification handlers
    system.register_notification_handler(EmailNotificationHandler())
    system.register_notification_handler(SlackNotificationHandler())
    
    # Add resources
    classroom_a = Resource(
        resource_id="room_001",
        name="Classroom A",
        resource_type=ResourceType.CLASSROOM,
        capacity=30,
        availability_hours=[
            TimeSlot(0, "08:00", "18:00"),
            TimeSlot(1, "08:00", "18:00"),
            TimeSlot(2, "08:00", "18:00"),
            TimeSlot(3, "08:00", "18:00"),
            TimeSlot(4, "08:00", "18:00")
        ]
    )
    system.add_resource(classroom_a)
    
    lab_a = Resource(
        resource_id="lab_001",
        name="Computer Lab A",
        resource_type=ResourceType.LABORATORY,
        capacity=20,
        availability_hours=[
            TimeSlot(0, "09:00", "17:00"),
            TimeSlot(2, "09:00", "17:00"),
            TimeSlot(4, "09:00", "17:00")
        ]
    )
    system.add_resource(lab_a)
    
    # Register instructors
    instructor1 = Instructor(
        instructor_id="instr_001",
        name="Dr. Smith",
        email="smith@example.com",
        specialization="Python Programming",
        available_slots=[
            TimeSlot(0, "08:00", "12:00"),
            TimeSlot(1, "08:00", "12:00"),
            TimeSlot(2, "08:00", "12:00"),
            TimeSlot(3, "08:00", "12:00"),
            TimeSlot(4, "08:00", "12:00")
        ],
        max_students=30
    )
    system.register_instructor(instructor1)
    
    instructor2 = Instructor(
        instructor_id="instr_002",
        name="Prof. Johnson",
        email="johnson@example.com",
        specialization="Data Science",
        available_slots=[
            TimeSlot(0, "14:00", "18:00"),
            TimeSlot(2, "14:00", "18:00"),
            TimeSlot(4, "14:00", "18:00")
        ],
        max_students=25
    )
    system.register_instructor(instructor2)
    
    # Create courses
    python_course = system.create_course(
        name="Python Programming Basics",
        description="Learn Python fundamentals",
        level=CourseLevel.BEGINNER,
        instructor=instructor1,
        duration_weeks=8,
        capacity=30,
        resources=[classroom_a]
    )
    
    data_science_course = system.create_course(
        name="Data Science with Python",
        description="Advanced data science techniques",
        level=CourseLevel.ADVANCED,
        instructor=instructor2,
        duration_weeks=12,
        capacity=25,
        resources=[lab_a, classroom_a]
    )
    
    # Schedule courses
    print("\n" + "-" * 80)
    print("SCHEDULING COURSES")
    print("-" * 80)
    
    success, msg = system.schedule_course(python_course.course_id)
    print(f"Python Course: {msg}")
    
    success, msg = system.schedule_course(data_science_course.course_id)
    print(f"Data Science Course: {msg}")
    
    # Enroll students
    print("\n" + "-" * 80)
    print("ENROLLING STUDENTS")
    print("-" * 80)
    
    for i in range(1, 6):
        success, msg = system.enroll_student(python_course.course_id, f"student_{i}")
        print(f"Python Course - {msg}")
    
    for i in range(1, 4):
        success, msg = system.enroll_student(data_science_course.course_id, f"student_{i+10}")
        print(f"Data Science Course - {msg}")
    
    # Get capacity info
    print("\n" + "-" * 80)
    print("CAPACITY INFORMATION")
    print("-" * 80)
    
    for course_id in [python_course.course_id, data_science_course.course_id]:
        capacity_info = system.get_course_capacity_info(course_id)
        print(f"\n{capacity_info['course_name']}:")
        print(f"  Total Capacity: {capacity_info['total_capacity']}")
        print(f"  Enrolled: {capacity_info['enrolled_students']}")
        print(f"  Available: {capacity_info['available_slots']}")
        print(f"  Occupancy: {capacity_info['occupancy_percent']:.1f}%")
    
    # Start and complete courses
    print("\n" + "-" * 80)
    print("COURSE STATUS UPDATES")
    print("-" * 80)
    
    success, msg = system.start_course(python_course.course_id)
    print(f"Start Python Course: {msg}")
    
    success, msg = system.complete_course(python_course.course_id)
    print(f"Complete Python Course: {msg}")
    
    # Generate reports
    print("\n" + "-" * 80)
    print("SYSTEM STATISTICS")
    print("-" * 80)
    
    stats = system.get_system_statistics()
    print(f"\nTotal Courses: {stats['total_courses']}")
    print(f"Total Instructors: {stats['total_instructors']}")
    print(f"Total Resources: {stats['total_resources']}")
    print(f"Total Capacity: {stats['total_capacity']}")
    print(f"Total Enrolled: {stats['total_enrolled']}")
    print(f"Overall Occupancy: {stats['occupancy_rate']:.1f}%")
    print(f"\nCourses by Status: {stats['courses_by_status']}")
    print(f"Courses by Level: {stats['courses_by_level']}")
    print(f"Total Conflicts: {stats['total_conflicts']}")
    
    # Export system state
    print("\n" + "-" * 80)
    print("EXPORTING SYSTEM STATE")
    print("-" * 80)
    system.export_system_state()
    
    print("\n" + "=" * 80)
    print("DEMO COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    demonstrate_system()
