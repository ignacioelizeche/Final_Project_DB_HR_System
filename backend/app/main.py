from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta

from . import models, schemas, database, auth

app = FastAPI(title="HR & Access Control System API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optional: Ensure tables are created if not relying entirely on init.sql
# models.Base.metadata.create_all(bind=database.engine)

@app.get("/")
def read_root():
    return {"message": "Welcome to HR API"}

@app.get("/api/v1/health")
def health_check():
    return {"status": "Database connection and API are healthy"}

# --- AUTHENTICATION ---
@app.post("/api/v1/auth/login", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    employee = db.query(models.Employee).filter(models.Employee.email == form_data.username).first()
    if not employee or not employee.credential:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    
    if not auth.verify_password(form_data.password, employee.credential.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    roles = [role.role_name for role in employee.roles]
    access_token = auth.create_access_token(data={"sub": employee.email, "roles": roles})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/v1/auth/me", response_model=schemas.AuthUser)
def read_users_me(current_user: models.Employee = Depends(auth.get_current_user)):
    roles = [role.role_name for role in current_user.roles]
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "roles": roles
    }

# --- EMPLOYEES ---
@app.get("/api/v1/employees", response_model=List[schemas.EmployeeOut])
def list_employees(
    skip: int = 0, limit: int = 20, 
    db: Session = Depends(database.get_db),
    current_user: models.Employee = Depends(auth.get_current_user)
):
    employees = db.query(models.Employee).offset(skip).limit(limit).all()
    return employees

@app.post("/api/v1/employees", response_model=schemas.EmployeeOut)
def create_employee(
    employee: schemas.EmployeeCreate, 
    db: Session = Depends(database.get_db),
    current_user: models.Employee = Depends(auth.RoleChecker(["Admin", "HR"]))
):
    # Validar que el email no exista
    db_employee_exists = db.query(models.Employee).filter(models.Employee.email == employee.email).first()
    if db_employee_exists:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Crear el empleado (extraemos la data quitando password y roles)
    emp_data = employee.model_dump(exclude={"password", "role_names"})
    db_employee = models.Employee(**emp_data)
    
    # Asignar roles (asegurarnos que existen)
    for role_name in employee.role_names:
        role = db.query(models.Role).filter(models.Role.role_name == role_name).first()
        if not role:
            role = models.Role(role_name=role_name)
            db.add(role)
        db_employee.roles.append(role)
        
    db.add(db_employee)
    db.flush() # Para obtener ID del empleado antes de commitear

    # Crear las credenciales
    hashed_password = auth.get_password_hash(employee.password)
    user_cred = models.UserCredential(employee_id=db_employee.id, password_hash=hashed_password)
    db.add(user_cred)

    db.commit()
    db.refresh(db_employee)
    return db_employee

@app.get("/api/v1/employees/{id}", response_model=schemas.EmployeeOut)
def get_employee(
    id: int, db: Session = Depends(database.get_db),
    current_user: models.Employee = Depends(auth.get_current_user)
):

    employee = db.query(models.Employee).filter(models.Employee.id == id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

@app.patch("/api/v1/employees/{id}", response_model=schemas.EmployeeOut)
def update_employee(
    id: int, employee_update: schemas.EmployeeUpdate, 
    db: Session = Depends(database.get_db),
    current_user: models.Employee = Depends(auth.RoleChecker(["Admin", "HR"]))
):
    # Salary Modification Hook
    db_employee = db.query(models.Employee).filter(models.Employee.id == id).first()

    if not db_employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    if employee_update.salary is not None and employee_update.salary != db_employee.salary:
        # Register history
        salary_log = models.SalaryHistory(
            employee_id=db_employee.id,
            new_salary=employee_update.salary
        )
        db.add(salary_log)
        db_employee.salary = employee_update.salary

    db.commit()
    db.refresh(db_employee)
    return db_employee

# --- ACCESS LOGS ---
@app.post("/api/v1/access-logs", response_model=schemas.AccessLogOut)
def create_access_log(
    log: schemas.AccessLogCreate, 
    db: Session = Depends(database.get_db),
    current_user: models.Employee = Depends(auth.get_current_user)
):
    # Cross-reference caller id with the log payload to prevent logging in as someone else
    if current_user.id != log.employee_id:
        # Check if the user is an Admin/HR forcing a manual entry
        user_roles = [role.role_name for role in current_user.roles]
        if not any(role in ["Admin", "HR"] for role in user_roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot log access for another employee")

    # Access Log Validation
    last_log = db.query(models.AccessLog).filter(

        models.AccessLog.employee_id == log.employee_id
    ).order_by(models.AccessLog.log_date.desc()).first()

    if last_log and last_log.event_type == log.event_type:
        raise HTTPException(status_code=400, detail=f"Cannot sequentially {log.event_type} twice.")

    db_log = models.AccessLog(**log.model_dump())

    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

# --- LEAVE REQUESTS ---
@app.post("/api/v1/leave-requests", response_model=schemas.LeaveRequestOut)
def create_leave_request(request: schemas.LeaveRequestCreate, db: Session = Depends(database.get_db)):
    db_request = models.LeaveRequest(**request.model_dump())
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

@app.patch("/api/v1/leave-requests/{id}", response_model=schemas.LeaveRequestOut)
def update_leave_request(id: int, request_update: schemas.LeaveRequestUpdate, db: Session = Depends(database.get_db)):
    db_request = db.query(models.LeaveRequest).filter(models.LeaveRequest.id == id).first()
    if not db_request:
        raise HTTPException(status_code=404, detail="Leave Request not found")
    
    db_request.status = request_update.status
    db.commit()
    db.refresh(db_request)
    return db_request

# --- PAYSLIPS ---
@app.get("/api/v1/employees/{id}/payslips", response_model=List[schemas.PayslipOut])
def get_employee_payslips(
    id: int, 
    db: Session = Depends(database.get_db),
    current_user: models.Employee = Depends(auth.get_current_user)
):
    # RBAC Self-Service Verification
    user_roles = [role.role_name for role in current_user.roles]
    if current_user.id != id and not any(role in ["Admin", "HR"] for role in user_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Cannot access payslips of another employee"
        )

    payslips = db.query(models.Payslip).filter(models.Payslip.employee_id == id).all()
    return payslips

@app.post("/api/v1/payslips", response_model=schemas.PayslipOut)
def create_payslip(
    payslip: schemas.PayslipCreate,
    db: Session = Depends(database.get_db),
    current_user: models.Employee = Depends(auth.get_current_user)
):
    # RBAC check: only Admin/HR can create payslips
    user_roles = [role.role_name for role in current_user.roles]
    if not any(role in ["Admin", "HR"] for role in user_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admin or HR personnel can create payslips"
        )
    
    # Verify employee exists
    employee = db.query(models.Employee).filter(models.Employee.id == payslip.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Create payslip
    db_payslip = models.Payslip(**payslip.model_dump())
    db.add(db_payslip)
    db.commit()
    db.refresh(db_payslip)
    return db_payslip

# --- DEPARTMENTS & SCHEDULES ---
@app.get("/api/v1/departments", response_model=List[schemas.DepartmentOut])
def list_departments(db: Session = Depends(database.get_db), current_user: models.Employee = Depends(auth.get_current_user)):
    return db.query(models.Department).all()

@app.get("/api/v1/schedules", response_model=List[schemas.ScheduleOut])
def list_schedules(db: Session = Depends(database.get_db), current_user: models.Employee = Depends(auth.get_current_user)):
    return db.query(models.Schedule).all()

# --- ACCESS LOGS LIST ---
@app.get("/api/v1/access-logs", response_model=List[schemas.AccessLogOut])
def list_access_logs(
    db: Session = Depends(database.get_db),
    current_user: models.Employee = Depends(auth.get_current_user)
):
    user_roles = [role.role_name for role in current_user.roles]
    if any(role in ["Admin", "HR"] for role in user_roles):
        return db.query(models.AccessLog).order_by(models.AccessLog.log_date.desc()).all()
    return db.query(models.AccessLog).filter(models.AccessLog.employee_id == current_user.id).order_by(models.AccessLog.log_date.desc()).all()

# --- LEAVE REQUESTS LIST ---
@app.get("/api/v1/leave-requests", response_model=List[schemas.LeaveRequestOut])
def list_leave_requests(
    db: Session = Depends(database.get_db),
    current_user: models.Employee = Depends(auth.get_current_user)
):
    user_roles = [role.role_name for role in current_user.roles]
    if any(role in ["Admin", "HR"] for role in user_roles):
        return db.query(models.LeaveRequest).order_by(models.LeaveRequest.start_date.desc()).all()
    return db.query(models.LeaveRequest).filter(models.LeaveRequest.employee_id == current_user.id).order_by(models.LeaveRequest.start_date.desc()).all()


