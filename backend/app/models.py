from sqlalchemy import Column, Integer, String, DECIMAL, ForeignKey, Date, Time, TIMESTAMP, Boolean, Table
from sqlalchemy.orm import relationship
from datetime import date, datetime
from .database import Base

# Association Table for Many-to-Many between Employees and Roles
employee_roles = Table(
    'employee_roles', Base.metadata,
    Column('employee_id', Integer, ForeignKey('employees.id', ondelete="CASCADE"), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete="CASCADE"), primary_key=True)
)

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(50), nullable=False, unique=True)

class UserCredential(Base):
    __tablename__ = "user_credentials"
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), primary_key=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="credential")

class Schedule(Base):

    __tablename__ = "schedules"
    id = Column(Integer, primary_key=True, index=True)
    shift_name = Column(String(50), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    email = Column(String(150), nullable=False, unique=True)
    salary = Column(DECIMAL(10, 2), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False)
    schedule_id = Column(Integer, ForeignKey("schedules.id", ondelete="RESTRICT"), nullable=False)

    department = relationship("Department")
    schedule = relationship("Schedule")
    credential = relationship("UserCredential", back_populates="employee", uselist=False)
    roles = relationship("Role", secondary=employee_roles)

class SalaryHistory(Base):
    __tablename__ = "salary_history"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    new_salary = Column(DECIMAL(10, 2), nullable=False)
    change_date = Column(Date, nullable=False, default=date.today)

class AccessLog(Base):
    __tablename__ = "access_logs"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    log_date = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    event_type = Column(String(20), nullable=False)

class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default="Pending")

class Payslip(Base):
    __tablename__ = "payslips"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    period_month = Column(String(20), nullable=False)
    period_year = Column(Integer, nullable=False)
    net_salary_paid = Column(DECIMAL(10, 2), nullable=False)
