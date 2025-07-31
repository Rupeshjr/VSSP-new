from datetime import datetime, date, time, timedelta
from fastapi import FastAPI, Depends, HTTPException, status, Request, status,Query
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse,StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from .auth.auth_handler import auth_handler, get_current_active_user, ACCESS_TOKEN_EXPIRE_MINUTES
from .auth.auth_models import Token, User, UserRegister
from .config.firebase_config import firebase_config, db
from fastapi.responses import StreamingResponse
import pandas as pd
import io
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi.responses import FileResponse
import os
from fastapi.middleware.cors import CORSMiddleware
from urllib.parse import unquote  # ADD THIS IMPORT

import random
import time
import uuid
from enum import Enum
from google.cloud import firestore
app = FastAPI(
    title="FastAPI Firebase Authentication",
    description="Firebase-based authentication system with FastAPI",
    version="1.0.0"
)

# FIXED CORS CONFIGURATION
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://harmonious-starburst-f1652c.netlify.app",  # Your Netlify URL with https://
        "http://localhost:3000",                             # Local development
        "http://localhost:3001",                             # Alternative local port
        "http://localhost:5173",                             # Vite development server
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicitly list methods
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ],
)
# Pydantic models for employee data validation
class PersonalDetails(BaseModel):
    mobileNumber: Optional[str] = None
    empDOB: Optional[str] = None
    address: Optional[str] = None
    emergencyContact: Optional[str] = None
    marriageAnniversary: Optional[str] = None
    
    class Config:
        extra = "allow"

class OfficialDetails(BaseModel):
    client: Optional[str] = None
    empDOJ: Optional[str] = None
    empCode: Optional[str] = None
    manager: Optional[str] = None
    workLocation: Optional[str] = None
    
    class Config:
        extra = "allow"

class Employee(BaseModel):
    id: str
    empid: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    hireDate: Optional[str] = None
    salary: Optional[str] = None
    status: Optional[str] = "Active"
    personalDetails: Optional[PersonalDetails] = None
    officialDetails: Optional[OfficialDetails] = None
    
    class Config:
        extra = "allow"
class AttendanceRecord(BaseModel):
    employee: str
    employee_id: str
    check_in: Optional[str] = "-"
    check_out: Optional[str] = "-"
    status: str
    working_hours: str
    department: Optional[str] = None

class AttendanceStats(BaseModel):
    present_today: int
    absent_today: int
    late_arrivals: int
    on_leave: int
    total_employees: int

class Holiday(BaseModel):
    id: str
    day: str
    remarks: str
    year: int
    domain: str
    type: str
    date_object: Optional[str] = None

# Define models that depend on other models AFTER the dependencies
class AttendanceResponse(BaseModel):
    stats: AttendanceStats
    today_attendance: List[AttendanceRecord]

class HolidayResponse(BaseModel):
    holidays: List[Holiday]
    total_count: int
    is_today_holiday: bool
    today_holiday_info: Optional[Holiday] = None

class AttendanceWithHoliday(BaseModel):
    stats: AttendanceStats  # Now AttendanceStats is already defined above
    today_attendance: List[AttendanceRecord]
    is_holiday_today: bool
    holiday_info: Optional[Holiday] = None
# Leave Management Models
class LeaveDetail(BaseModel):
    id: str
    appliedby: Optional[str] = None
    days: Optional[int] = None
    starttime: Optional[str] = None
    mgremail: Optional[str] = None
    empid: Optional[str] = None
    # Add other potential fields
    endtime: Optional[str] = None
    leavetype: Optional[str] = None
    reason: Optional[str] = None
    status: Optional[str] = "Pending"
    applieddate: Optional[str] = None
    
    class Config:
        extra = "allow"

class LeaveSummary(BaseModel):
    id: str
    creditedbalance: Optional[float] = None
    name: Optional[str] = None
    encash: Optional[float] = None
    year: Optional[int] = None
    leavetaken: Optional[float] = None
    # Add other potential fields
    remaining: Optional[float] = None
    empid: Optional[str] = None
    
    class Config:
        extra = "allow"

class LeaveRequest(BaseModel):
    id: str
    employee: str
    leave_type: str
    start_date: str
    end_date: str
    days: int
    status: str
    reason: Optional[str] = None
    applied_date: Optional[str] = None
    manager_email: Optional[str] = None

class LeaveStats(BaseModel):
    total_requests: int
    pending_requests: int
    approved_requests: int
    rejected_requests: int

class LeaveManagementResponse(BaseModel):
    stats: LeaveStats
    leave_requests: List[LeaveRequest]
    leave_summaries: List[LeaveSummary]
class Job(BaseModel):
    id: str
    title: Optional[str] = None
    status: Optional[str] = None
    processflow: Optional[str] = None
    modifiedOn: Optional[str] = None
    test: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    location: Optional[str] = None
    department: Optional[str] = None
    experience: Optional[str] = None
    salary: Optional[str] = None
    
    class Config:
        extra = "allow"

class JobStats(BaseModel):
    total_jobs: int
    active_jobs: int
    inactive_jobs: int
    draft_jobs: int
    filled_jobs: int

class RecruitmentResponse(BaseModel):
    stats: JobStats
    jobs: List[Job]
    total_count: int
class ResignationRequest(BaseModel):
    id: Optional[str] = None
    ID: str  # Using existing field from itrequests
    empid: str
    employee_name: str
    employee_email: str
    department: str
    position: str
    manager_name: Optional[str] = None
    manager_email: Optional[str] = None
    resignation_date: str
    last_working_date: str
    reason: str
    notice_period_days: int
    status: str = "Pending"
    comments: Optional[str] = None
    hr_comments: Optional[str] = None
    request_type: str = "Resignation"  # To identify resignation requests
    createdBy: str  # Using existing field
    modifiedBy: Optional[str] = None  # Using existing field
    modifiedOn: str  # Using existing field
    assignedTo: Optional[str] = None  # Using existing field for HR assignment
    
    class Config:
        extra = "allow"

class ResignationStats(BaseModel):
    total_resignations: int
    pending_approvals: int
    approved_resignations: int
    rejected_resignations: int
    this_month_resignations: int
class ReportType(str, Enum):
    EMPLOYEE_SUMMARY = "employee_summary"
    RECRUITMENT_ANALYTICS = "recruitment_analytics" 
    LEAVE_MANAGEMENT = "leave_management"
    PERFORMANCE_REVIEW = "performance_review"
    ASSET_MANAGEMENT = "asset_management"
    IT_REQUESTS = "it_requests"
    HOLIDAY_CALENDAR = "holiday_calendar"
    VENDOR_MANAGEMENT = "vendor_management"

class ReportRequest(BaseModel):
    report_type: ReportType
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    domain: Optional[str] = None
    filters: Optional[Dict[str, Any]] = {}

class GeneratedReport(BaseModel):
    id: str
    report_type: str
    period_start: Optional[date]
    period_end: Optional[date] 
    created_at: datetime
    status: str
    record_count: int
class ConfigAll(BaseModel):
    user: str
    description: str
    type: str
    comments: Optional[str] = ""

class ConfigGeneral(BaseModel):
    CL: Optional[int] = 0  # Casual Leave
    SL: Optional[int] = 0  # Sick Leave  
    PL: Optional[int] = 0  # Privilege Leave
    CF: Optional[int] = 0  # Carry Forward
    comments: Optional[str] = ""

class ConfigPDP(BaseModel):
    eligibilitydate: str
    year: int
    status: str
    domain: str
    mailMessage: str


# Create FastAPI app
app = FastAPI(
    title="FastAPI Firebase Authentication",
    description="Firebase-based authentication system with FastAPI",
    version="1.0.0"
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request:Request, exc: RequestValidationError):
     exc_str = f'{exc}'.replace('\n', ' ').replace(' ', ' ')
     print(f"Validation error: {exc_str}")  # This will help you debug
     content = {'status_code': 422, 'message': exc_str, 'data': None}
     return JSONResponse(content=content,status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
    
@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    from .config.firebase_config import firebase_config
    import os

    # Load environment variables
    firebase_project_id = os.getenv("PROJECT_ID", "NOT_SET")
    environment = os.getenv("ENVIRONMENT", "development")

    try:
        # Try to get Firestore client and list collections
        db = firebase_config.db
        collections = list(db.collections())
        print("âœ… Firebase connection established")
        print(f"ðŸ“¦ Project ID: {firebase_project_id}")
        print(f"ðŸŒŽ Environment: {environment}")
        print(f"ðŸ“š Collections found: {[c.id for c in collections]}")
    except Exception as e:
        print("âŒ Firebase DB connection failed:", str(e))
        print(f"ðŸ“¦ Project ID: {firebase_project_id}")
        print(f"ðŸŒŽ Environment: {environment}")
    
    print("ðŸš€ FastAPI Firebase Auth server starting up...")
    print("âœ… Firebase connection established")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "FastAPI Firebase Authentication System",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            # ... existing endpoints ...
            # NEW RESIGNATION ENDPOINTS
            "resignations": "/api/resignations",
            "resignation_detail": "/api/resignations/{resignation_id}",
            "resignation_stats": "/api/resignations/stats",
            "resignation_dashboard": "/api/resignations/dashboard",
            "employee_resignations": "/api/resignations/employee/{empid}",
            "pending_resignations": "/api/resignations/pending",
            "approve_resignation": "/api/resignations/{resignation_id}/approve [POST]",
            "reject_resignation": "/api/resignations/{resignation_id}/reject [POST]",
            "resignation_reports": "/api/resignations/reports/monthly",
            "create_resignation": "/api/resignations [POST]",
            "update_resignation": "/api/resignations/{resignation_id} [PUT]",
            "withdraw_resignation": "/api/resignations/{resignation_id} [DELETE]"
        }
    }





# Helper function to convert Firestore document to dict
def firestore_doc_to_dict(doc) -> Dict[str, Any]:
    """Convert Firestore document to dictionary with proper handling of nested objects"""
    doc_dict = doc.to_dict()
    doc_dict['id'] = doc.id
    return doc_dict

# NEW ENDPOINT 1: Get all employees
@app.get("/employees", response_model=List[Employee])
async def get_all_employees():
    """
    Fetch all employees from Firebase Firestore
    Returns a list of all employee records
    """
    try:
        # Reference to the employees collection
        employees_ref = db.collection('employeelists')  # Using your collection name
        
        # Get all documents from the collection
        docs = employees_ref.stream()
        
        # Convert documents to list of dictionaries
        employees_data = []
        for doc in docs:
            employee_dict = firestore_doc_to_dict(doc)
            employees_data.append(employee_dict)
        
        print(f"Successfully fetched {len(employees_data)} employees")
        return employees_data
        
    except Exception as e:
        print(f"Error fetching employees: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch employees: {str(e)}")

# NEW ENDPOINT 2: Get single employee by ID
@app.get("/employees/{employee_id}", response_model=Employee)
async def get_employee_by_id(employee_id: str):
    """
    Fetch a single employee by their document ID
    """
    try:
        doc_ref = db.collection('employeelists').document(employee_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        employee_dict = firestore_doc_to_dict(doc)
        return employee_dict
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching employee {employee_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch employee: {str(e)}")

# NEW ENDPOINT 3: Search employees with query parameters
@app.get("/employees/search", response_model=List[Employee])
async def search_employees(
    name: Optional[str] = None,
    department: Optional[str] = None,
    client: Optional[str] = None,
    position: Optional[str] = None,
    email: Optional[str] = None
):
    """
    Search employees based on query parameters
    """
    try:
        employees_ref = db.collection('employeelists')
        
        # Since Firestore has limited query capabilities, we'll fetch all and filter in Python
        docs = employees_ref.stream()
        employees_data = []
        
        for doc in docs:
            employee_dict = firestore_doc_to_dict(doc)
            match = True
            
            # Apply filters
            if name and name.lower() not in employee_dict.get('name', '').lower():
                match = False
            if department and department.lower() not in employee_dict.get('department', '').lower():
                match = False
            if position and position.lower() not in employee_dict.get('position', '').lower():
                match = False
            if email and email.lower() not in employee_dict.get('email', '').lower():
                match = False
            if client:
                official_details = employee_dict.get('officialDetails', {})
                if client.lower() not in official_details.get('client', '').lower():
                    match = False
            
            if match:
                employees_data.append(employee_dict)
        
        return employees_data
        
    except Exception as e:
        print(f"Error searching employees: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to search employees: {str(e)}")

@app.get("/employees/count")
async def get_employee_count(current_user: User = Depends(get_current_active_user)):
    
    try:
        employees_ref = db.collection('employeelists')
        docs = employees_ref.stream()
        count = sum(1 for _ in docs)
        
        return {
            "status": "success",
            "total_employees": count,
            "message": f"Found {count} employees in the database",
            "requested_by": current_user.email,
            "timestamp": "2025-07-24T14:44:13Z"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching employee count: {str(e)}"
        )

@app.get("/employees/export")
async def export_employees_excel(current_user: User = Depends(get_current_active_user)):
    """
    Export employee data to Excel file
    Only HR can export employee data
    """
    try:
        # Check if user has permission (only HR)
        if current_user.role != 'hr':
            raise HTTPException(
                status_code=403, 
                detail="Only HR can export employee data"
            )
        
        # Fetch employee data from Firebase
        employees_ref = db.collection('employeelists')
        docs = employees_ref.stream()
        
        # Convert Firebase data to list of dictionaries
        employees_data = []
        for doc in docs:
            emp_data = doc.to_dict()
            
            # Flatten the nested data structure for Excel
            flattened_data = {
                'Employee ID': doc.id,
                'Name': emp_data.get('name', ''),
                'Email': emp_data.get('email', ''),
                'Phone': emp_data.get('phone', ''),
                'Department': emp_data.get('department', ''),
                'Position': emp_data.get('position', ''),
                'Hire Date': emp_data.get('hireDate', ''),
                'Salary': emp_data.get('salary', ''),
                'Status': emp_data.get('status', 'Active'),
            }
            
            # Add personal details if available
            personal_details = emp_data.get('personalDetails', {})
            if personal_details:
                flattened_data.update({
                    'Date of Birth': personal_details.get('empDOB', ''),
                    'Address': personal_details.get('address', ''),
                    'Emergency Contact': personal_details.get('emergencyContact', ''),
                    'Marriage Anniversary': personal_details.get('marriageAnniversary', ''),
                })
            
            # Add official details if available
            official_details = emp_data.get('officialDetails', {})
            if official_details:
                flattened_data.update({
                    'Employee Code': official_details.get('empCode', ''),
                    'Date of Joining': official_details.get('empDOJ', ''),
                    'Manager': official_details.get('manager', ''),
                    'Work Location': official_details.get('workLocation', ''),
                })
            
            employees_data.append(flattened_data)
        
        # Create DataFrame from the data
        df = pd.DataFrame(employees_data)
        
        # Create Excel file in memory
        excel_buffer = io.BytesIO()
        
        # Write DataFrame to Excel with formatting
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Employees', index=False)
            
            # Get the workbook and worksheet for formatting
            workbook = writer.book
            worksheet = writer.sheets['Employees']
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                adjusted_width = min(max_length + 2, 50)  # Max width 50
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        excel_buffer.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"employees_export_{timestamp}.xlsx"
        
        # Return Excel file as downloadable response
        return StreamingResponse(
            io.BytesIO(excel_buffer.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error exporting employee data: {str(e)}"
        )

@app.get("/employees/export/public")
async def export_employees_excel_public():
    """
    Export employee data to Excel file - Public endpoint (no authentication required)
    """
    try:
        # Fetch employee data from Firebase
        employees_ref = db.collection('employeelists')
        docs = employees_ref.stream()
        
        # Convert Firebase data to list of dictionaries
        employees_data = []
        for doc in docs:
            emp_data = doc.to_dict()
            
            # Flatten the nested data structure for Excel
            flattened_data = {
                'Employee ID': doc.id,
                'Name': emp_data.get('name', ''),
                'Email': emp_data.get('email', ''),
                'Phone': emp_data.get('phone', ''),
                'Department': emp_data.get('department', ''),
                'Position': emp_data.get('position', ''),
                'Hire Date': emp_data.get('hireDate', ''),
                'Salary': emp_data.get('salary', ''),
                'Status': emp_data.get('status', 'Active'),
            }
            
            # Add personal details if available
            personal_details = emp_data.get('personalDetails', {})
            if personal_details:
                flattened_data.update({
                    'Date of Birth': personal_details.get('empDOB', ''),
                    'Address': personal_details.get('address', ''),
                    'Emergency Contact': personal_details.get('emergencyContact', ''),
                    'Marriage Anniversary': personal_details.get('marriageAnniversary', ''),
                })
            
            # Add official details if available
            official_details = emp_data.get('officialDetails', {})
            if official_details:
                flattened_data.update({
                    'Employee Code': official_details.get('empCode', ''),
                    'Date of Joining': official_details.get('empDOJ', ''),
                    'Manager': official_details.get('manager', ''),
                    'Work Location': official_details.get('workLocation', ''),
                })
            
            employees_data.append(flattened_data)
        
        # Create DataFrame from the data
        df = pd.DataFrame(employees_data)
        
        # Create Excel file in memory
        excel_buffer = io.BytesIO()
        
        # Write DataFrame to Excel with formatting
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Employees', index=False)
            
            # Get the workbook and worksheet for formatting
            workbook = writer.book
            worksheet = writer.sheets['Employees']
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                adjusted_width = min(max_length + 2, 50)  # Max width 50
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        excel_buffer.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"employees_export_{timestamp}.xlsx"
        
        # Return Excel file as downloadable response
        return StreamingResponse(
            io.BytesIO(excel_buffer.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error exporting employee data: {str(e)}"
        )

@app.get("/employees/count/public")
async def get_employee_count_public():
    """
    Get total count of employees - Public endpoint for testing
    """
    try:
        employees_ref = db.collection('employeelists')
        docs = employees_ref.stream()
        count = sum(1 for _ in docs)
        
        return {
            "status": "success",
            "total_employees": count,
            "message": f"Found {count} employees in the database",
            "timestamp": "2025-07-24T14:44:13Z"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching employee count: {str(e)}"
        )
@app.get("/employees/{employee_id}/details")
async def get_employee_details(employee_id: str):
    try:
        # URL decode the employee_id to handle encoded emails
        decoded_employee_id = unquote(employee_id)
        print(f"Original employee_id: {employee_id}")
        print(f"Decoded employee_id: {decoded_employee_id}")
        
        document_id_to_use = None
        
        # METHOD 1: Search in employee_id collection
        print("Searching in employee_id collection...")
        employee_ids_ref = db.collection('employee_id')
        employee_ids_docs = employee_ids_ref.stream()
        
        for doc in employee_ids_docs:
            doc_data = doc.to_dict()
            if 'employee_ids' in doc_data:
                for emp_entry in doc_data['employee_ids']:
                    # Check all possible matches
                    if (emp_entry.get('empid') == decoded_employee_id or 
                        emp_entry.get('document_id') == decoded_employee_id or
                        emp_entry.get('email') == decoded_employee_id):
                        
                        document_id_to_use = emp_entry.get('document_id')
                        print(f"✅ Found matching employee in employee_id collection, using document_id: {document_id_to_use}")
                        break
            
            if document_id_to_use:
                break
        
        # METHOD 2: Direct search in employeelists collection by document ID
        if not document_id_to_use:
            print("Searching by direct document ID in employeelists...")
            doc_ref = db.collection('employeelists').document(decoded_employee_id)
            doc = doc_ref.get()
            
            if doc.exists:
                document_id_to_use = decoded_employee_id
                print(f"✅ Found direct match with document ID: {document_id_to_use}")
        
        # METHOD 3: Search by PERSONAL email field in employeelists collection
        if not document_id_to_use:
            print("Searching by personal email field in employeelists...")
            employees_ref = db.collection('employeelists')
            # FIXED: Search in personalDetails.email instead of root email
            query = employees_ref.where('personalDetails.email', '==', decoded_employee_id).limit(1)
            results = query.stream()
            
            for result_doc in results:
                document_id_to_use = result_doc.id
                print(f"✅ Found employee by personal email search, document_id: {document_id_to_use}")
                break
        
        # METHOD 4: Search by company email field (fallback)
        if not document_id_to_use:
            print("Searching by company email field in employeelists...")
            employees_ref = db.collection('employeelists')
            query = employees_ref.where('email', '==', decoded_employee_id).limit(1)
            results = query.stream()
            
            for result_doc in results:
                document_id_to_use = result_doc.id
                print(f"✅ Found employee by company email search, document_id: {document_id_to_use}")
                break
        
        # METHOD 5: Search by empid field in employeelists collection
        if not document_id_to_use:
            print("Searching by empid field in employeelists...")
            employees_ref = db.collection('employeelists')
            query = employees_ref.where('empid', '==', decoded_employee_id).limit(1)
            results = query.stream()
            
            for result_doc in results:
                document_id_to_use = result_doc.id
                print(f"✅ Found employee by empid search, document_id: {document_id_to_use}")
                break
        
        # If still not found, show what's available
        if not document_id_to_use:
            print("❌ Employee not found. Checking available employees...")
            
            # Show what's actually in the database
            employees_ref = db.collection('employeelists')
            all_employees = employees_ref.stream()
            
            available_employees = []
            for emp_doc in list(all_employees)[:5]:  # Show first 5 for debugging
                emp_data = emp_doc.to_dict()
                personal_details = emp_data.get('personalDetails', {})
                available_employees.append({
                    'document_id': emp_doc.id,
                    'name': emp_data.get('name'),
                    'company_email': emp_data.get('email'),
                    'personal_email': personal_details.get('email'),
                    'empid': emp_data.get('empid')
                })
                print(f"Available: ID={emp_doc.id}, name={emp_data.get('name')}, personal_email={personal_details.get('email')}, company_email={emp_data.get('email')}")
            
            raise HTTPException(
                status_code=404, 
                detail=f"Employee with ID '{decoded_employee_id}' not found. Available employees: {available_employees}"
            )
        
        # Fetch the actual employee data
        doc_ref = db.collection('employeelists').document(document_id_to_use)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail=f"Employee document not found with document_id: {document_id_to_use}")
        
        employee_data = doc.to_dict()
        print(f"✅ Successfully found employee: {employee_data.get('name', 'Unknown')}")
        
        # Log both email types for debugging
        personal_details = employee_data.get('personalDetails', {})
        print(f"Personal email: {personal_details.get('email')}")
        print(f"Company email: {employee_data.get('email')}")
        
        return employee_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching employee {employee_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/employees/{employee_id}/document-image/{field_name}")
async def get_employee_document_image(employee_id: str, field_name: str):
    try:
        # Fetch employee details from your database
        employee_details = await get_employee_details(employee_id)
        
        # Get the Firebase URL for the specific document field
        firebase_url = employee_details.get('documentDetails', {}).get(field_name)
        
        if not firebase_url:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Ensure the URL has proper format for public access
        if 'alt=media' not in firebase_url:
            firebase_url += '&alt=media' if '?' in firebase_url else '?alt=media'
        
        # Fetch the image from Firebase
        response = requests.get(firebase_url)
        response.raise_for_status()
        
        # Return the image as a streaming response
        return StreamingResponse(
            io.BytesIO(response.content),
            media_type="image/jpeg",
            headers={"Cache-Control": "max-age=3600"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching image: {str(e)}")





# Optional: File serving endpoint for document images/files
@app.get("/files/documents/{employee_id}/{filename}")
async def get_document_file(employee_id: str, filename: str):
    """
    Serve document files (images, PDFs, etc.)
    """
    try:
        import os
        from fastapi.responses import FileResponse
        
        # Define the file path (adjust this to your actual file storage location)
        file_path = f"uploads/documents/{employee_id}/{filename}"
        
        if os.path.exists(file_path):
            return FileResponse(file_path)
        else:
            raise HTTPException(status_code=404, detail="File not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving file: {str(e)}")


# Optional: Debug endpoint to verify collection data
@app.get("/debug/employee/{employee_id}")
async def debug_employee(employee_id: str):
    """
    Debug endpoint to see raw employee data structure
    """
    try:
        employee_ref = db.collection('employeelists').document(employee_id)
        employee_doc = employee_ref.get()
        
        if not employee_doc.exists:
            return {"error": "Employee not found"}
        
        data = employee_doc.to_dict()
        return {
            "document_id": employee_doc.id,
            "data": data,
            "available_fields": list(data.keys())
        }
        
    except Exception as e:
        return {"error": str(e)}


@app.get("/debug/collections")
async def get_all_collections(current_user: User = Depends(get_current_active_user)):
    """
    Get all collection names from Firebase Firestore - Protected endpoint
    Requires authentication token
    """
    try:
        # Get all collections from Firestore
        collections = list(db.collections())
        collection_names = [col.id for col in collections]
        
        # Get document count for each collection (optional detailed info)
        collection_details = []
        for collection_name in collection_names:
            try:
                # Count documents in each collection
                docs = list(db.collection(collection_name).limit(1000).stream())
                doc_count = len(docs)
                
                # Get sample field names from first document
                sample_fields = []
                if docs:
                    first_doc = docs[0].to_dict()
                    sample_fields = list(first_doc.keys())[:5]  # First 5 fields
                
                collection_details.append({
                    "collection_name": collection_name,
                    "document_count": doc_count,
                    "sample_fields": sample_fields,
                    "status": "âœ… Active" if doc_count > 0 else "âŒ Empty"
                })
                
            except Exception as e:
                collection_details.append({
                    "collection_name": collection_name,
                    "document_count": 0,
                    "sample_fields": [],
                    "status": f"âŒ Error: {str(e)}"
                })
        
        return {
            "status": "success",
            "total_collections": len(collection_names),
            "collection_names": collection_names,
            "detailed_info": collection_details,
            "timestamp": "2025-07-24T16:54:00Z",
            "requested_by": current_user.email
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching collections: {str(e)}"
        )

@app.post("/auth/register", response_model=dict)
async def register_user(user_data: UserRegister):
    """Register a new user with Firebase"""
    try:
        # Create user in Firebase Auth and Firestore
        firebase_user = await auth_handler.create_firebase_user(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            role=user_data.role
        )
        
        return {
            "message": "User created successfully",
            "uid": firebase_user.uid,
            "email": firebase_user.email,
            "full_name": user_data.full_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@app.post("/auth/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login endpoint to get access token
    
    Use email as username in the login form
    """
    user = await auth_handler.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_handler.create_access_token(
        data={"sub": user.uid}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user_info": {
            "uid": user.uid,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        }
    }

@app.get("/calendar/events")
async def get_calendar_events(
    year: int = None,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get calendar events (birthdays, work anniversaries, marriage anniversaries)
    from employeelists collection
    """
    try:
        from datetime import datetime
        
        # Use current year if not specified
        if year is None:
            year = datetime.now().year
        
        # Fetch employees from employeelists collection
        employees_ref = db.collection('employeelists')
        docs = employees_ref.stream()
        
        formatted_events = []
        
        for doc in docs:
            emp_data = doc.to_dict()
            emp_name = emp_data.get('name', 'Employee')
            
            # Process Birthday events
            personal_details = emp_data.get('personalDetails', {})
            if personal_details.get('empDOB'):
                try:
                    dob = datetime.fromisoformat(personal_details['empDOB'].replace('Z', '+00:00'))
                    formatted_events.append({
                        "date": f"{year}-{dob.month}-{dob.day}",
                        "name": emp_name,
                        "type": "birthday",
                        "employee_id": doc.id
                    })
                except Exception as e:
                    print(f"Error processing DOB for {emp_name}: {e}")
            
            # Process Work Anniversary events
            official_details = emp_data.get('officialDetails', {})
            if official_details.get('empDOJ'):
                try:
                    doj = datetime.fromisoformat(official_details['empDOJ'].replace('Z', '+00:00'))
                    formatted_events.append({
                        "date": f"{year}-{doj.month}-{doj.day}",
                        "name": emp_name,
                        "type": "work",
                        "employee_id": doc.id
                    })
                except Exception as e:
                    print(f"Error processing DOJ for {emp_name}: {e}")
            
            # Process Marriage Anniversary events
            if personal_details.get('marriageAnniversary'):
                try:
                    mar_date = datetime.fromisoformat(personal_details['marriageAnniversary'].replace('Z', '+00:00'))
                    formatted_events.append({
                        "date": f"{year}-{mar_date.month}-{mar_date.day}",
                        "name": emp_name,
                        "type": "marriage",
                        "employee_id": doc.id
                    })
                except Exception as e:
                    print(f"Error processing marriage anniversary for {emp_name}: {e}")
        
        return {
            "status": "success",
            "year": year,
            "total_events": len(formatted_events),
            "events": formatted_events,
            "requested_by": current_user.email,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching calendar events: {str(e)}"
        )

@app.get("/calendar/events/public")
async def get_calendar_events_public(year: int = None):
    """
    Get calendar events (birthdays, work anniversaries, marriage anniversaries)
    from employeelists collection - Public endpoint (no authentication required)
    """
    try:
        from datetime import datetime
        
        # Use current year if not specified
        if year is None:
            year = datetime.now().year
        
        # Fetch employees from employeelists collection
        employees_ref = db.collection('employeelists')
        docs = employees_ref.stream()
        
        formatted_events = []
        
        for doc in docs:
            emp_data = doc.to_dict()
            emp_name = emp_data.get('name', 'Employee')
            
            # Process Birthday events
            personal_details = emp_data.get('personalDetails', {})
            if personal_details.get('empDOB'):
                try:
                    dob = datetime.fromisoformat(personal_details['empDOB'].replace('Z', '+00:00'))
                    formatted_events.append({
                        "date": f"{year}-{dob.month}-{dob.day}",
                        "name": emp_name,
                        "type": "birthday",
                        "employee_id": doc.id
                    })
                except Exception as e:
                    print(f"Error processing DOB for {emp_name}: {e}")
            
            # Process Work Anniversary events
            official_details = emp_data.get('officialDetails', {})
            if official_details.get('empDOJ'):
                try:
                    doj = datetime.fromisoformat(official_details['empDOJ'].replace('Z', '+00:00'))
                    formatted_events.append({
                        "date": f"{year}-{doj.month}-{doj.day}",
                        "name": emp_name,
                        "type": "work",
                        "employee_id": doc.id
                    })
                except Exception as e:
                    print(f"Error processing DOJ for {emp_name}: {e}")
            
            # Process Marriage Anniversary events
            if personal_details.get('marriageAnniversary'):
                try:
                    mar_date = datetime.fromisoformat(personal_details['marriageAnniversary'].replace('Z', '+00:00'))
                    formatted_events.append({
                        "date": f"{year}-{mar_date.month}-{mar_date.day}",
                        "name": emp_name,
                        "type": "marriage",
                        "employee_id": doc.id
                    })
                except Exception as e:
                    print(f"Error processing marriage anniversary for {emp_name}: {e}")
        
        return {
            "status": "success",
            "year": year,
            "total_events": len(formatted_events),
            "events": formatted_events,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching calendar events: {str(e)}"
        )

@app.get("/protected")
async def protected_route(current_user: User = Depends(get_current_active_user)):
    """Protected route that requires authentication"""
    return {
        "message": f"Hello {current_user.full_name}!",
        "user": {
            "uid": current_user.uid,
            "email": current_user.email,
            "role": current_user.role
        },
        "access": "granted",
        "timestamp": "2025-01-23T11:06:00Z"
    }

@app.get("/auth/verify-token")
async def verify_token(current_user: User = Depends(get_current_active_user)):
    """Verify if token is valid and return user info"""
    return {
        "valid": True,
        "user": current_user,
        "message": "Token is valid"
    }
@app.get("/api/holidays", response_model=HolidayResponse)
async def get_holidays(year: Optional[int] = None, domain: Optional[str] = None):
    """
    Get all holidays with optional filtering by year and domain
    """
    try:
        holidays_ref = db.collection('holidays')
        query = holidays_ref
        
        # Filter by year if provided
        if year:
            query = query.where('year', '==', year)
        
        # Filter by domain if provided
        if domain:
            query = query.where('domain', '==', domain)
        
        holidays_docs = query.get()
        
        holidays = []
        today = date.today()
        is_today_holiday = False
        today_holiday_info = None
        
        for doc in holidays_docs:
            holiday_data = doc.to_dict()
            
            # Create holiday object
            holiday = Holiday(
                id=doc.id,
                day=holiday_data.get('day', ''),
                remarks=holiday_data.get('remarks', ''),
                year=holiday_data.get('year', today.year),
                domain=holiday_data.get('domain', ''),
                type=holiday_data.get('type', ''),
                date_object=holiday_data.get('day', '')  # Assuming day is in readable format
            )
            
            holidays.append(holiday)
            
            # Check if today is a holiday
            if holiday_data.get('day'):
                try:
                    # Try different date formats
                    holiday_date = None
                    day_str = holiday_data.get('day', '')
                    
                    # Try parsing different date formats
                    for date_format in ['%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d/%m/%Y']:
                        try:
                            holiday_date = datetime.strptime(day_str, date_format).date()
                            break
                        except ValueError:
                            continue
                    
                    if holiday_date and holiday_date == today:
                        is_today_holiday = True
                        today_holiday_info = holiday
                        
                except Exception:
                    pass
        
        # Sort holidays by date (if possible) or by day string
        holidays.sort(key=lambda x: x.day)
        
        return HolidayResponse(
            holidays=holidays,
            total_count=len(holidays),
            is_today_holiday=is_today_holiday,
            today_holiday_info=today_holiday_info
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching holidays: {str(e)}")

@app.get("/api/holidays/today")
async def get_today_holiday():
    """
    Check if today is a holiday
    """
    try:
        today = date.today()
        current_year = today.year
        
        holidays_ref = db.collection('holidays')
        holidays_docs = holidays_ref.where('year', '==', current_year).get()
        
        for doc in holidays_docs:
            holiday_data = doc.to_dict()
            day_str = holiday_data.get('day', '')
            
            # Try to parse the date
            try:
                for date_format in ['%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d/%m/%Y']:
                    try:
                        holiday_date = datetime.strptime(day_str, date_format).date()
                        if holiday_date == today:
                            return {
                                'is_holiday': True,
                                'holiday_info': {
                                    'id': doc.id,
                                    'day': day_str,
                                    'remarks': holiday_data.get('remarks', ''),
                                    'type': holiday_data.get('type', ''),
                                    'domain': holiday_data.get('domain', '')
                                }
                            }
                        break
                    except ValueError:
                        continue
            except Exception:
                continue
        
        return {'is_holiday': False, 'holiday_info': None}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking today's holiday: {str(e)}")

@app.get("/api/holidays/upcoming")
async def get_upcoming_holidays(days: int = 30):
    """
    Get upcoming holidays within specified days
    """
    try:
        today = date.today()
        future_date = today + timedelta(days=days)
        current_year = today.year
        
        holidays_ref = db.collection('holidays')
        holidays_docs = holidays_ref.where('year', '==', current_year).get()
        
        upcoming_holidays = []
        
        for doc in holidays_docs:
            holiday_data = doc.to_dict()
            day_str = holiday_data.get('day', '')
            
            try:
                holiday_date = None
                for date_format in ['%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d/%m/%Y']:
                    try:
                        holiday_date = datetime.strptime(day_str, date_format).date()
                        break
                    except ValueError:
                        continue
                
                if holiday_date and today <= holiday_date <= future_date:
                    upcoming_holidays.append({
                        'id': doc.id,
                        'day': day_str,
                        'date': holiday_date.strftime('%Y-%m-%d'),
                        'remarks': holiday_data.get('remarks', ''),
                        'type': holiday_data.get('type', ''),
                        'domain': holiday_data.get('domain', ''),
                        'days_from_now': (holiday_date - today).days
                    })
            except Exception:
                continue
        
        # Sort by date
        upcoming_holidays.sort(key=lambda x: x['days_from_now'])
        
        return {
            'upcoming_holidays': upcoming_holidays,
            'count': len(upcoming_holidays)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching upcoming holidays: {str(e)}")

# Updated attendance endpoint to include holiday information
@app.get("/api/attendance/today-with-holiday", response_model=AttendanceWithHoliday)
async def get_today_attendance_with_holiday():
    """
    Get today's attendance data along with holiday information
    """
    try:
        # Get attendance data (reuse existing logic)
        attendance_response = await get_today_attendance()
        
        # Get holiday information
        holiday_info = await get_today_holiday()
        
        # If today is a holiday, adjust attendance logic
        if holiday_info['is_holiday']:
            # You might want to modify attendance stats for holidays
            # For example, not count people as absent if it's a holiday
            pass
        
        return AttendanceWithHoliday(
            stats=attendance_response.stats,
            today_attendance=attendance_response.today_attendance,
            is_holiday_today=holiday_info['is_holiday'],
            holiday_info=Holiday(**holiday_info['holiday_info']) if holiday_info['holiday_info'] else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching attendance with holiday data: {str(e)}")

# Get holidays by domain (useful for different departments)
@app.get("/api/holidays/domain/{domain}")
async def get_holidays_by_domain(domain: str, year: Optional[int] = None):
    """
    Get holidays specific to a domain/department
    """
    try:
        if not year:
            year = date.today().year
            
        holidays_ref = db.collection('holidays')
        holidays_docs = holidays_ref.where('domain', '==', domain).where('year', '==', year).get()
        
        holidays = []
        for doc in holidays_docs:
            holiday_data = doc.to_dict()
            holidays.append({
                'id': doc.id,
                'day': holiday_data.get('day', ''),
                'remarks': holiday_data.get('remarks', ''),
                'type': holiday_data.get('type', ''),
                'year': holiday_data.get('year', year)
            })
        
        return {
            'domain': domain,
            'year': year,
            'holidays': holidays,
            'count': len(holidays)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching holidays for domain {domain}: {str(e)}")
@app.get("/api/attendance/today", response_model=AttendanceResponse)
async def get_today_attendance():
    """
    Get today's attendance data - Currently using mock data from employeelists
    """
    try:
        # Get all employees from employeelists collection
        employees_ref = db.collection('employeelists')
        employees_docs = list(employees_ref.get())  # Convert to list
        
        if not employees_docs:
            raise HTTPException(status_code=404, detail="No employees found")
        
        attendance_records = []
        present_count = 0
        absent_count = 0
        late_count = 0
        on_leave_count = 0
        total_employees = 0
        
        # Generate mock attendance data for each employee
        for doc in employees_docs:
            employee_data = doc.to_dict()
            total_employees += 1
            
            # Extract employee information
            employee_name = employee_data.get('name', 'Unknown Employee')
            employee_domain = employee_data.get('domain', 'General')
            
            # Generate realistic mock attendance data
            attendance_status = random.choices(
                ['Present', 'Absent', 'On Leave'], 
                weights=[75, 15, 10]
            )[0]
            
            check_in_time = "-"
            check_out_time = "-"
            working_hours = "0h 0m"
            
            if attendance_status == 'Present':
                # Generate realistic check-in time (8:00 AM to 10:00 AM)
                check_in_hour = random.randint(8, 9)
                check_in_minute = random.randint(0, 59)
                
                # Create time object properly
                from datetime import time as time_class  # Import with alias to avoid confusion
                check_in_dt = time_class(check_in_hour, check_in_minute)
                check_in_time = check_in_dt.strftime("%H:%M")
                
                # Check if late (after 9:15 AM)
                late_threshold = time_class(9, 15)
                if check_in_dt > late_threshold:
                    late_count += 1
                
                # Generate check-out time (5:00 PM to 7:00 PM) for some employees
                if random.choice([True, False]):
                    check_out_hour = random.randint(17, 19)
                    check_out_minute = random.randint(0, 59)
                    check_out_dt = time_class(check_out_hour, check_out_minute)
                    check_out_time = check_out_dt.strftime("%H:%M")
                    
                    # Calculate working hours
                    check_in_datetime = datetime.combine(date.today(), check_in_dt)
                    check_out_datetime = datetime.combine(date.today(), check_out_dt)
                    work_duration = check_out_datetime - check_in_datetime
                    hours = work_duration.seconds // 3600
                    minutes = (work_duration.seconds // 60) % 60
                    working_hours = f"{hours}h {minutes}m"
                
                present_count += 1
            elif attendance_status == 'Absent':
                absent_count += 1
            elif attendance_status == 'On Leave':
                on_leave_count += 1
            
            # Create attendance record
            record = AttendanceRecord(
                employee=employee_name,
                employee_id=doc.id,
                check_in=check_in_time,
                check_out=check_out_time,
                status=attendance_status,
                working_hours=working_hours,
                department=employee_domain
            )
            attendance_records.append(record)
        
        # Create statistics
        stats = AttendanceStats(
            present_today=present_count,
            absent_today=absent_count,
            late_arrivals=late_count,
            on_leave=on_leave_count,
            total_employees=total_employees
        )
        
        # Sort records by employee name
        attendance_records.sort(key=lambda x: x.employee)
        
        response = AttendanceResponse(
            stats=stats,
            today_attendance=attendance_records
        )
        
        return response
        
    except Exception as e:
        print(f"Detailed error in get_today_attendance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching attendance data: {str(e)}")


@app.get("/api/attendance/stats")
async def get_attendance_stats():
    """
    Get quick attendance statistics for dashboard
    """
    try:
        attendance_data = await get_today_attendance()
        return attendance_data.stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching attendance stats: {str(e)}")

# Optional: Get employees list for dropdown/selection
@app.get("/api/employees")
async def get_employees():
    """
    Get list of all employees with detailed information
    """
    try:
        employees_ref = db.collection('employeelists')
        employees_docs = employees_ref.get()
        
        employees = []
        for doc in employees_docs:
            employee_data = doc.to_dict()
            
            # Extract nested data safely
            personal_details = employee_data.get('personalDetails', {})
            official_details = employee_data.get('officialDetails', {})
            
            employees.append({
                'id': doc.id,
                'empid': employee_data.get('empid', 'N/A'),
                'name': employee_data.get('name', 'Unknown'),
                'email': employee_data.get('email', 'N/A'),
                'department': employee_data.get('department', 'N/A'),
                'position': employee_data.get('position', 'N/A'),
                'domain': employee_data.get('domain', 'General'),
                'status': employee_data.get('status', 'Active'),
                
                # Add nested details for table display
                'personalDetails': {
                    'mobileNumber': personal_details.get('mobileNumber'),
                    'empDOB': personal_details.get('empDOB'),
                    'gender': personal_details.get('gender'),
                    'maritalStatus': personal_details.get('maritalStatus'),
                    'bloodGroup': personal_details.get('bloodGroup'),
                    'address': personal_details.get('address'),
                    'city': personal_details.get('city'),
                    'state': personal_details.get('state'),
                    'pinCode': personal_details.get('pinCode'),
                    'nationality': personal_details.get('nationality')
                },
                
                'officialDetails': {
                    'empDOJ': official_details.get('empDOJ'),
                    'client': official_details.get('client'),
                    'employeeType': official_details.get('employeeType'),
                    'workLocation': official_details.get('workLocation'),
                    'reportingManager': official_details.get('reportingManager'),
                    'salary': official_details.get('salary'),
                    'pfNumber': official_details.get('pfNumber'),
                    'esiNumber': official_details.get('esiNumber'),
                    'bankAccountNumber': official_details.get('bankAccountNumber'),
                    'bankName': official_details.get('bankName'),
                    'ifscCode': official_details.get('ifscCode')
                }
            })
        
        print(f"Debug: Retrieved {len(employees)} employees from employeelists collection")
        return {
            'employees': employees,
            'total_count': len(employees)
        }
        
    except Exception as e:
        print(f"Error fetching employees: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching employees: {str(e)}")

@app.get("/api/leave/requests", response_model=Dict)
async def get_leave_requests(employee_email: str = None):
    """
    Get all leave requests from leavedetails collection
    """
    try:
        # Get leave details from leavedetails collection
        leave_details_ref = db.collection('leavedetails')
        leave_docs = leave_details_ref.get()
        
        leave_requests = []
        pending_count = 0
        approved_count = 0
        rejected_count = 0
        
        for doc in leave_docs:
            leave_data = doc.to_dict()
            
            # Determine status (you might need to adjust based on your actual status field)
            status = leave_data.get('status', 'Pending')
            if not status:
                # If no status field, you might determine based on other fields
                status = 'Pending'
            
            # Count statistics
            if status.lower() == 'pending':
                pending_count += 1
            elif status.lower() in ['approved', 'approve']:
                approved_count += 1
            elif status.lower() in ['rejected', 'reject']:
                rejected_count += 1
            else:
                pending_count += 1  # Default to pending if unclear
            
            # Create leave request object
            leave_request = {
                'id': doc.id,
                'employee': leave_data.get('appliedby', 'Unknown'),
                'empid': leave_data.get('empid', ''),
                'leave_type': leave_data.get('leavetype', 'General Leave'),
                'start_date': leave_data.get('starttime', ''),
                'end_date': leave_data.get('endtime', ''),
                'days': leave_data.get('days', 0),
                'status': status,
                'reason': leave_data.get('reason', ''),
                'applied_date': leave_data.get('applieddate', ''),
                'manager_email': leave_data.get('mgremail', '')
            }
            leave_requests.append(leave_request)
        
        # Create statistics
        stats = {
            'total_requests': len(leave_requests),
            'pending_requests': pending_count,
            'approved_requests': approved_count,
            'rejected_requests': rejected_count
        }
        
        # Sort by applied date (most recent first)
        leave_requests.sort(key=lambda x: x.get('applied_date', ''), reverse=True)
        
        return {
            'status': 'success',
            'stats': stats,
            'leave_requests': leave_requests,
            'total_count': len(leave_requests)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching leave requests: {str(e)}")

@app.get("/api/leave/summaries")
async def get_leave_summaries(year: Optional[int] = None):
    """
    Get leave summaries from leavesummaries collection
    """
    try:
        leave_summaries_ref = db.collection('leavesummaries')
        
        # Filter by year if provided
        if year:
            leave_docs = leave_summaries_ref.where('year', '==', year).get()
        else:
            leave_docs = leave_summaries_ref.get()
        
        summaries = []
        for doc in leave_docs:
            summary_data = doc.to_dict()
            
            # Calculate remaining balance
            credited = summary_data.get('creditedbalance', 0) or 0
            taken = summary_data.get('leavetaken', 0) or 0
            remaining = credited - taken
            
            summary = {
                'id': doc.id,
                'name': summary_data.get('name', 'Unknown'),
                'year': summary_data.get('year', datetime.now().year),
                'credited_balance': credited,
                'leave_taken': taken,
                'remaining_balance': remaining,
                'encash': summary_data.get('encash', 0) or 0
            }
            summaries.append(summary)
        
        return {
            'status': 'success',
            'summaries': summaries,
            'total_count': len(summaries),
            'year': year or 'all'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching leave summaries: {str(e)}")

@app.get("/api/leave/management")
async def get_leave_management_data():
    """
    Get combined leave management data (requests + summaries)
    """
    try:
        # Get leave requests
        leave_requests_response = await get_leave_requests()
        
        # Get leave summaries for current year
        current_year = datetime.now().year
        leave_summaries_response = await get_leave_summaries(year=current_year)
        
        return {
            'status': 'success',
            'requests': leave_requests_response,
            'summaries': leave_summaries_response,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching leave management data: {str(e)}")

@app.put("/api/leave/requests/{request_id}/status")
async def update_leave_request_status(request_id: str, status: str):
    """
    Update leave request status (approve/reject)
    """
    try:
        if status.lower() not in ['approved', 'rejected', 'pending']:
            raise HTTPException(status_code=400, detail="Invalid status. Must be 'approved', 'rejected', or 'pending'")
        
        # Update the document in Firestore
        leave_ref = db.collection('leavedetails').document(request_id)
        leave_doc = leave_ref.get()
        
        if not leave_doc.exists:
            raise HTTPException(status_code=404, detail="Leave request not found")
        
        # Update the status
        leave_ref.update({
            'status': status,
            'updated_at': datetime.now().isoformat()
        })
        
        return {
            'status': 'success',
            'message': f'Leave request {status} successfully',
            'request_id': request_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating leave request: {str(e)}")

@app.get("/api/leave/employee/{empid}")
async def get_employee_leave_data(empid: str):
    """
    Get leave data for a specific employee
    """
    try:
        # Get employee's leave requests
        leave_details_ref = db.collection('leavedetails')
        employee_requests = leave_details_ref.where('empid', '==', empid).get()
        
        requests = []
        for doc in employee_requests:
            leave_data = doc.to_dict()
            requests.append({
                'id': doc.id,
                'leave_type': leave_data.get('leavetype', 'General'),
                'start_date': leave_data.get('starttime', ''),
                'end_date': leave_data.get('endtime', ''),
                'days': leave_data.get('days', 0),
                'status': leave_data.get('status', 'Pending'),
                'reason': leave_data.get('reason', ''),
                'applied_date': leave_data.get('applieddate', '')
            })
        
        # Get employee's leave summary
        leave_summaries_ref = db.collection('leavesummaries')
        current_year = datetime.now().year
        
        # Try to find summary by empid or name
        summary_docs = leave_summaries_ref.where('year', '==', current_year).get()
        employee_summary = None
        
        for doc in summary_docs:
            summary_data = doc.to_dict()
            # You might need to adjust this logic based on how you link employees
            if summary_data.get('empid') == empid:
                credited = summary_data.get('creditedbalance', 0) or 0
                taken = summary_data.get('leavetaken', 0) or 0
                employee_summary = {
                    'credited_balance': credited,
                    'leave_taken': taken,
                    'remaining_balance': credited - taken,
                    'encash': summary_data.get('encash', 0) or 0,
                    'year': current_year
                }
                break
        
        return {
            'status': 'success',
            'empid': empid,
            'leave_requests': requests,
            'leave_summary': employee_summary,
            'total_requests': len(requests)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching employee leave data: {str(e)}")

@app.get("/api/leave/stats")
async def get_leave_stats():
    """
    Get leave statistics for dashboard
    """
    try:
        leave_requests_response = await get_leave_requests()
        return leave_requests_response['stats']
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching leave stats: {str(e)}")
@app.get("/api/recruitment/jobs", response_model=List[Job])
async def get_all_jobs(
    status: Optional[str] = None,
    limit: Optional[int] = 50,
    search: Optional[str] = None
):
    """
    Get all recruitment jobs from Firebase jobs collection
    
    - **status**: Filter by job status (active, inactive, draft, filled)
    - **limit**: Maximum number of jobs to return (default: 50)
    - **search**: Search in job title or description
    """
    try:
        jobs_ref = db.collection('jobs')
        
        # Apply status filter if provided
        if status:
            jobs_ref = jobs_ref.where('status', '==', status)
        
        # Apply limit
        jobs_ref = jobs_ref.limit(limit)
        
        # Execute query
        docs = jobs_ref.get()
        
        jobs = []
        for doc in docs:
            job_data = doc.to_dict()
            job_data['id'] = doc.id
            
            # Apply search filter (client-side since Firestore doesn't support full-text search)
            if search:
                title = job_data.get('title', '').lower()
                description = job_data.get('description', '').lower()
                search_term = search.lower()
                
                if search_term not in title and search_term not in description:
                    continue
            
            # Convert timestamps if needed
            if job_data.get('modifiedOn'):
                try:
                    # Handle Firestore timestamps
                    modified_on = job_data['modifiedOn']
                    if hasattr(modified_on, 'isoformat'):
                        job_data['modifiedOn'] = modified_on.isoformat()
                    elif hasattr(modified_on, 'timestamp'):
                        job_data['modifiedOn'] = datetime.fromtimestamp(modified_on.timestamp()).isoformat()
                except Exception:
                    pass
            
            jobs.append(job_data)
        
        return jobs
    
    except Exception as e:
        print(f"Error fetching jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching jobs: {str(e)}")

@app.get("/api/recruitment/jobs/{job_id}", response_model=Job)
async def get_job_by_id(job_id: str):
    """
    Get a specific job by ID
    """
    try:
        doc_ref = db.collection('jobs').document(job_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job_data = doc.to_dict()
        job_data['id'] = doc.id
        
        # Handle timestamp conversion
        if job_data.get('modifiedOn'):
            try:
                modified_on = job_data['modifiedOn']
                if hasattr(modified_on, 'isoformat'):
                    job_data['modifiedOn'] = modified_on.isoformat()
                elif hasattr(modified_on, 'timestamp'):
                    job_data['modifiedOn'] = datetime.fromtimestamp(modified_on.timestamp()).isoformat()
            except Exception:
                pass
        
        return job_data
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching job: {str(e)}")

@app.get("/api/recruitment/stats", response_model=JobStats)
async def get_recruitment_stats():
    """
    Get recruitment statistics for dashboard
    """
    try:
        jobs_ref = db.collection('jobs')
        docs = jobs_ref.get()
        
        total_jobs = 0
        active_jobs = 0
        inactive_jobs = 0
        draft_jobs = 0
        filled_jobs = 0
        
        for doc in docs:
            total_jobs += 1
            job_data = doc.to_dict()
            status = job_data.get('status', '').lower()
            
            if status == 'active':
                active_jobs += 1
            elif status == 'inactive':
                inactive_jobs += 1
            elif status == 'draft':
                draft_jobs += 1
            elif status == 'filled':
                filled_jobs += 1
        
        return JobStats(
            total_jobs=total_jobs,
            active_jobs=active_jobs,
            inactive_jobs=inactive_jobs,
            draft_jobs=draft_jobs,
            filled_jobs=filled_jobs
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recruitment stats: {str(e)}")

@app.get("/api/recruitment/dashboard", response_model=RecruitmentResponse)
async def get_recruitment_dashboard():
    """
    Get complete recruitment dashboard data (stats + recent jobs)
    """
    try:
        # Get stats
        stats = await get_recruitment_stats()
        
        # Get recent active jobs (limit 20)
        jobs = await get_all_jobs(status="active", limit=20)
        
        return RecruitmentResponse(
            stats=stats,
            jobs=jobs,
            total_count=len(jobs)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recruitment dashboard: {str(e)}")

@app.get("/api/recruitment/jobs/search")
async def search_jobs_advanced(
    title: Optional[str] = None,
    status: Optional[str] = None,
    department: Optional[str] = None,
    location: Optional[str] = None,
    limit: Optional[int] = 50
):
    """
    Advanced job search with multiple filters
    """
    try:
        jobs_ref = db.collection('jobs')
        
        # Apply Firestore filters
        if status:
            jobs_ref = jobs_ref.where('status', '==', status)
        
        jobs_ref = jobs_ref.limit(limit)
        docs = jobs_ref.get()
        
        jobs = []
        for doc in docs:
            job_data = doc.to_dict()
            job_data['id'] = doc.id
            
            # Apply client-side filters
            match = True
            
            if title and title.lower() not in job_data.get('title', '').lower():
                match = False
            if department and department.lower() not in job_data.get('department', '').lower():
                match = False
            if location and location.lower() not in job_data.get('location', '').lower():
                match = False
            
            if match:
                # Handle timestamp conversion
                if job_data.get('modifiedOn'):
                    try:
                        modified_on = job_data['modifiedOn']
                        if hasattr(modified_on, 'isoformat'):
                            job_data['modifiedOn'] = modified_on.isoformat()
                        elif hasattr(modified_on, 'timestamp'):
                            job_data['modifiedOn'] = datetime.fromtimestamp(modified_on.timestamp()).isoformat()
                    except Exception:
                        pass
                
                jobs.append(job_data)
        
        return {
            'status': 'success',
            'jobs': jobs,
            'total_count': len(jobs),
            'filters_applied': {
                'title': title,
                'status': status,
                'department': department,
                'location': location
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching jobs: {str(e)}")

@app.post("/api/recruitment/jobs")
async def create_job(job_data: dict):
    """
    Create a new job posting
    """
    try:
        # Add timestamp
        job_data['modifiedOn'] = datetime.now().isoformat()
        job_data['createdAt'] = datetime.now().isoformat()
        
        # Add to Firestore
        doc_ref = db.collection('jobs').add(job_data)
        job_id = doc_ref[1].id
        
        return {
            'status': 'success',
            'message': 'Job created successfully',
            'job_id': job_id,
            'data': job_data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating job: {str(e)}")

@app.put("/api/recruitment/jobs/{job_id}")
async def update_job(job_id: str, job_data: dict):
    """
    Update an existing job
    """
    try:
        doc_ref = db.collection('jobs').document(job_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Add modified timestamp
        job_data['modifiedOn'] = datetime.now().isoformat()
        
        # Update document
        doc_ref.update(job_data)
        
        return {
            'status': 'success',
            'message': 'Job updated successfully',
            'job_id': job_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating job: {str(e)}")

@app.delete("/api/recruitment/jobs/{job_id}")
async def delete_job(job_id: str):
    """
    Delete a job posting
    """
    try:
        doc_ref = db.collection('jobs').document(job_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Delete document
        doc_ref.delete()
        
        return {
            'status': 'success',
            'message': 'Job deleted successfully',
            'job_id': job_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting job: {str(e)}")
# RESIGNATION ENDPOINTS USING ITREQUESTS COLLECTION - FIXED VERSION
@app.get("/api/resignations", response_model=List[ResignationRequest])
async def get_all_resignations(
    status: Optional[str] = None,
    empid: Optional[str] = None,
    limit: Optional[int] = 50
):
    """
    Get all resignation requests from itrequests collection
    """
    try:
        # Query itrequests collection for resignation requests
        requests_ref = db.collection('itrequests').where('request_type', '==', 'Resignation')
        
        # Apply additional filters
        if status:
            requests_ref = requests_ref.where('status', '==', status)
        if empid:
            requests_ref = requests_ref.where('empid', '==', empid)
        
        # Apply limit and ordering - FIXED: Use proper firestore import
        requests_ref = requests_ref.limit(limit)
        
        # Try to order by modifiedOn if it exists, otherwise just get documents
        try:
            requests_ref = requests_ref.order_by('modifiedOn', direction=firestore.Query.DESCENDING)
        except Exception:
            # If ordering fails, just get the documents without ordering
            pass
        
        docs = requests_ref.get()
        
        resignations = []
        for doc in docs:
            resignation_data = doc.to_dict()
            resignation_data['id'] = doc.id
            
            # Convert timestamp if needed
            if resignation_data.get('modifiedOn'):
                try:
                    modified_on = resignation_data['modifiedOn']
                    if hasattr(modified_on, 'isoformat'):
                        resignation_data['modifiedOn'] = modified_on.isoformat()
                    elif hasattr(modified_on, 'timestamp'):
                        resignation_data['modifiedOn'] = datetime.fromtimestamp(modified_on.timestamp()).isoformat()
                except Exception:
                    pass
            
            resignations.append(resignation_data)
        
        # Sort in Python if Firestore ordering failed
        resignations.sort(key=lambda x: x.get('modifiedOn', ''), reverse=True)
        
        return resignations
    
    except Exception as e:
        print(f"Error fetching resignations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching resignations: {str(e)}")

# FIXED RESIGNATION ENDPOINTS - NO ORDERING ISSUES
@app.get("/api/resignations")
async def get_all_resignations(
    status: Optional[str] = None,
    empid: Optional[str] = None,
    limit: Optional[int] = 50
):
    """
    Get all resignation requests from itrequests collection - FIXED VERSION
    """
    try:
        print(f"Fetching resignations with filters: status={status}, empid={empid}")
        
        # Query itrequests collection for resignation requests
        requests_ref = db.collection('itrequests').where('request_type', '==', 'Resignation')
        
        # Apply additional filters
        if status:
            requests_ref = requests_ref.where('status', '==', status)
        if empid:
            requests_ref = requests_ref.where('empid', '==', empid)
        
        # Apply limit BUT NO ORDERING to avoid Firestore index issues
        requests_ref = requests_ref.limit(limit)
        
        # Get documents without ordering
        docs = list(requests_ref.get())
        print(f"Found {len(docs)} documents in itrequests with request_type=Resignation")
        
        resignations = []
        for doc in docs:
            resignation_data = doc.to_dict()
            resignation_data['id'] = doc.id
            
            # Ensure modifiedOn is always a string for consistent sorting
            if resignation_data.get('modifiedOn'):
                try:
                    modified_on = resignation_data['modifiedOn']
                    if hasattr(modified_on, 'isoformat'):
                        resignation_data['modifiedOn'] = modified_on.isoformat()
                    elif hasattr(modified_on, 'timestamp'):
                        resignation_data['modifiedOn'] = datetime.fromtimestamp(modified_on.timestamp()).isoformat()
                    # If it's already a string, keep it as is
                except Exception as e:
                    print(f"Timestamp conversion error: {e}")
                    # Set a default timestamp if conversion fails
                    resignation_data['modifiedOn'] = datetime.now().isoformat()
            else:
                # Set default timestamp if field is missing
                resignation_data['modifiedOn'] = datetime.now().isoformat()
            
            resignations.append(resignation_data)
        
        # Sort in Python instead of Firestore to avoid index issues
        try:
            resignations.sort(key=lambda x: x.get('modifiedOn', ''), reverse=True)
        except Exception as e:
            print(f"Python sorting error: {e}")
            # If sorting fails, just return unsorted data
            pass
        
        print(f"Returning {len(resignations)} resignations")
        return resignations
    
    except Exception as e:
        print(f"Error fetching resignations: {str(e)}")
        # Return empty list instead of raising exception to prevent 500 errors
        return []

@app.get("/api/resignations/stats")
async def get_resignation_stats():
    """
    Get resignation statistics from itrequests collection - FIXED VERSION
    """
    try:
        # Simple query without ordering
        requests_ref = db.collection('itrequests').where('request_type', '==', 'Resignation')
        docs = list(requests_ref.get())
        
        total_resignations = 0
        pending_approvals = 0
        approved_resignations = 0
        rejected_resignations = 0
        this_month_resignations = 0
        
        current_month = datetime.now().strftime('%Y-%m')
        
        for doc in docs:
            total_resignations += 1
            resignation_data = doc.to_dict()
            status = resignation_data.get('status', '').lower()
            modified_on = resignation_data.get('modifiedOn', '')
            
            # Count by status
            if status == 'pending':
                pending_approvals += 1
            elif status == 'approved':
                approved_resignations += 1
            elif status == 'rejected':
                rejected_resignations += 1
            
            # Count this month's resignations
            try:
                if isinstance(modified_on, str) and modified_on.startswith(current_month):
                    this_month_resignations += 1
                elif hasattr(modified_on, 'isoformat'):
                    if modified_on.isoformat().startswith(current_month):
                        this_month_resignations += 1
            except Exception:
                pass
        
        return {
            "total_resignations": total_resignations,
            "pending_approvals": pending_approvals,
            "approved_resignations": approved_resignations,
            "rejected_resignations": rejected_resignations,
            "this_month_resignations": this_month_resignations
        }
    
    except Exception as e:
        print(f"Error fetching resignation stats: {str(e)}")
        # Return zero stats instead of raising exception
        return {
            "total_resignations": 0,
            "pending_approvals": 0,
            "approved_resignations": 0,
            "rejected_resignations": 0,
            "this_month_resignations": 0
        }

@app.get("/api/resignations/dashboard")
async def get_resignation_dashboard():
    """
    Get complete resignation dashboard data - FIXED VERSION
    """
    try:
        print("Fetching resignation dashboard...")
        
        # Get stats (this will return default values if it fails)
        stats = await get_resignation_stats()
        print(f"Stats: {stats}")
        
        # Get recent resignations (this will return empty list if it fails)
        resignations = await get_all_resignations(limit=20)
        print(f"Found {len(resignations)} resignations")
        
        return {
            'status': 'success',
            'stats': stats,
            'resignations': resignations,
            'total_count': len(resignations),
            'debug_info': {
                'timestamp': datetime.now().isoformat(),
                'collection_used': 'itrequests',
                'filter': 'request_type == Resignation'
            }
        }
    
    except Exception as e:
        print(f"Dashboard error: {str(e)}")
        # Return safe default response instead of 500 error
        return {
            'status': 'error',
            'error': str(e),
            'stats': {
                'total_resignations': 0,
                'pending_approvals': 0,
                'approved_resignations': 0,
                'rejected_resignations': 0,
                'this_month_resignations': 0
            },
            'resignations': [],
            'total_count': 0,
            'message': 'Unable to fetch resignation data, showing empty state'
        }

# Enhanced create test data with proper timestamps
@app.get("/api/resignations/create-test-data-get")
async def create_test_resignation_data_get():
    """Create test resignation data - FIXED VERSION with consistent timestamps"""
    try:
        current_time = datetime.now().isoformat()
        
        test_resignations = [
            {
                'ID': f'RES_{datetime.now().strftime("%Y%m%d")}_001',
                'request_type': 'Resignation',
                'empid': 'EMP001',
                'employee_name': 'John Doe',
                'employee_email': 'john.doe@company.com',
                'department': 'Engineering',
                'position': 'Software Developer',
                'manager_name': 'Jane Smith',
                'resignation_date': '2024-01-15',
                'last_working_date': '2024-02-15',
                'reason': 'Better opportunity',
                'notice_period_days': 30,
                'status': 'Pending',
                'comments': 'Thank you for the opportunity',
                'hr_comments': '',
                'createdBy': 'john.doe@company.com',
                'modifiedBy': 'john.doe@company.com',
                'modifiedOn': current_time,  # Consistent string timestamp
                'assignedTo': 'HR'
            },
            {
                'ID': f'RES_{datetime.now().strftime("%Y%m%d")}_002',
                'request_type': 'Resignation',
                'empid': 'EMP002',
                'employee_name': 'Sarah Johnson',
                'employee_email': 'sarah.j@company.com',
                'department': 'Marketing',
                'position': 'Marketing Manager',
                'manager_name': 'Mike Davis',
                'resignation_date': '2024-01-20',
                'last_working_date': '2024-02-20',
                'reason': 'Personal reasons',
                'notice_period_days': 30,
                'status': 'Approved',
                'comments': 'Moving to another city',
                'hr_comments': 'Approved with best wishes',
                'createdBy': 'sarah.j@company.com',
                'modifiedBy': 'hr@company.com',
                'modifiedOn': current_time,  # Consistent string timestamp
                'assignedTo': 'HR'
            },
            {
                'ID': f'RES_{datetime.now().strftime("%Y%m%d")}_003',
                'request_type': 'Resignation',
                'empid': 'EMP003',
                'employee_name': 'Mike Wilson',
                'employee_email': 'mike.w@company.com',
                'department': 'Sales',
                'position': 'Sales Executive',
                'manager_name': 'Lisa Brown',
                'resignation_date': '2024-01-25',
                'last_working_date': '2024-02-25',
                'reason': 'Career change',
                'notice_period_days': 30,
                'status': 'Rejected',
                'comments': 'Want to pursue higher studies',
                'hr_comments': 'Request denied - critical project phase',
                'createdBy': 'mike.w@company.com',
                'modifiedBy': 'hr@company.com',
                'modifiedOn': current_time,  # Consistent string timestamp
                'assignedTo': 'HR'
            }
        ]
        
        created_ids = []
        for resignation_data in test_resignations:
            doc_ref = db.collection('itrequests').add(resignation_data)
            created_ids.append(doc_ref[1].id)
        
        return {
            'status': 'success',
            'message': f'Created {len(test_resignations)} test resignation requests with consistent timestamps',
            'created_ids': created_ids,
            'data': test_resignations
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'message': 'Failed to create test data'
        }
        
        
@app.get("/api/reports/types")
async def get_report_types():
    """Get available report types"""
    return {
        "report_types": [
            {"value": "employee_summary", "label": "Employee Summary Report"},
            {"value": "recruitment_analytics", "label": "Recruitment Analytics"},
            {"value": "leave_management", "label": "Leave Management Report"},
            {"value": "performance_review", "label": "Performance Review Report"},
            {"value": "asset_management", "label": "Asset Management Report"},
            {"value": "it_requests", "label": "IT Requests Report"},
            {"value": "holiday_calendar", "label": "Holiday Calendar Report"},
            {"value": "vendor_management", "label": "Vendor Management Report"}
        ]
    }

@app.post("/api/reports/generate")
async def generate_report(request: ReportRequest):
    """Generate a new report"""
    try:
        report_id = f"REP-{uuid.uuid4().hex[:12]}"
        
        # Generate report data based on type
        if request.report_type == ReportType.EMPLOYEE_SUMMARY:
            data = await generate_employee_report(request.date_from, request.date_to, request.domain)
        elif request.report_type == ReportType.RECRUITMENT_ANALYTICS:
            data = await generate_recruitment_report(request.date_from, request.date_to, request.domain)
        elif request.report_type == ReportType.LEAVE_MANAGEMENT:
            data = await generate_leave_report(request.date_from, request.date_to, request.domain)
        elif request.report_type == ReportType.PERFORMANCE_REVIEW:
            data = await generate_performance_report(request.date_from, request.date_to, request.domain)
        elif request.report_type == ReportType.ASSET_MANAGEMENT:
            data = await generate_asset_report(request.date_from, request.date_to, request.domain)
        elif request.report_type == ReportType.IT_REQUESTS:
            data = await generate_it_requests_report(request.date_from, request.date_to, request.domain)
        elif request.report_type == ReportType.HOLIDAY_CALENDAR:
            data = await generate_holiday_report(request.date_from, request.date_to, request.domain)
        elif request.report_type == ReportType.VENDOR_MANAGEMENT:
            data = await generate_vendor_report(request.date_from, request.date_to, request.domain)
        else:
            raise HTTPException(status_code=400, detail="Invalid report type")
        
        # Store report metadata (you can store this in a new 'reports' collection)
        report_doc = {
            "id": report_id,
            "report_type": request.report_type,
            "period_start": request.date_from,
            "period_end": request.date_to,
            "domain": request.domain,
            "created_at": datetime.now(),
            "status": "completed",
            "record_count": len(data),
            "data": data
        }
        
        # Insert into reports collection (create if doesn't exist)
        await db.reports.insert_one(report_doc)
        
        return {
            "report_id": report_id,
            "status": "completed",
            "record_count": len(data),
            "message": "Report generated successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

@app.get("/api/reports")
async def get_generated_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """Get list of generated reports"""
    try:
        # Check if reports collection exists
        collection_names = await db.list_collection_names()
        if "reports" not in collection_names:
            # Return empty list if collection doesn't exist yet
            return {
                "reports": [],
                "message": "No reports collection found. Generate your first report to get started."
            }
        
        reports = await db.reports.find().sort("created_at", -1).skip(skip).limit(limit).to_list(None)
        
        return {
            "reports": [
                {
                    "id": report["id"],
                    "report_type": report["report_type"],
                    "period": f"{report.get('period_start', '')} - {report.get('period_end', '')}",
                    "created_at": report["created_at"],
                    "record_count": report["record_count"],
                    "status": report["status"]
                }
                for report in reports
            ]
        }
    except Exception as e:
        # More detailed error logging
        print(f"Error in get_generated_reports: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching reports: {str(e)}")


@app.get("/api/reports/download/{report_id}")
async def download_report(report_id: str):
    """Download report as CSV"""
    try:
        report = await db.reports.find_one({"id": report_id})
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Convert data to DataFrame and CSV
        df = pd.DataFrame(report["data"])
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        return StreamingResponse(
            io.BytesIO(csv_buffer.getvalue().encode('utf-8')),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={report_id}_{report['report_type']}.csv"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading report: {str(e)}")

# Report Generation Functions
async def generate_employee_report(date_from: date = None, date_to: date = None, domain: str = None):
    """Generate employee summary report"""
    match_filter = {}
    if domain:
        match_filter["domain"] = domain
    
    pipeline = [
        {"$match": match_filter},
        {
            "$lookup": {
                "from": "userroles",
                "localField": "personalDetails.email",
                "foreignField": "email", 
                "as": "role_info"
            }
        },
        {
            "$project": {
                "employee_id": {"$ifNull": ["$personalDetails.empId", "N/A"]},
                "name": "$name",
                "email": {"$ifNull": ["$personalDetails.email", "N/A"]},
                "department": {"$ifNull": ["$personalDetails.department", "N/A"]},
                "designation": {"$ifNull": ["$personalDetails.designation", "N/A"]},
                "role": {"$ifNull": [{"$arrayElemAt": ["$role_info.role", 0]}, "N/A"]},
                "manager": {"$ifNull": [{"$arrayElemAt": ["$role_info.mgrName", 0]}, "N/A"]},
                "domain": "$domain"
            }
        }
    ]
    
    employees = await db.employeelists.aggregate(pipeline).to_list(None)
    return employees

async def generate_recruitment_report(date_from: date = None, date_to: date = None, domain: str = None):
    """Generate recruitment analytics report"""
    match_filter = {}
    if domain:
        match_filter["domain"] = domain
        
    pipeline = [
        {"$match": match_filter},
        {
            "$lookup": {
                "from": "jobs",
                "localField": "processflow",
                "foreignField": "_id",
                "as": "job_info"
            }
        },
        {
            "$project": {
                "candidate_name": "$candidateName",
                "scores": "$scores",
                "domain": "$domain",
                "processflow": "$processflow",
                "job_title": {"$arrayElemAt": ["$job_info.title", 0]},
                "test_report": "$testreport"
            }
        }
    ]
    
    candidates = await db.profiles.aggregate(pipeline).to_list(None)
    return candidates

async def generate_leave_report(date_from: date = None, date_to: date = None, domain: str = None):
    """Generate leave management report"""
    match_filter = {}
    if date_from and date_to:
        match_filter["starttime"] = {
            "$gte": date_from.isoformat(),
            "$lte": date_to.isoformat()
        }
    
    pipeline = [
        {"$match": match_filter},
        {
            "$lookup": {
                "from": "employeelists",
                "localField": "empid",
                "foreignField": "personalDetails.empId",
                "as": "employee_info"
            }
        },
        {
            "$project": {
                "employee_id": "$empid",
                "employee_name": {"$arrayElemAt": ["$employee_info.name", 0]},
                "applied_by": "$appliedby",
                "days": "$days",
                "start_time": "$starttime",
                "manager_email": "$mgremail",
                "leave_type": "$leavetype"
            }
        }
    ]
    
    leaves = await db.leavedetails.aggregate(pipeline).to_list(None)
    return leaves

async def generate_performance_report(date_from: date = None, date_to: date = None, domain: str = None):
    """Generate performance review report"""
    match_filter = {}
    if domain:
        match_filter["domain"] = domain
        
    reviews = await db.performancereviews.find(match_filter, {
        "name": 1,
        "reviewername": 1,
        "revieweremail": 1,
        "reviewerstatus": 1,
        "pdp": 1,
        "_id": 0
    }).to_list(None)
    
    return reviews

async def generate_asset_report(date_from: date = None, date_to: date = None, domain: str = None):
    """Generate asset management report"""
    match_filter = {}
    if domain:
        match_filter["domain"] = domain
        
    assets = await db.assetlists.find(match_filter, {
        "id": 1,
        "make": 1,
        "theftInsrances": 1,
        "insuranceExpiryDate": 1,
        "comments": 1,
        "_id": 0
    }).to_list(None)
    
    return assets

async def generate_it_requests_report(date_from: date = None, date_to: date = None, domain: str = None):
    """Generate IT requests report"""
    it_requests = await db.itrequests.find({}, {
        "ID": 1,
        "createdBy": 1,
        "assignedTo": 1,
        "modifiedOn": 1,
        "modifiedBy": 1,
        "_id": 0
    }).to_list(None)
    
    return it_requests

async def generate_holiday_report(date_from: date = None, date_to: date = None, domain: str = None):
    """Generate holiday calendar report"""
    match_filter = {}
    if domain:
        match_filter["domain"] = domain
    if date_from and date_to:
        match_filter["year"] = {"$gte": date_from.year, "$lte": date_to.year}
        
    holidays = await db.holidays.find(match_filter, {
        "day": 1,
        "remarks": 1,
        "year": 1,
        "domain": 1,
        "type": 1,
        "_id": 0
    }).to_list(None)
    
    return holidays

async def generate_vendor_report(date_from: date = None, date_to: date = None, domain: str = None):
    """Generate vendor management report"""
    match_filter = {}
    if domain:
        match_filter["domain"] = domain
        
    vendors = await db.vendorlists.find(match_filter, {
        "name": 1,
        "contactNumber": 1,
        "address": 1,
        "domain": 1,
        "status": 1,
        "_id": 0
    }).to_list(None)
    
    return vendors


@app.get("/api/config/general")
async def get_general_config():
    """Get general configuration (leave policies)"""
    try:
        # Check if collection exists
        collection_names = await db.list_collection_names()
        if "configgenerals" not in collection_names:
            # Return default values if collection doesn't exist
            default_config = {
                "CL": 12,
                "SL": 12, 
                "PL": 21,
                "CF": 10,
                "comments": ""
            }
            return {"config": default_config}
        
        config = await db.configgenerals.find_one({})
        if not config:
            # Return default values if no config exists
            default_config = {
                "CL": 12,
                "SL": 12, 
                "PL": 21,
                "CF": 10,
                "comments": ""
            }
            return {"config": default_config}
        
        # Remove MongoDB _id from response
        if "_id" in config:
            del config["_id"]
            
        return {"config": config}
        
    except Exception as e:
        print(f"Error in get_general_config: {str(e)}")
        # Return default config even on error for better UX
        default_config = {
            "CL": 12,
            "SL": 12, 
            "PL": 21,
            "CF": 10,
            "comments": ""
        }
        return {"config": default_config}

@app.put("/api/config/general")
async def update_general_config(config: ConfigGeneral):
    """Update general configuration"""
    try:
        config_dict = config.dict()
        config_dict["updated_at"] = datetime.now()
        
        # Use upsert to create if doesn't exist
        result = await db.configgenerals.replace_one(
            {},  # Empty filter to replace first document
            config_dict,
            upsert=True
        )
        
        return {"message": "General configuration updated successfully"}
        
    except Exception as e:
        print(f"Error in update_general_config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating general config: {str(e)}")

@app.get("/api/config/pdp")
async def get_pdp_configs():
    """Get PDP configurations"""
    try:
        # Check if collection exists
        collection_names = await db.list_collection_names()
        if "configpdps" not in collection_names:
            return {"configs": []}
        
        configs = await db.configpdps.find({}).sort("year", -1).to_list(None)
        
        # Convert ObjectId to string for JSON serialization
        for config in configs:
            if "_id" in config:
                config["_id"] = str(config["_id"])
        
        return {"configs": configs}
        
    except Exception as e:
        print(f"Error in get_pdp_configs: {str(e)}")
        return {"configs": []}

@app.post("/api/config/pdp")
async def create_pdp_config(config: ConfigPDP):
    """Create new PDP configuration"""
    try:
        config_dict = config.dict()
        config_dict["created_at"] = datetime.now()
        
        result = await db.configpdps.insert_one(config_dict)
        return {"message": "PDP configuration created successfully", "id": str(result.inserted_id)}
        
    except Exception as e:
        print(f"Error in create_pdp_config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating PDP config: {str(e)}")

@app.put("/api/config/pdp/{config_id}")
async def update_pdp_config(config_id: str, config: ConfigPDP):
    """Update PDP configuration"""
    try:
        if not ObjectId.is_valid(config_id):
            raise HTTPException(status_code=400, detail="Invalid config ID")
            
        config_dict = config.dict()
        config_dict["updated_at"] = datetime.now()
        
        result = await db.configpdps.update_one(
            {"_id": ObjectId(config_id)},
            {"$set": config_dict}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="PDP configuration not found")
            
        return {"message": "PDP configuration updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in update_pdp_config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating PDP config: {str(e)}")

@app.delete("/api/config/pdp/{config_id}")
async def delete_pdp_config(config_id: str):
    """Delete PDP configuration"""
    try:
        if not ObjectId.is_valid(config_id):
            raise HTTPException(status_code=400, detail="Invalid config ID")
            
        result = await db.configpdps.delete_one({"_id": ObjectId(config_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="PDP configuration not found")
            
        return {"message": "PDP configuration deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in delete_pdp_config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting PDP config: {str(e)}")

@app.get("/api/config/domains")
async def get_domains():
    """Get available domains for PDP configuration"""
    try:
        # Check if domains collection exists and has data
        collection_names = await db.list_collection_names()
        
        if "domains" in collection_names:
            domains_from_db = await db.domains.find({}).to_list(None)
            if domains_from_db:
                # Extract domain names from your domains collection
                domain_list = [domain.get("name", "Unknown") for domain in domains_from_db]
            else:
                # Fallback to default domains
                domain_list = ["HR", "IT", "Finance", "Operations", "Marketing", "Sales", "Admin"]
        else:
            # Fallback to default domains if collection doesn't exist
            domain_list = ["HR", "IT", "Finance", "Operations", "Marketing", "Sales", "Admin"]
        
        return {"domains": domain_list}
        
    except Exception as e:
        print(f"Error in get_domains: {str(e)}")
        # Return default domains even on error
        return {"domains": ["HR", "IT", "Finance", "Operations", "Marketing", "Sales", "Admin"]}

@app.get("/api/config/all")
async def get_all_configs():
    """Get all configuration types"""
    try:
        collection_names = await db.list_collection_names()
        if "configall" not in collection_names:
            return {"configs": []}
            
        configs = await db.configall.find({}).to_list(None)
        
        # Convert ObjectId to string
        for config in configs:
            if "_id" in config:
                config["_id"] = str(config["_id"])
        
        return {"configs": configs}
        
    except Exception as e:
        print(f"Error in get_all_configs: {str(e)}")
        return {"configs": []}
        

@app.get("/employees/new-hires-this-month/public")
async def get_new_hires_this_month_public():
    """Get count of employees hired this month - Public endpoint"""
    try:
        from datetime import datetime
        current_month = datetime.now().strftime('%Y-%m')
        
        employees_ref = db.collection('employeelists')
        docs = employees_ref.stream()
        
        new_hires_count = 0
        for doc in docs:
            emp_data = doc.to_dict()
            official_details = emp_data.get('officialDetails', {})
            doj = official_details.get('empDOJ', '')
            
            # Check if hire date is in current month (format: YYYY-MM-DD)
            if doj and doj.startswith(current_month):
                new_hires_count += 1
        
        return {
            "new_hires_count": new_hires_count,
            "month": current_month
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching new hires: {str(e)}")

@app.get("/api/attendance/stats/public")
async def get_attendance_stats_public():
    """Get attendance statistics - Public endpoint"""
    try:
        # Call your existing attendance function
        attendance_data = await get_today_attendance()
        return {
            "present_today": attendance_data.stats.present_today,
            "on_leave": attendance_data.stats.on_leave,
            "total_employees": attendance_data.stats.total_employees,
            "absent_today": attendance_data.stats.absent_today,
            "late_arrivals": attendance_data.stats.late_arrivals
        }
    except Exception as e:
        # If attendance system not set up, return mock data
        return {
            "present_today": 0,
            "on_leave": 0,
            "total_employees": 0,
            "absent_today": 0,
            "late_arrivals": 0
        }
        
@app.get("/debug/employee-ids")
async def get_all_employee_ids():
    """Debug endpoint to see all employee document IDs"""
    try:
        employees_ref = db.collection('employeelists')
        docs = employees_ref.stream()
        
        employee_ids = []
        for doc in docs:
            employee_data = doc.to_dict()
            employee_ids.append({
                'document_id': doc.id,  # This is the actual document ID
                'empid': employee_data.get('empid'),  # This is the empid field value
                'name': employee_data.get('name'),
                'email': employee_data.get('email')
            })
        
        return {
            'total_employees': len(employee_ids),
            'employee_ids': employee_ids
        }
    except Exception as e:
        return {'error': str(e)}
    
@app.get("/debug/employee-mapping/{employee_id}")
async def debug_employee_mapping(employee_id: str):
    """Debug endpoint to show ID mapping"""
    try:
        # Search in employee_id collection
        employee_ids_ref = db.collection('employee_id')
        employee_ids_docs = employee_ids_ref.stream()
        
        mappings = []
        
        for doc in employee_ids_docs:
            doc_data = doc.to_dict()
            if 'employee_ids' in doc_data:
                for emp_entry in doc_data['employee_ids']:
                    mappings.append({
                        'empid': emp_entry.get('empid'),
                        'document_id': emp_entry.get('document_id'),
                        'matches_search': (emp_entry.get('empid') == employee_id or 
                                         emp_entry.get('document_id') == employee_id)
                    })
        
        return {
            'searched_id': employee_id,
            'mappings': mappings,
            'total_found': len(mappings)
        }
        
    except Exception as e:
        return {'error': str(e)}
@app.get("/debug/all-employees")
async def debug_all_employees():
    """Debug endpoint to see all employees in both collections"""
    try:
        result = {
            'employee_id_collection': [],
            'employeelists_collection': []
        }
        
        # Check employee_id collection
        employee_ids_ref = db.collection('employee_id')
        employee_ids_docs = employee_ids_ref.stream()
        
        for doc in employee_ids_docs:
            doc_data = doc.to_dict()
            result['employee_id_collection'].append({
                'document_id': doc.id,
                'data': doc_data
            })
        
        # Check employeelists collection
        employeelists_ref = db.collection('employeelists')
        employeelists_docs = employeelists_ref.stream()
        
        for doc in employeelists_docs:
            doc_data = doc.to_dict()
            result['employeelists_collection'].append({
                'document_id': doc.id,
                'name': doc_data.get('name'),
                'email': doc_data.get('email'),
                'empid': doc_data.get('empid')
            })
        
        return result
        
    except Exception as e:
        return {'error': str(e)}










if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
