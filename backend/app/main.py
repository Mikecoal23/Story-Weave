from fastapi import FastAPI

from app.api.routes import health

app = FastAPI(title="StoryWeave API")

app.include_router(health.router)
