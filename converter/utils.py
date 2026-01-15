"""
Conversion utilities for .doc/.docx to Markdown using Pandoc
"""
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from django.conf import settings


def check_pandoc_installed():
    """Check if Pandoc is installed on the system"""
    try:
        result = subprocess.run(
            ['pandoc', '--version'],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def convert_doc_to_docx(doc_path: str, output_dir: str = None) -> str:
    """
    Convert .doc file to .docx using pandoc
    
    Args:
        doc_path: Path to the .doc file
        output_dir: Directory to save the converted file (optional)
    
    Returns:
        Path to the converted .docx file
    """
    doc_path = Path(doc_path)
    
    if output_dir:
        output_path = Path(output_dir) / f"{doc_path.stem}.docx"
    else:
        output_path = doc_path.with_suffix('.docx')
    
    try:
        result = subprocess.run(
            ['pandoc', str(doc_path), '-o', str(output_path)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            raise Exception(f"Pandoc conversion failed: {result.stderr}")
        
        return str(output_path)
    
    except subprocess.TimeoutExpired:
        raise Exception("Conversion timed out")
    except Exception as e:
        raise Exception(f"Error converting .doc to .docx: {str(e)}")


def convert_docx_to_markdown(docx_path: str, output_dir: str = None) -> tuple:
    """
    Convert .docx file to Markdown using pandoc
    
    Args:
        docx_path: Path to the .docx file
        output_dir: Directory to save the converted file (optional)
    
    Returns:
        Tuple of (path to markdown file, markdown content)
    """
    docx_path = Path(docx_path)
    
    if output_dir:
        output_path = Path(output_dir) / f"{docx_path.stem}.md"
    else:
        output_path = docx_path.with_suffix('.md')
    
    try:
        # Use pandoc to convert docx to markdown
        result = subprocess.run(
            [
                'pandoc',
                str(docx_path),
                '-f', 'docx',
                '-t', 'markdown',
                '-o', str(output_path),
                '--wrap=none',  # Don't wrap lines
                '--extract-media', str(output_path.parent / 'media')  # Extract embedded images
            ],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            raise Exception(f"Pandoc conversion failed: {result.stderr}")
        
        # Read the markdown content
        with open(output_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        return str(output_path), markdown_content
    
    except subprocess.TimeoutExpired:
        raise Exception("Conversion timed out")
    except Exception as e:
        raise Exception(f"Error converting .docx to markdown: {str(e)}")


def convert_file_to_markdown(file_path: str, output_dir: str) -> tuple:
    """
    Convert a .doc or .docx file to Markdown
    
    This function handles the full conversion:
    1. If .doc, first converts to .docx
    2. Then converts .docx to Markdown
    
    Args:
        file_path: Path to the input file (.doc or .docx)
        output_dir: Directory to save output files
    
    Returns:
        Tuple of (markdown file path, markdown content)
    """
    file_path = Path(file_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    extension = file_path.suffix.lower()
    
    temp_docx = None
    
    try:
        if extension == '.doc':
            # First convert .doc to .docx
            docx_path = convert_doc_to_docx(str(file_path), str(output_dir))
            temp_docx = docx_path
        elif extension == '.docx':
            docx_path = str(file_path)
        else:
            raise ValueError(f"Unsupported file type: {extension}")
        
        # Convert .docx to Markdown
        md_path, md_content = convert_docx_to_markdown(docx_path, str(output_dir))
        
        return md_path, md_content
    
    finally:
        # Clean up temporary .docx file if created from .doc
        if temp_docx and os.path.exists(temp_docx):
            try:
                os.remove(temp_docx)
            except:
                pass


def process_uploaded_file(uploaded_file_instance):
    """
    Process an uploaded file model instance
    
    Args:
        uploaded_file_instance: UploadedFile model instance
    
    Returns:
        Tuple of (success: bool, result: str or error message)
    """
    from .models import UploadedFile
    from django.core.files.base import ContentFile
    
    try:
        uploaded_file_instance.status = 'converting'
        uploaded_file_instance.save()
        
        # Create output directory
        output_dir = Path(settings.MEDIA_ROOT) / 'converted' / str(uploaded_file_instance.conversion_batch.id)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get the file path
        file_path = uploaded_file_instance.original_file.path
        
        # Convert to markdown
        md_path, md_content = convert_file_to_markdown(file_path, str(output_dir))
        
        # Save the converted file
        md_filename = uploaded_file_instance.markdown_filename
        
        # Read the markdown file and save it to the model
        with open(md_path, 'rb') as f:
            uploaded_file_instance.converted_file.save(md_filename, ContentFile(f.read()))
        
        uploaded_file_instance.markdown_content = md_content
        uploaded_file_instance.status = 'converted'
        uploaded_file_instance.save()
        
        return True, md_content
    
    except Exception as e:
        uploaded_file_instance.status = 'failed'
        uploaded_file_instance.error_message = str(e)
        uploaded_file_instance.save()
        return False, str(e)
