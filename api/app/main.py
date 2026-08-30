from fastapi import FastAPI

from app.departments import DEPARTMENT_EMAILS, Department
from app.schemas import RouteRequest, RouteResponse

app = FastAPI(
    title="AI Email Router",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/route", response_model=RouteResponse)
def route(request: RouteRequest) -> RouteResponse:
    department = Department.OTHER
    return RouteResponse(department=department, department_email=DEPARTMENT_EMAILS[department])
