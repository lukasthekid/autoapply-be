from django.db import models


class TypstTemplate(models.Model):
    """Model for Typst templates stored in the database."""
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    version = models.IntegerField()
    name = models.CharField(max_length=255)
    code = models.TextField()
    
    class Meta:
        db_table = 'typst_templates'
        ordering = ['-created_at']
        verbose_name = 'Typst Template'
        verbose_name_plural = 'Typst Templates'
    
    def __str__(self):
        return f"{self.name} (v{self.version})"
