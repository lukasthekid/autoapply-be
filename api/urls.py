"""
URL configuration for api project.
"""
from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI
from django.core.exceptions import RequestDataTooBig
from templates.routers import router as templates_router
from templates.cover_letters import router as cover_letters_router
from authentication.routers import router as auth_router
from jobs.routers import router as jobs_router
from jobs.applications import router as applications_router
from documents.routers import router as documents_router
from documents.exceptions import handle_request_too_large

# Create Django Ninja API instance
api = NinjaAPI(
    title="AutoApply API",
    description="Generate Perfect Cover Letters with AI",
    version="1.0.0",
)

# Register custom exception handlers
@api.exception_handler(RequestDataTooBig)
def request_too_large_handler(request, exc):
    return api.create_response(
        request,
        handle_request_too_large(request, exc),
        status=413
    )

# Register routers
api.add_router("/auth", auth_router)
api.add_router("/templates", templates_router)
api.add_router("/cover-letters", cover_letters_router)
api.add_router("/jobs", jobs_router)
api.add_router("/applications", applications_router)
api.add_router("/documents", documents_router)


@api.get("/")
def hello(request):
    """Health check endpoint"""
    return {"message": "Welcome to AutoApply API"}


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
]
