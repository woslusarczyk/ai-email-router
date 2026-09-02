from fastapi import FastAPI

from app.agent import route_message
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
    department = route_message(sender_email=request.email, message=request.message)
    return RouteResponse(department=department, department_email=department.email)
