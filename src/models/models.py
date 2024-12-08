from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional

@dataclass
class Violation:
    user_name: str
    violation_type: str
    timestamp: datetime
    details: str
    duration: Optional[timedelta] = None

@dataclass
class UserState:
    user_name: str
    is_working: bool = False
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    current_break: Optional[str] = None
    break_start_time: Optional[datetime] = None
    breaks: Dict[str, timedelta] = field(default_factory=lambda: {})
    break_counts: Dict[str, int] = field(default_factory=lambda: {})