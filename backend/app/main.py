from fastapi import FastAPI

app = FastAPI(
    title="Flowwatch",
    description="Monitor n8n workflow runs and alert on failures",
    version="0.1.0",
)


@app.on_event("startup")
async def on_startup():
    """Ensure database tables are created on startup."""
    from .database import Base, engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health", tags=["health"])
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}