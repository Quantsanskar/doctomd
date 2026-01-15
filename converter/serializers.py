from rest_framework import serializers
from django.conf import settings
from .models import ConversionBatch, UploadedFile
import os


class UploadedFileSerializer(serializers.ModelSerializer):
    """Serializer for individual uploaded files"""
    markdown_filename = serializers.ReadOnlyField()
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = UploadedFile
        fields = [
            'id', 'original_filename', 'file_extension', 'status',
            'error_message', 'markdown_filename', 'markdown_content',
            'download_url', 'created_at'
        ]

    def get_download_url(self, obj):
        if obj.converted_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.converted_file.url)
        return None


class ConversionBatchSerializer(serializers.ModelSerializer):
    """Serializer for conversion batch"""
    files = UploadedFileSerializer(many=True, read_only=True)
    file_count = serializers.SerializerMethodField()

    class Meta:
        model = ConversionBatch
        fields = [
            'id', 'status', 'created_at', 'completed_at',
            'error_message', 'files', 'file_count'
        ]

    def get_file_count(self, obj):
        return obj.files.count()


class FileUploadSerializer(serializers.Serializer):
    """Serializer for file upload validation"""
    files = serializers.ListField(
        child=serializers.FileField(),
        min_length=1,
        max_length=settings.MAX_FILES_UPLOAD,
        help_text=f"Upload up to {settings.MAX_FILES_UPLOAD} .doc or .docx files"
    )

    def validate_files(self, files):
        """Validate uploaded files"""
        allowed_extensions = ['.doc', '.docx']
        max_files = settings.MAX_FILES_UPLOAD

        if len(files) > max_files:
            raise serializers.ValidationError(
                f"Maximum {max_files} files allowed. You uploaded {len(files)} files."
            )

        for file in files:
            # Get file extension
            filename = file.name
            _, ext = os.path.splitext(filename)
            ext = ext.lower()

            if ext not in allowed_extensions:
                raise serializers.ValidationError(
                    f"Invalid file type: {filename}. Only .doc and .docx files are allowed."
                )

            # Check file size (max 10MB per file)
            if file.size > 10 * 1024 * 1024:
                raise serializers.ValidationError(
                    f"File too large: {filename}. Maximum size is 10MB."
                )

        return files
