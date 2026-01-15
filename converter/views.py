from rest_framework import status, viewsets
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, FileResponse
from django.utils import timezone
from django.conf import settings
import os
import zipfile
import io

from .models import ConversionBatch, UploadedFile
from .serializers import (
    ConversionBatchSerializer, 
    UploadedFileSerializer, 
    FileUploadSerializer
)
from .utils import process_uploaded_file, check_pandoc_installed


def index(request):
    """Render the main upload page"""
    return render(request, 'converter/index.html')


@api_view(['GET'])
def check_pandoc(request):
    """Check if Pandoc is installed"""
    is_installed = check_pandoc_installed()
    return Response({
        'pandoc_installed': is_installed,
        'message': 'Pandoc is installed and ready' if is_installed else 'Pandoc is not installed. Please install Pandoc to use this service.'
    })


@api_view(['POST'])
def upload_files(request):
    """
    Upload files for conversion
    
    Accepts up to 10 .doc or .docx files
    """
    # Check if Pandoc is installed
    if not check_pandoc_installed():
        return Response(
            {'error': 'Pandoc is not installed on the server. Please install Pandoc first.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    # Validate the uploaded files
    serializer = FileUploadSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    files = serializer.validated_data['files']
    
    # Create a new conversion batch
    batch = ConversionBatch.objects.create(status='processing')
    
    # Save uploaded files
    uploaded_files = []
    for file in files:
        filename = file.name
        _, ext = os.path.splitext(filename)
        
        uploaded_file = UploadedFile.objects.create(
            conversion_batch=batch,
            original_file=file,
            original_filename=filename,
            file_extension=ext.lower()
        )
        uploaded_files.append(uploaded_file)
    
    # Process each file
    all_success = True
    for uploaded_file in uploaded_files:
        success, _ = process_uploaded_file(uploaded_file)
        if not success:
            all_success = False
    
    # Update batch status
    batch.completed_at = timezone.now()
    batch.status = 'completed' if all_success else 'failed'
    batch.save()
    
    # Return the results
    batch.refresh_from_db()
    response_serializer = ConversionBatchSerializer(batch, context={'request': request})
    
    return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def get_batch(request, batch_id):
    """Get conversion batch details"""
    batch = get_object_or_404(ConversionBatch, id=batch_id)
    serializer = ConversionBatchSerializer(batch, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def download_file(request, file_id):
    """Download a single converted markdown file"""
    uploaded_file = get_object_or_404(UploadedFile, id=file_id)
    
    if not uploaded_file.converted_file:
        return Response(
            {'error': 'File has not been converted yet'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    response = FileResponse(
        uploaded_file.converted_file.open('rb'),
        as_attachment=True,
        filename=uploaded_file.markdown_filename
    )
    return response


@api_view(['GET'])
def download_batch_zip(request, batch_id):
    """Download all converted files in a batch as a ZIP"""
    batch = get_object_or_404(ConversionBatch, id=batch_id)
    
    # Create a ZIP file in memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for uploaded_file in batch.files.filter(status='converted'):
            if uploaded_file.converted_file:
                # Read the converted file
                file_content = uploaded_file.converted_file.read()
                zip_file.writestr(uploaded_file.markdown_filename, file_content)
    
    zip_buffer.seek(0)
    
    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="converted_files_{batch_id}.zip"'
    
    return response


@api_view(['GET'])
def list_batches(request):
    """List all conversion batches"""
    batches = ConversionBatch.objects.all()[:20]  # Last 20 batches
    serializer = ConversionBatchSerializer(batches, many=True, context={'request': request})
    return Response(serializer.data)
