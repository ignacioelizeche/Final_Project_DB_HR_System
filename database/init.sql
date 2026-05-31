-- 1. Independent Lookup Tables
CREATE TABLE SCHEDULES (
    id SERIAL PRIMARY KEY,
    shift_name VARCHAR(50) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL
);

CREATE TABLE DEPARTMENTS (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

-- 2. Core Entity Table
CREATE TABLE EMPLOYEES (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    salary DECIMAL(10, 2) NOT NULL,
    department_id INT NOT NULL REFERENCES DEPARTMENTS(id) ON DELETE RESTRICT,
    schedule_id INT NOT NULL REFERENCES SCHEDULES(id) ON DELETE RESTRICT
);

-- 3. Dependent Transactional / Historical Tables
CREATE TABLE SALARY_HISTORY (
    id SERIAL PRIMARY KEY,
    employee_id INT NOT NULL REFERENCES EMPLOYEES(id) ON DELETE CASCADE,
    new_salary DECIMAL(10, 2) NOT NULL,
    change_date DATE NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE ACCESS_LOGS (
    id SERIAL PRIMARY KEY,
    employee_id INT NOT NULL REFERENCES EMPLOYEES(id) ON DELETE CASCADE,
    log_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    event_type VARCHAR(20) NOT NULL -- 'Check-In', 'Check-Out'
);

CREATE TABLE LEAVE_REQUESTS (
    id SERIAL PRIMARY KEY,
    employee_id INT NOT NULL REFERENCES EMPLOYEES(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,     -- 'Medical', 'Vacation', 'Personal'
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending' -- 'Pending', 'Approved', 'Rejected'
);

CREATE TABLE PAYSLIPS (
    id SERIAL PRIMARY KEY,
    employee_id INT NOT NULL REFERENCES EMPLOYEES(id) ON DELETE CASCADE,
    period_month VARCHAR(20) NOT NULL,
    period_year INT NOT NULL,
    net_salary_paid DECIMAL(10, 2) NOT NULL
);

-- 4. Authentication & Security Tables
CREATE TABLE ROLES (
    id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL UNIQUE -- 'Admin', 'HR', 'Employee'
);

CREATE TABLE USER_CREDENTIALS (
    employee_id INT PRIMARY KEY REFERENCES EMPLOYEES(id) ON DELETE CASCADE,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE EMPLOYEE_ROLES (
    employee_id INT REFERENCES EMPLOYEES(id) ON DELETE CASCADE,
    role_id INT REFERENCES ROLES(id) ON DELETE CASCADE,
    PRIMARY KEY (employee_id, role_id)
);

-- 5. Seed Data: Lookup data required by FK constraints
INSERT INTO ROLES (role_name) VALUES ('Admin'), ('HR'), ('Employee');

INSERT INTO DEPARTMENTS (name) VALUES 
('Administration'),
('Human Resources'),
('Engineering'),
('Marketing'),
('Finance');

INSERT INTO SCHEDULES (shift_name, start_time, end_time) VALUES 
('Morning', '08:00:00', '16:00:00'),
('Afternoon', '16:00:00', '00:00:00'),
('Night', '00:00:00', '08:00:00');

-- 6. Seed Data: Employees
-- All seeded users will share the password: 'Admin123' (hash: $2b$12$mg32ZRJlCwUZZrosk3dwJu7sWaPYhdroW5AaSyc3ylGr12X14yBpC)

-- Employee 1: Admin
INSERT INTO EMPLOYEES (name, email, salary, department_id, schedule_id)
VALUES ('System Administrator', 'admin@hr.com', 9500.00, 1, 1);
INSERT INTO USER_CREDENTIALS (employee_id, password_hash)
VALUES (1, '$2b$12$mg32ZRJlCwUZZrosk3dwJu7sWaPYhdroW5AaSyc3ylGr12X14yBpC');
INSERT INTO EMPLOYEE_ROLES (employee_id, role_id) VALUES (1, 1); -- Admin

-- Employee 2: HR Manager
INSERT INTO EMPLOYEES (name, email, salary, department_id, schedule_id)
VALUES ('Juan Elizeche', 'juan@hr.com', 6200.00, 2, 1);
INSERT INTO USER_CREDENTIALS (employee_id, password_hash)
VALUES (2, '$2b$12$mg32ZRJlCwUZZrosk3dwJu7sWaPYhdroW5AaSyc3ylGr12X14yBpC');
INSERT INTO EMPLOYEE_ROLES (employee_id, role_id) VALUES (2, 2); -- HR

-- Employee 3: Software Engineer
INSERT INTO EMPLOYEES (name, email, salary, department_id, schedule_id)
VALUES ('Cesar Oyola', 'cesar@hr.com', 7500.00, 3, 1);
INSERT INTO USER_CREDENTIALS (employee_id, password_hash)
VALUES (3, '$2b$12$mg32ZRJlCwUZZrosk3dwJu7sWaPYhdroW5AaSyc3ylGr12X14yBpC');
INSERT INTO EMPLOYEE_ROLES (employee_id, role_id) VALUES (3, 3); -- Employee

-- Employee 4: Marketing Specialist
INSERT INTO EMPLOYEES (name, email, salary, department_id, schedule_id)
VALUES ('Benjamin Botifacil', 'benja@hr.com', 4800.00, 4, 2);
INSERT INTO USER_CREDENTIALS (employee_id, password_hash)
VALUES (4, '$2b$12$mg32ZRJlCwUZZrosk3dwJu7sWaPYhdroW5AaSyc3ylGr12X14yBpC');
INSERT INTO EMPLOYEE_ROLES (employee_id, role_id) VALUES (4, 3); -- Employee

-- Employee 5: Financial Analyst
INSERT INTO EMPLOYEES (name, email, salary, department_id, schedule_id)
VALUES ('Albert Pont', 'albert@hr.com', 5800.00, 5, 1);
INSERT INTO USER_CREDENTIALS (employee_id, password_hash)
VALUES (5, '$2b$12$mg32ZRJlCwUZZrosk3dwJu7sWaPYhdroW5AaSyc3ylGr12X14yBpC');
INSERT INTO EMPLOYEE_ROLES (employee_id, role_id) VALUES (5, 3); -- Employee

-- 7. Seed Data: Access Logs (Attendance logs)
INSERT INTO ACCESS_LOGS (employee_id, event_type, log_date) VALUES 
(1, 'Check-In', '2026-05-28 07:55:23'),
(1, 'Check-Out', '2026-05-28 16:05:12'),
(2, 'Check-In', '2026-05-28 08:01:45'),
(2, 'Check-Out', '2026-05-28 16:02:10'),
(3, 'Check-In', '2026-05-28 08:15:00'),
(3, 'Check-Out', '2026-05-28 16:30:00'),
(4, 'Check-In', '2026-05-28 15:58:30'),
(4, 'Check-Out', '2026-05-28 23:59:12'),
(1, 'Check-In', '2026-05-29 07:48:11'),
(1, 'Check-Out', '2026-05-29 16:00:05'),
(2, 'Check-In', '2026-05-29 07:59:15'),
(2, 'Check-Out', '2026-05-29 16:03:40'),
(3, 'Check-In', '2026-05-29 08:05:00'),
(3, 'Check-Out', '2026-05-29 16:15:30');

-- 8. Seed Data: Leave Requests
INSERT INTO LEAVE_REQUESTS (employee_id, type, start_date, end_date, status) VALUES 
(3, 'Vacation', '2026-06-10', '2026-06-24', 'Approved'),
(4, 'Medical', '2026-05-15', '2026-05-18', 'Rejected'),
(5, 'Personal', '2026-06-05', '2026-06-07', 'Pending'),
(3, 'Medical', '2026-07-01', '2026-07-02', 'Pending');

