"""
Course Scheduling Engine with Constraint Validation System

This module implements the core scheduling logic for the course scheduling system,
including constraint validation, conflict detection, and schedule optimization.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional
from enum import Enum
from datetime import datetime, time, timedelta
import json


class DayOfWeek(Enum):
    """Days of the week enumeration."""
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class ConstraintType(Enum):
    """Types of scheduling constraints."""
    HARD = "hard"  # Must be satisfied
    SOFT = "soft"  # Should be satisfied but can be violated


@dataclass
class TimeSlot:
    """Represents a time slot for scheduling."""
    day: DayOfWeek
    start_time: time
    end_time: time

    def overlaps_with(self, other: 'TimeSlot') -> bool:
        """Check if this time slot overlaps with another."""
        if self.day != other.day:
            return False
        return not (self.end_time <= other.start_time or self.start_time >= other.end_time)

    def duration_minutes(self) -> int:
        """Calculate duration in minutes."""
        start_minutes = self.start_time.hour * 60 + self.start_time.minute
        end_minutes = self.end_time.hour * 60 + self.end_time.minute
        return end_minutes - start_minutes

    def __hash__(self):
        return hash((self.day, self.start_time, self.end_time))

    def __eq__(self, other):
        if not isinstance(other, TimeSlot):
            return False
        return (self.day == other.day and 
                self.start_time == other.start_time and 
                self.end_time == other.end_time)


@dataclass
class Instructor:
    """Represents an instructor."""
    instructor_id: str
    name: str
    unavailable_slots: List[TimeSlot] = field(default_factory=list)
    max_hours_per_week: float = 40.0
    preferred_time_slots: List[TimeSlot] = field(default_factory=list)

    def is_available(self, time_slot: TimeSlot) -> bool:
        """Check if instructor is available at given time slot."""
        for unavailable in self.unavailable_slots:
            if time_slot.overlaps_with(unavailable):
                return False
        return True

    def get_weekly_hours(self, schedule: 'Schedule') -> float:
        """Calculate total scheduled hours for the week."""
        total_hours = 0.0
        for course_schedule in schedule.get_instructor_courses(self.instructor_id):
            total_hours += course_schedule.time_slot.duration_minutes() / 60.0
        return total_hours


@dataclass
class Classroom:
    """Represents a classroom resource."""
    room_id: str
    name: str
    capacity: int
    available_slots: List[TimeSlot] = field(default_factory=list)
    special_equipment: Set[str] = field(default_factory=set)

    def is_available(self, time_slot: TimeSlot) -> bool:
        """Check if classroom is available at given time slot."""
        if not self.available_slots:
            return True

        for available in self.available_slots:
            if time_slot.day == available.day:
                if (time_slot.start_time >= available.start_time and 
                    time_slot.end_time <= available.end_time):
                    return True
        return False

    def has_equipment(self, required_equipment: Set[str]) -> bool:
        """Check if classroom has required equipment."""
        return required_equipment.issubset(self.special_equipment)


@dataclass
class Course:
    """Represents a course to be scheduled."""
    course_id: str
    name: str
    instructor_id: str
    required_capacity: int
    duration_minutes: int
    preferred_days: List[DayOfWeek] = field(default_factory=list)
    required_equipment: Set[str] = field(default_factory=set)
    sessions_per_week: int = 1
    constraints: Dict[str, Tuple[ConstraintType, str]] = field(default_factory=dict)

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate course data."""
        errors = []
        if not self.course_id or not self.name:
            errors.append("Course must have ID and name")
        if self.required_capacity <= 0:
            errors.append("Course capacity must be positive")
        if self.duration_minutes <= 0:
            errors.append("Course duration must be positive")
        if self.sessions_per_week < 1:
            errors.append("Course must have at least 1 session per week")
        return len(errors) == 0, errors


@dataclass
class CourseSchedule:
    """Represents a scheduled course."""
    course: Course
    instructor: Instructor
    classroom: Classroom
    time_slot: TimeSlot
    scheduled_date: datetime = field(default_factory=datetime.utcnow)

    def __hash__(self):
        return hash((self.course.course_id, self.time_slot))

    def __eq__(self, other):
        if not isinstance(other, CourseSchedule):
            return False
        return (self.course.course_id == other.course.course_id and 
                self.time_slot == other.time_slot)


class ConstraintValidator:
    """Validates scheduling constraints and conflicts."""

    @staticmethod
    def validate_instructor_availability(
        instructor: Instructor,
        time_slot: TimeSlot
    ) -> Tuple[bool, Optional[str]]:
        """Validate instructor is available at time slot."""
        if not instructor.is_available(time_slot):
            return False, f"Instructor {instructor.name} is unavailable at {time_slot.day.name} {time_slot.start_time}-{time_slot.end_time}"
        return True, None

    @staticmethod
    def validate_classroom_availability(
        classroom: Classroom,
        time_slot: TimeSlot
    ) -> Tuple[bool, Optional[str]]:
        """Validate classroom is available at time slot."""
        if not classroom.is_available(time_slot):
            return False, f"Classroom {classroom.name} is unavailable at {time_slot.day.name} {time_slot.start_time}-{time_slot.end_time}"
        return True, None

    @staticmethod
    def validate_classroom_capacity(
        classroom: Classroom,
        course: Course
    ) -> Tuple[bool, Optional[str]]:
        """Validate classroom has sufficient capacity."""
        if classroom.capacity < course.required_capacity:
            return False, f"Classroom {classroom.name} capacity ({classroom.capacity}) is less than required ({course.required_capacity})"
        return True, None

    @staticmethod
    def validate_classroom_equipment(
        classroom: Classroom,
        course: Course
    ) -> Tuple[bool, Optional[str]]:
        """Validate classroom has required equipment."""
        if not classroom.has_equipment(course.required_equipment):
            missing = course.required_equipment - classroom.special_equipment
            return False, f"Classroom {classroom.name} missing equipment: {missing}"
        return True, None

    @staticmethod
    def validate_instructor_hours(
        instructor: Instructor,
        course_schedule: CourseSchedule,
        schedule: 'Schedule'
    ) -> Tuple[bool, Optional[str]]:
        """Validate instructor doesn't exceed max hours."""
        new_total = instructor.get_weekly_hours(schedule) + course_schedule.time_slot.duration_minutes() / 60.0
        if new_total > instructor.max_hours_per_week:
            return False, f"Instructor {instructor.name} would exceed max hours ({new_total} > {instructor.max_hours_per_week})"
        return True, None

    @staticmethod
    def validate_no_instructor_conflicts(
        instructor: Instructor,
        time_slot: TimeSlot,
        schedule: 'Schedule'
    ) -> Tuple[bool, Optional[str]]:
        """Validate instructor has no scheduling conflicts."""
        for course_schedule in schedule.get_instructor_courses(instructor.instructor_id):
            if time_slot.overlaps_with(course_schedule.time_slot):
                return False, f"Instructor {instructor.name} has conflict at {time_slot.day.name} {time_slot.start_time}-{time_slot.end_time}"
        return True, None

    @staticmethod
    def validate_no_classroom_conflicts(
        classroom: Classroom,
        time_slot: TimeSlot,
        schedule: 'Schedule'
    ) -> Tuple[bool, Optional[str]]:
        """Validate classroom is not double-booked."""
        for course_schedule in schedule.get_classroom_courses(classroom.room_id):
            if time_slot.overlaps_with(course_schedule.time_slot):
                return False, f"Classroom {classroom.name} is double-booked at {time_slot.day.name} {time_slot.start_time}-{time_slot.end_time}"
        return True, None

    @staticmethod
    def validate_preferred_days(
        course: Course,
        time_slot: TimeSlot
    ) -> Tuple[bool, Optional[str]]:
        """Validate course is scheduled on preferred days if specified."""
        if course.preferred_days and time_slot.day not in course.preferred_days:
            return False, f"Course {course.name} scheduled on non-preferred day {time_slot.day.name}"
        return True, None


class Schedule:
    """Manages the overall course schedule."""

    def __init__(self):
        """Initialize schedule."""
        self.courses: Dict[str, CourseSchedule] = {}
        self.validation_errors: List[str] = []
        self.validation_warnings: List[str] = []

    def add_course(
        self,
        course: Course,
        instructor: Instructor,
        classroom: Classroom,
        time_slot: TimeSlot,
        validate_constraints: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """
        Add a course to the schedule with validation.
        
        Returns:
            Tuple of (success, error_message)
        """
        course_schedule = CourseSchedule(course, instructor, classroom, time_slot)

        if validate_constraints:
            is_valid, error_msg = self._validate_course_schedule(course_schedule)
            if not is_valid:
                self.validation_errors.append(error_msg)
                return False, error_msg

        self.courses[course.course_id] = course_schedule
        return True, None

    def _validate_course_schedule(self, course_schedule: CourseSchedule) -> Tuple[bool, Optional[str]]:
        """Validate a course schedule against all constraints."""
        # Validate course data
        is_valid, errors = course_schedule.course.validate()
        if not errors:
            return False, "; ".join(errors)

        # Validate instructor availability
        is_valid, error = ConstraintValidator.validate_instructor_availability(
            course_schedule.instructor,
            course_schedule.time_slot
        )
        if not is_valid:
            return False, error

        # Validate classroom availability
        is_valid, error = ConstraintValidator.validate_classroom_availability(
            course_schedule.classroom,
            course_schedule.time_slot
        )
        if not is_valid:
            return False, error

        # Validate classroom capacity
        is_valid, error = ConstraintValidator.validate_classroom_capacity(
            course_schedule.classroom,
            course_schedule.course
        )
        if not is_valid:
            return False, error

        # Validate classroom equipment
        is_valid, error = ConstraintValidator.validate_classroom_equipment(
            course_schedule.classroom,
            course_schedule.course
        )
        if not is_valid:
            return False, error

        # Validate instructor hours
        is_valid, error = ConstraintValidator.validate_instructor_hours(
            course_schedule.instructor,
            course_schedule,
            self
        )
        if not is_valid:
            return False, error

        # Validate no instructor conflicts
        is_valid, error = ConstraintValidator.validate_no_instructor_conflicts(
            course_schedule.instructor,
            course_schedule.time_slot,
            self
        )
        if not is_valid:
            return False, error

        # Validate no classroom conflicts
        is_valid, error = ConstraintValidator.validate_no_classroom_conflicts(
            course_schedule.classroom,
            course_schedule.time_slot,
            self
        )
        if not is_valid:
            return False, error

        # Check soft constraint: preferred days
        is_valid, warning = ConstraintValidator.validate_preferred_days(
            course_schedule.course,
            course_schedule.time_slot
        )
        if not is_valid:
            self.validation_warnings.append(warning)

        return True, None

    def remove_course(self, course_id: str) -> bool:
        """Remove a course from the schedule."""
        if course_id in self.courses:
            del self.courses[course_id]
            return True
        return False

    def get_instructor_courses(self, instructor_id: str) -> List[CourseSchedule]:
        """Get all courses scheduled for an instructor."""
        return [cs for cs in self.courses.values() 
                if cs.instructor.instructor_id == instructor_id]

    def get_classroom_courses(self, room_id: str) -> List[CourseSchedule]:
        """Get all courses scheduled for a classroom."""
        return [cs for cs in self.courses.values() 
                if cs.classroom.room_id == room_id]

    def get_courses_by_day(self, day: DayOfWeek) -> List[CourseSchedule]:
        """Get all courses scheduled for a specific day."""
        return [cs for cs in self.courses.values() 
                if cs.time_slot.day == day]

    def check_instructor_conflicts(self, instructor_id: str) -> List[Tuple[CourseSchedule, CourseSchedule]]:
        """Find all scheduling conflicts for an instructor."""
        courses = self.get_instructor_courses(instructor_id)
        conflicts = []
        for i, course1 in enumerate(courses):
            for course2 in courses[i + 1:]:
                if course1.time_slot.overlaps_with(course2.time_slot):
                    conflicts.append((course1, course2))
        return conflicts

    def check_classroom_conflicts(self, room_id: str) -> List[Tuple[CourseSchedule, CourseSchedule]]:
        """Find all double-booking conflicts for a classroom."""
        courses = self.get_classroom_courses(room_id)
        conflicts = []
        for i, course1 in enumerate(courses):
            for course2 in courses[i + 1:]:
                if course1.time_slot.overlaps_with(course2.time_slot):
                    conflicts.append((course1, course2))
        return conflicts

    def get_schedule_summary(self) -> Dict:
        """Generate a summary of the current schedule."""
        summary = {
            "total_courses": len(self.courses),
            "by_day": {},
            "by_instructor": {},
            "by_classroom": {},
            "conflicts": {
                "instructor": [],
                "classroom": []
            }
        }

        # Courses by day
        for day in DayOfWeek:
            day_courses = self.get_courses_by_day(day)
            if day_courses:
                summary["by_day"][day.name] = len(day_courses)

        # Courses by instructor
        instructors = set(cs.instructor.instructor_id for cs in self.courses.values())
        for instructor_id in instructors:
            courses = self.get_instructor_courses(instructor_id)
            summary["by_instructor"][instructor_id] = len(courses)

        # Courses by classroom
        classrooms = set(cs.classroom.room_id for cs in self.courses.values())
        for room_id in classrooms:
            courses = self.get_classroom_courses(room_id)
            summary["by_classroom"][room_id] = len(courses)

        # Check for conflicts
        for instructor_id in instructors:
            conflicts = self.check_instructor_conflicts(instructor_id)
            if conflicts:
                summary["conflicts"]["instructor"].append({
                    "instructor_id": instructor_id,
                    "conflict_count": len(conflicts)
                })

        for room_id in classrooms:
            conflicts = self.check_classroom_conflicts(room_id)
            if conflicts:
                summary["conflicts"]["classroom"].append({
                    "room_id": room_id,
                    "conflict_count": len(conflicts)
                })

        return summary

    def export_to_json(self) -> str:
        """Export schedule to JSON format."""
        schedule_dict = {
            "courses": []
        }
        for course_schedule in self.courses.values():
            schedule_dict["courses"].append({
                "course_id": course_schedule.course.course_id,
                "course_name": course_schedule.course.name,
                "instructor_id": course_schedule.instructor.instructor_id,
                "instructor_name": course_schedule.instructor.name,
                "classroom_id": course_schedule.classroom.room_id,
                "classroom_name": course_schedule.classroom.name,
                "day": course_schedule.time_slot.day.name,
                "start_time": course_schedule.time_slot.start_time.isoformat(),
                "end_time": course_schedule.time_slot.end_time.isoformat(),
                "duration_minutes": course_schedule.time_slot.duration_minutes(),
                "scheduled_date": course_schedule.scheduled_date.isoformat()
            })
        return json.dumps(schedule_dict, indent=2)

    def is_valid(self) -> bool:
        """Check if the schedule is valid (no hard constraint violations)."""
        return len(self.validation_errors) == 0

    def get_validation_report(self) -> Dict:
        """Generate a validation report."""
        return {
            "is_valid": self.is_valid(),
            "errors": self.validation_errors,
            "warnings": self.validation_warnings,
            "total_courses": len(self.courses),
            "summary": self.get_schedule_summary()
        }
