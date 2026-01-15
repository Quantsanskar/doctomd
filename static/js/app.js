// DocToMD - Frontend JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const fileList = document.getElementById('file-list');
    const filesUl = document.getElementById('files-ul');
    const fileCount = document.getElementById('file-count');
    const clearBtn = document.getElementById('clear-btn');
    const convertBtn = document.getElementById('convert-btn');
    const progressSection = document.getElementById('progress-section');
    const progressFill = document.getElementById('progress-fill');
    const resultsSection = document.getElementById('results-section');
    const resultsList = document.getElementById('results-list');
    const downloadAllBtn = document.getElementById('download-all-btn');
    const newConversionBtn = document.getElementById('new-conversion-btn');
    const errorSection = document.getElementById('error-section');
    const errorMessage = document.getElementById('error-message');
    const retryBtn = document.getElementById('retry-btn');
    const pandocStatus = document.getElementById('pandoc-status');
    const uploadSection = document.querySelector('.upload-section');

    // State
    let selectedFiles = [];
    let currentBatchId = null;
    const MAX_FILES = 10;

    // Check Pandoc status on load
    checkPandocStatus();

    // Event Listeners
    dropZone.addEventListener('click', () => fileInput.click());
    
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        handleFiles(e.dataTransfer.files);
    });

    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });

    clearBtn.addEventListener('click', clearFiles);
    convertBtn.addEventListener('click', startConversion);
    newConversionBtn.addEventListener('click', resetToStart);
    retryBtn.addEventListener('click', resetToStart);
    downloadAllBtn.addEventListener('click', downloadAllFiles);

    // Functions
    async function checkPandocStatus() {
        try {
            const response = await fetch('/api/check-pandoc/');
            const data = await response.json();
            
            if (!data.pandoc_installed) {
                pandocStatus.classList.remove('hidden');
                pandocStatus.classList.add('warning');
                pandocStatus.querySelector('.status-message').textContent = data.message;
                convertBtn.disabled = true;
            }
        } catch (error) {
            console.error('Failed to check Pandoc status:', error);
        }
    }

    function handleFiles(files) {
        const fileArray = Array.from(files);
        
        // Filter valid files
        const validFiles = fileArray.filter(file => {
            const ext = file.name.toLowerCase().split('.').pop();
            return ext === 'doc' || ext === 'docx';
        });

        if (validFiles.length !== fileArray.length) {
            showError('Some files were skipped. Only .doc and .docx files are allowed.');
        }

        // Check max files limit
        const remainingSlots = MAX_FILES - selectedFiles.length;
        const filesToAdd = validFiles.slice(0, remainingSlots);

        if (validFiles.length > remainingSlots) {
            showError(`Maximum ${MAX_FILES} files allowed. Only ${filesToAdd.length} files were added.`);
        }

        // Add files to selection
        selectedFiles = [...selectedFiles, ...filesToAdd];
        updateFileList();
    }

    function updateFileList() {
        filesUl.innerHTML = '';
        fileCount.textContent = selectedFiles.length;

        if (selectedFiles.length === 0) {
            fileList.classList.add('hidden');
            return;
        }

        fileList.classList.remove('hidden');

        selectedFiles.forEach((file, index) => {
            const li = document.createElement('li');
            const ext = file.name.toLowerCase().split('.').pop();
            const icon = ext === 'doc' ? '📄' : '📝';
            
            li.innerHTML = `
                <div class="file-info">
                    <span class="file-icon">${icon}</span>
                    <div>
                        <div class="file-name">${file.name}</div>
                        <div class="file-size">${formatFileSize(file.size)}</div>
                    </div>
                </div>
                <button class="remove-btn" data-index="${index}" title="Remove">✕</button>
            `;
            filesUl.appendChild(li);
        });

        // Add remove button listeners
        document.querySelectorAll('.remove-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const index = parseInt(e.target.dataset.index);
                selectedFiles.splice(index, 1);
                updateFileList();
            });
        });
    }

    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }

    function clearFiles() {
        selectedFiles = [];
        fileInput.value = '';
        updateFileList();
    }

    async function startConversion() {
        if (selectedFiles.length === 0) {
            showError('Please select at least one file.');
            return;
        }

        // Show progress section
        uploadSection.classList.add('hidden');
        progressSection.classList.remove('hidden');
        errorSection.classList.add('hidden');
        resultsSection.classList.add('hidden');
        progressFill.style.width = '0%';

        // Create FormData
        const formData = new FormData();
        selectedFiles.forEach(file => {
            formData.append('files', file);
        });

        // Animate progress
        let progress = 0;
        const progressInterval = setInterval(() => {
            if (progress < 90) {
                progress += Math.random() * 10;
                progressFill.style.width = Math.min(progress, 90) + '%';
            }
        }, 300);

        try {
            const response = await fetch('/api/upload/', {
                method: 'POST',
                body: formData
            });

            clearInterval(progressInterval);
            progressFill.style.width = '100%';

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || errorData.files?.[0] || 'Upload failed');
            }

            const data = await response.json();
            currentBatchId = data.id;

            // Show results
            setTimeout(() => {
                showResults(data);
            }, 500);

        } catch (error) {
            clearInterval(progressInterval);
            progressSection.classList.add('hidden');
            showErrorSection(error.message);
        }
    }

    function showResults(data) {
        progressSection.classList.add('hidden');
        resultsSection.classList.remove('hidden');

        resultsList.innerHTML = '';

        data.files.forEach(file => {
            const div = document.createElement('div');
            div.className = `result-item ${file.status === 'converted' ? 'success' : 'failed'}`;

            if (file.status === 'converted') {
                div.innerHTML = `
                    <div class="result-info">
                        <span class="result-status">✅</span>
                        <span class="result-name">${file.original_filename} → ${file.markdown_filename}</span>
                    </div>
                    <a href="${file.download_url}" class="result-download" download>Download</a>
                `;
            } else {
                div.innerHTML = `
                    <div class="result-info">
                        <span class="result-status">❌</span>
                        <span class="result-name">${file.original_filename}</span>
                    </div>
                    <span style="color: var(--error-color); font-size: 0.875rem;">${file.error_message || 'Conversion failed'}</span>
                `;
            }

            resultsList.appendChild(div);
        });
    }

    function downloadAllFiles() {
        if (currentBatchId) {
            window.location.href = `/api/batch/${currentBatchId}/download/`;
        }
    }

    function showError(message) {
        // Temporary error notification
        const notification = document.createElement('div');
        notification.className = 'status-banner warning';
        notification.style.position = 'fixed';
        notification.style.top = '1rem';
        notification.style.right = '1rem';
        notification.style.left = '1rem';
        notification.style.maxWidth = '400px';
        notification.style.marginLeft = 'auto';
        notification.style.zIndex = '1000';
        notification.innerHTML = `<span class="status-icon">⚠️</span><span>${message}</span>`;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    function showErrorSection(message) {
        errorSection.classList.remove('hidden');
        errorMessage.textContent = message;
    }

    function resetToStart() {
        selectedFiles = [];
        fileInput.value = '';
        currentBatchId = null;
        
        progressSection.classList.add('hidden');
        resultsSection.classList.add('hidden');
        errorSection.classList.add('hidden');
        uploadSection.classList.remove('hidden');
        fileList.classList.add('hidden');
        
        updateFileList();
    }
});
