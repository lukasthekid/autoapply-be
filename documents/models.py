from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class UserDocumentStatus(models.Model):
    """Track document upload status for users."""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='document_status',
        primary_key=True
    )
    has_uploaded_document = models.BooleanField(default=False)
    last_upload_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_document_status'
        verbose_name = 'User Document Status'
        verbose_name_plural = 'User Document Statuses'
    
    def __str__(self):
        return f"Document status for {self.user.username}"
