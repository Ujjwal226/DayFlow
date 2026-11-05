from fastapi import APIRouter
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.categories import router as categories_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.projects import router as projects_router
from app.api.v1.endpoints.recurring_tasks import router as recurring_tasks_router
from app.api.v1.endpoints.subtasks import router as subtasks_router
from app.api.v1.endpoints.tags import router as tags_router
from app.api.v1.endpoints.tasks import router as tasks_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(projects_router)
api_v1_router.include_router(recurring_tasks_router)
api_v1_router.include_router(categories_router)
api_v1_router.include_router(tags_router)
api_v1_router.include_router(tasks_router)
api_v1_router.include_router(subtasks_router)
