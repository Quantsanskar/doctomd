from django.urls import path
from . import views

urlpatterns = [
    # Frontend
    path('', views.index, name='index'),
    
    # API endpoints
    path('api/check-pandoc/', views.check_pandoc, name='check-pandoc'),
    path('api/upload/', views.upload_files, name='upload-files'),
    path('api/batch/<uuid:batch_id>/', views.get_batch, name='get-batch'),
    path('api/batch/<uuid:batch_id>/download/', views.download_batch_zip, name='download-batch'),
    path('api/file/<uuid:file_id>/download/', views.download_file, name='download-file'),
    path('api/batches/', views.list_batches, name='list-batches'),
]
