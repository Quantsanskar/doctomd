# DocToMD - Word to Markdown Converter

A web application built with Django REST Framework that converts Word documents (.doc, .docx) to Markdown format using Pandoc.

## Features

- Upload up to 10 files at once
- Supports both .doc and .docx formats
- Automatic conversion of .doc to .docx before Markdown conversion (Pandoc works better with .docx)
- Download individual converted files or all files as a ZIP
- Clean, modern UI with drag-and-drop support
- REST API for programmatic access

## Prerequisites

1. **Python 3.8+**
2. **Pandoc** - Must be installed on your system

### Installing Pandoc

**Windows:**
```bash
# Using Chocolatey
choco install pandoc

# Or download from https://pandoc.org/installing.html
```

**macOS:**
```bash
brew install pandoc
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install pandoc
```

## Installation

1. **Create a virtual environment:**
```bash
python -m venv venv
```

2. **Activate the virtual environment:**
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Run migrations:**
```bash
python manage.py migrate
```

5. **Create a superuser (optional):**
```bash
python manage.py createsuperuser
```

6. **Run the development server:**
```bash
python manage.py runserver
```

7. **Open your browser and go to:**
```
http://localhost:8000
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/check-pandoc/` | GET | Check if Pandoc is installed |
| `/api/upload/` | POST | Upload files for conversion |
| `/api/batch/<batch_id>/` | GET | Get batch conversion details |
| `/api/batch/<batch_id>/download/` | GET | Download all converted files as ZIP |
| `/api/file/<file_id>/download/` | GET | Download a single converted file |
| `/api/batches/` | GET | List all conversion batches |

## API Usage Example

### Upload files using curl:
```bash
curl -X POST http://localhost:8000/api/upload/ \
  -F "files=@document1.docx" \
  -F "files=@document2.doc"
```

### Response:
```json
{
  "id": "uuid-here",
  "status": "completed",
  "files": [
    {
      "id": "file-uuid",
      "original_filename": "document1.docx",
      "markdown_filename": "document1.md",
      "status": "converted",
      "download_url": "http://localhost:8000/media/converted/..."
    }
  ]
}
```

## Project Structure

```
doctomd/
├── doctomd/                 # Project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── converter/               # Main app
│   ├── models.py           # Database models
│   ├── serializers.py      # DRF serializers
│   ├── views.py            # API views
│   ├── urls.py             # URL routing
│   ├── utils.py            # Conversion utilities
│   └── admin.py            # Admin configuration
├── templates/
│   └── converter/
│       └── index.html      # Frontend template
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
├── media/                   # Uploaded and converted files
├── manage.py
├── requirements.txt
└── README.md
```

## License

MIT License
