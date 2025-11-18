from django.contrib import admin
from .models import UserDocumentStatus


@admin.register(UserDocumentStatus)
class UserDocumentStatusAdmin(admin.ModelAdmin):
    list_display = ('user', 'has_uploaded_document', 'last_upload_date', 'updated_at')
    list_filter = ('has_uploaded_document', 'last_upload_date')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
