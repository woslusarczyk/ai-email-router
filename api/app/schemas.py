from pydantic import BaseModel, EmailStr

from app.departments import Department


class RouteRequest(BaseModel):
    email: EmailStr
    message: str


class RouteResponse(BaseModel):
    department: Department
    department_email: str
