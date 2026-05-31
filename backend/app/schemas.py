from pydantic import BaseModel, EmailStr
from datetime import date, datetime, time
from typing import Optional, List
from decimal import Decimal


# Employee Schemas
class EmployeeBase(BaseModel):
    name: str
    email: EmailStr
    salary: Decimal
    department_id: int
    schedule_id: int

class EmployeeCreate(EmployeeBase):
    password: str
    role_names: List[str] = ["Employee"]

class EmployeeUpdate(BaseModel):

    salary: Optional[Decimal] = None

class EmployeeOut(EmployeeBase):
    id: int

    class Config:
        from_attributes = True

# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class AuthUser(BaseModel):
    id: int
    name: str
    email: str
    roles: List[str]

    class Config:
        from_attributes = True

# Access Log Schemas
class AccessLogCreate(BaseModel):
    employee_id: int
    event_type: str

class AccessLogOut(AccessLogCreate):
    id: int
    log_date: datetime

    class Config:
        from_attributes = True

# Leave Request Schemas
class LeaveRequestCreate(BaseModel):
    employee_id: int
    type: str
    start_date: date
    end_date: date

class LeaveRequestUpdate(BaseModel):
    status: str

class LeaveRequestOut(LeaveRequestCreate):
    id: int
    status: str

    class Config:
        from_attributes = True

# Payslip Schemas
class PayslipOut(BaseModel):
    id: int
    employee_id: int
    period_month: str
    period_year: int
    net_salary_paid: Decimal

    class Config:
        from_attributes = True

# Department Schemas
class DepartmentOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

# Schedule Schemas
class ScheduleOut(BaseModel):
    id: int
    shift_name: str
    start_time: time
    end_time: time

    class Config:
        from_attributes = True

