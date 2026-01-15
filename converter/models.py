from django.db import models
import uuid
import os


def upload_to_path(instance, filename):
    """Generate upload path for files"""
    return f'uploads/{instance.conversion_batch.id}/{filename}'


def converted_file_path(instance, filename):
    """Generate path for converted files"""
    return f'converted/{instance.conversion_batch.id}/{filename}'


class ConversionBatch(models.Model):
    """Model to track a batch of file conversions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='pending')
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Batch {self.id} - {self.status}"


class UploadedFile(models.Model):
    """Model to track individual uploaded files"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversion_batch = models.ForeignKey(
        ConversionBatch, 
        on_delete=models.CASCADE, 
        related_name='files'
    )
    original_file = models.FileField(upload_to=upload_to_path)
    original_filename = models.CharField(max_length=255)
    file_extension = models.CharField(max_length=10)
    converted_file = models.FileField(upload_to=converted_file_path, null=True, blank=True)
    markdown_content = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[
        ('uploaded', 'Uploaded'),
        ('converting', 'Converting'),
        ('converted', 'Converted'),
        ('failed', 'Failed'),
    ], default='uploaded')
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.original_filename} - {self.status}"

    @property
    def markdown_filename(self):
        """Get the markdown filename"""
        name, _ = os.path.splitext(self.original_filename)
        return f"{name}.md"
