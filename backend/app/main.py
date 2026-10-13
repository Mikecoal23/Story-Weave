from fastapi import FastAPI

from app.api.routes.caregivers import router as caregivers_router
from app.api.routes.children import router as children_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.health import router as health_router
from app.api.routes.sessions import router as sessions_router
from app.api.routes.stories import router as stories_router

app = FastAPI(title="StoryWeave API", version="0.1.0")
app.include_router(health_router)
app.include_router(caregivers_router)
app.include_router(children_router)
app.include_router(sessions_router)
app.include_router(stories_router)
app.include_router(dashboard_router)
