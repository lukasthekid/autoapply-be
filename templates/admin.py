from django.contrib import admin
from .models import TypstTemplate


@admin.register(TypstTemplate)
class TypstTemplateAdmin(admin.ModelAdmin):
    """Admin interface for TypstTemplate model."""
    list_display = ('id', 'name', 'version', 'created_at', 'updated_at')
    list_filter = ('version', 'created_at', 'updated_at')
    search_fields = ('name', 'code')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
