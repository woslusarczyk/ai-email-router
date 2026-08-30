from fastapi import FastAPI

app = FastAPI(
    title="AI Email Router",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
