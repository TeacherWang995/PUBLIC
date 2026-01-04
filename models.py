"""
Data models for the comprehensive course scheduling system.
Handles teacher, class, subject, period, and scheduling data structures.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Set, Dict
from datetime import datetime
from enum import Enum


class CourseAssignmentMode(Enum):
    """Different modes for course assignment."""
    SCHOOL_WIDE = "school_wide"
    CROSS_CLASS = "cross_class"
    SPECIAL_NEEDS = "special_needs"
    BINDING_CLASS = "binding_class"


class ConstraintType(Enum):
    """Types of scheduling constraints."""
    HARD = "hard"  # Must be satisfied
    SOFT = "soft"  # Should be satisfied if possible


@dataclass
class Teacher:
    """Represents a teacher in the system."""
    teacher_id: str
    name: str
    subject_codes: List[str] = field(default_factory=list)
    max_daily_periods: int = 6
    unavailable_periods: Set[str] = field(default_factory=set)  # Format: "day_period"
    preferred_periods: Set[str] = field(default_factory=set)
    special_rooms: List[str] = field(default_factory=list)
    groups: List[str] = field(default_factory=list)  # Teaching groups
    max_weekly_hours: int = 24
    constraints: Dict[str, str] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.teacher_id)

    def __eq__(self, other):
        if isinstance(other, Teacher):
            return self.teacher_id == other.teacher_id
        return False


@dataclass
class SchoolClass:
    """Represents a class in the school."""
    class_id: str
    name: str
    grade: int
    total_students: int
    special_needs_count: int = 0
    available_rooms: List[str] = field(default_factory=list)
    unavailable_periods: Set[str] = field(default_factory=set)  # Format: "day_period"
    constraints: Dict[str, str] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.class_id)

    def __eq__(self, other):
        if isinstance(other, SchoolClass):
            return self.class_id == other.class_id
        return False


@dataclass
class Subject:
    """Represents a subject."""
    subject_code: str
    name: str
    weekly_periods: int
    min_consecutive_periods: int = 1
    max_consecutive_periods: int = 2
    requires_special_room: bool = False
    special_room_type: Optional[str] = None

    def __hash__(self):
        return hash(self.subject_code)

    def __eq__(self, other):
        if isinstance(other, Subject):
            return self.subject_code == other.subject_code
        return False


@dataclass
class Period:
    """Represents a time period in the schedule."""
    period_id: str
    day: str  # Monday, Tuesday, etc.
    period_number: int
    start_time: str  # HH:MM
    end_time: str    # HH:MM
    duration_minutes: int = 45

    def __hash__(self):
        return hash(self.period_id)

    def __eq__(self, other):
        if isinstance(other, Period):
            return self.period_id == other.period_id
        return False


@dataclass
class Room:
    """Represents a classroom or special room."""
    room_id: str
    name: str
    room_type: str  # "classroom", "lab", "gym", "music_room", etc.
    capacity: int
    special_equipment: List[str] = field(default_factory=list)
    unavailable_periods: Set[str] = field(default_factory=set)  # Format: "day_period"

    def __hash__(self):
        return hash(self.room_id)

    def __eq__(self, other):
        if isinstance(other, Room):
            return self.room_id == other.room_id
        return False


@dataclass
class Course:
    """Represents a course assignment (teacher teaching subject to class)."""
    course_id: str
    teacher: Teacher
    school_class: SchoolClass
    subject: Subject
    weekly_periods: int
    assignment_mode: CourseAssignmentMode
    binding_courses: List[str] = field(default_factory=list)  # For binding class mode
    groups: List[str] = field(default_factory=list)  # Student groups for special needs
    priority: int = 1  # 1=high, 2=medium, 3=low


@dataclass
class ScheduledSlot:
    """Represents a scheduled course slot."""
    slot_id: str
    course: Course
    period: Period
    room: Room
    assigned_date: datetime
    groups_assigned: List[str] = field(default_factory=list)

    def __hash__(self):
        return hash(self.slot_id)

    def __eq__(self, other):
        if isinstance(other, ScheduledSlot):
            return self.slot_id == other.slot_id
        return False


@dataclass
class SchedulingConstraint:
    """Represents a scheduling constraint."""
    constraint_id: str
    name: str
    description: str
    constraint_type: ConstraintType
    affected_entities: List[str]  # teacher_id, class_id, etc.
    rule: str  # Description of the rule
    weight: float = 1.0  # For soft constraints, weight in optimization


@dataclass
class Schedule:
    """Represents the complete schedule."""
    schedule_id: str
    name: str
    school_year: str
    term: int
    created_date: datetime
    modified_date: datetime
    scheduled_slots: List[ScheduledSlot] = field(default_factory=list)
    constraints_satisfied: Dict[str, bool] = field(default_factory=dict)
    unscheduled_courses: List[Course] = field(default_factory=list)
    collision_report: Dict[str, List[str]] = field(default_factory=dict)
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class AdjustmentRequest:
    """Represents a manual adjustment request."""
    adjustment_id: str
    slot_id: str
    new_period: Period
    new_room: Room
    requested_date: datetime
    reason: str
    approved: bool = False
    collision_detected: bool = False
    collision_details: List[str] = field(default_factory=list)
