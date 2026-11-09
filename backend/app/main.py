from fastapi import FastAPI

app = FastAPI(
    title="Flowwatch",
    description="Monitor n8n workflow runs and alert on failures",
    version="0.1.0",
)


@app.get("/health", tags=["health"])
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}