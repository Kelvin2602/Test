from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import configparser
from pathlib import Path

@dataclass
class Violation:
    user_name: str
    violation_type: str
    timestamp: datetime
    details: str
    duration: Optional[timedelta] = None

class ViolationManager:
    def __init__(self, config_path: Path = Path('config/config.ini')):
        self.violations: Dict[str, List[Violation]] = {}
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        
        # Đọc cấu hình từ config.ini
        self.break_durations = {
            k: int(v) for k, v in self.config['break_durations'].items()
        }
        self.break_frequencies = {
            k: int(v) for k, v in self.config['break_frequencies'].items()
        }
        self.working_hours = {
            'start': datetime.strptime(self.config['working_hours']['start_time'], '%H:%M').time(),
            'end': datetime.strptime(self.config['working_hours']['end_time'], '%H:%M').time()
        }

    def check_working_hours_violation(self, user_name: str, current_time: datetime) -> Optional[Violation]:
        """Kiểm tra vi phạm giờ làm việc"""
        current_time_only = current_time.time()
        if current_time_only < self.working_hours['start']:
            return Violation(
                user_name=user_name,
                violation_type="early_start",
                timestamp=current_time,
                details=f"Bắt đầu ca sớm hơn giờ quy định ({self.working_hours['start'].strftime('%H:%M')})"
            )
        elif current_time_only > self.working_hours['end']:
            return Violation(
                user_name=user_name,
                violation_type="late_end",
                timestamp=current_time,
                details=f"Kết thúc ca muộn hơn giờ quy định ({self.working_hours['end'].strftime('%H:%M')})"
            )
        return None

    def check_break_violations(self, user_name: str, break_type: str, 
                             start_time: datetime, end_time: datetime,
                             current_count: int) -> List[Violation]:
        """Kiểm tra vi phạm giờ nghỉ"""
        violations = []
        
        # Kiểm tra thời lượng nghỉ
        actual_duration = end_time - start_time
        allowed_duration = timedelta(minutes=self.break_durations[break_type])
        if actual_duration > allowed_duration:
            overtime = actual_duration - allowed_duration
            violations.append(Violation(
                user_name=user_name,
                violation_type="overtime_break",
                timestamp=end_time,
                details=f"Nghỉ {break_type} vượt {str(overtime).split('.')[0]} (cho phép {self.break_durations[break_type]} phút)",
                duration=overtime
            ))

        # Kiểm tra số lần nghỉ
        max_count = self.break_frequencies[break_type]
        if current_count > max_count:
            violations.append(Violation(
                user_name=user_name,
                violation_type="exceed_break_limit",
                timestamp=end_time,
                details=f"Vượt số lần nghỉ {break_type} ({current_count}/{max_count} lần/ca)"
            ))

        return violations

    def add_violations(self, violations: List[Violation]):
        """Thêm nhiều vi phạm cùng lúc"""
        for violation in violations:
            if violation.user_name not in self.violations:
                self.violations[violation.user_name] = []
            self.violations[violation.user_name].append(violation)

    def generate_violation_report(self, start_date: Optional[datetime] = None,
                                user_name: Optional[str] = None) -> str:
        """Tạo báo cáo vi phạm có lọc theo ngày và người dùng"""
        report = "📋 BÁO CÁO VI PHẠM\n\n"
        
        for name, user_violations in self.violations.items():
            if user_name and name != user_name:
                continue
                
            filtered_violations = user_violations
            if start_date:
                filtered_violations = [v for v in user_violations 
                                    if v.timestamp >= start_date]
            
            if filtered_violations:
                report += f"👤 {name}:\n"
                for violation in filtered_violations:
                    report += f"⚠️ {violation.timestamp.strftime('%H:%M:%S')} - {violation.details}\n"
                report += "\n"
                
        return report if len(report) > 20 else "✅ Không có vi phạm nào!"

    def get_user_violations_count(self, user_name: str, 
                                start_date: Optional[datetime] = None) -> Dict[str, int]:
        """Lấy số lượng vi phạm theo loại của một người dùng"""
        violations = self.violations.get(user_name, [])
        if start_date:
            violations = [v for v in violations if v.timestamp >= start_date]
            
        counts = {
            "overtime_break": 0,
            "exceed_break_limit": 0,
            "early_start": 0,
            "late_end": 0
        }
        
        for violation in violations:
            if violation.violation_type in counts:
                counts[violation.violation_type] += 1
                
        return counts