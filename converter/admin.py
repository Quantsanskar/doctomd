from django.contrib import admin
from .models import ConversionBatch, UploadedFile


@admin.register(ConversionBatch)
class ConversionBatchAdmin(admin.ModelAdmin):
    list_display = ['id', 'status', 'created_at', 'completed_at']
    list_filter = ['status', 'created_at']
    readonly_fields = ['id', 'created_at']


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ['id', 'original_filename', 'status', 'conversion_batch', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['original_filename']
    readonly_fields = ['id', 'created_at']
