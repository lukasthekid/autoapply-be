"""
URL configuration for api project.
"""
from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI
from templates.routers import router as templates_router
from authentication.routers import router as auth_router

# Create Django Ninja API instance
api = NinjaAPI(
    title="AutoApply API",
    description="Generate Perfect Cover Letters with AI",
    version="1.0.0",
)

# Register routers
api.add_router("/auth", auth_router)
api.add_router("/templates", templates_router)


@api.get("/")
def hello(request):
    """Health check endpoint"""
    return {"message": "Welcome to AutoApply API"}


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
]
