from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional

@dataclass
class UserState:
    user_name: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    current_break: Optional[str] = None
    break_start_time: Optional[datetime] = None
    breaks: Dict[str, timedelta] = field(default_factory=lambda: {})
    is_working: bool = False
    break_counts: Dict[str, int] = field(default_factory=lambda: {}) 