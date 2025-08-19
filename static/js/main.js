// Main JavaScript for bioinformatics pipeline webapp

let progressInterval;
let progressModal;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap modal
    const progressModalElement = document.getElementById('progressModal');
    if (progressModalElement) {
        progressModal = new bootstrap.Modal(progressModalElement, {
            backdrop: 'static',
            keyboard: false
        });
    }
    
    // Add file input validation
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.addEventListener('change', validateFiles);
    }
    
    // Add form validation for file upload
    const uploadForm = document.querySelector('form[action*="upload"]');
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            if (!validateFiles()) {
                e.preventDefault();
            }
        });
    }
});

function startAnalysis() {
    const analyzeBtn = document.getElementById('analyzeBtn');
    
    // Disable the button to prevent multiple submissions
    analyzeBtn.disabled = true;
    analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Starting...';
    
    fetch('/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showAlert('danger', data.error);
            resetAnalyzeButton();
        } else {
            // Show progress modal and start monitoring
            showProgressModal();
            startProgressMonitoring();
        }
    })
    .catch(error => {
        console.error('Error starting analysis:', error);
        showAlert('danger', 'Error starting analysis. Please try again.');
        resetAnalyzeButton();
    });
}

function showProgressModal() {
    if (progressModal) {
        progressModal.show();
        
        // Reset progress elements
        updateProgress(0, 'Starting', 'Initializing analysis...');
        document.getElementById('progressComplete').classList.add('d-none');
    }
}

function startProgressMonitoring() {
    progressInterval = setInterval(checkProgress, 1000); // Check every second
}

function checkProgress() {
    fetch('/status')
    .then(response => response.json())
    .then(data => {
        updateProgress(data.progress, data.current_step, data.message);
        
        if (!data.running) {
            clearInterval(progressInterval);
            
            if (data.error) {
                showProgressError(data.error);
            } else {
                showProgressComplete();
            }
            
            resetAnalyzeButton();
        }
    })
    .catch(error => {
        console.error('Error checking progress:', error);
        clearInterval(progressInterval);
        showProgressError('Connection error while monitoring progress');
        resetAnalyzeButton();
    });
}

function updateProgress(progress, step, message) {
    const progressBar = document.getElementById('progressBar');
    const progressStep = document.getElementById('progressStep');
    const progressMessage = document.getElementById('progressMessage');
    
    if (progressBar) {
        progressBar.style.width = progress + '%';
        progressBar.setAttribute('aria-valuenow', progress);
        progressBar.textContent = Math.round(progress) + '%';
    }
    
    if (progressStep) {
        progressStep.textContent = formatStepName(step);
    }
    
    if (progressMessage) {
        progressMessage.textContent = message;
    }
}

function formatStepName(step) {
    const stepNames = {
        'translation': 'Step 1: FNA to FAA Translation',
        'hmmer': 'Step 2: HMMER Database Search',
        'results': 'Step 3: Processing Results',
        'counting': 'Step 4: Counting PFAM Hits',
        'complete': 'Analysis Complete!'
    };
    
    return stepNames[step] || step;
}

function showProgressComplete() {
    const progressBar = document.getElementById('progressBar');
    const progressStep = document.getElementById('progressStep');
    const progressMessage = document.getElementById('progressMessage');
    const completeSection = document.getElementById('progressComplete');
    
    if (progressBar) {
        progressBar.classList.remove('progress-bar-striped', 'progress-bar-animated');
        progressBar.classList.add('bg-success');
    }
    
    if (progressStep) {
        progressStep.textContent = 'Analysis Complete!';
        progressStep.className = 'fw-bold mb-2 text-success';
    }
    
    if (progressMessage) {
        progressMessage.textContent = 'All files have been processed successfully.';
    }
    
    if (completeSection) {
        completeSection.classList.remove('d-none');
    }
    
    // Auto-redirect to results after a few seconds
    setTimeout(() => {
        if (progressModal) {
            progressModal.hide();
        }
        window.location.href = '/results';
    }, 3000);
}

function showProgressError(errorMessage) {
    const progressBar = document.getElementById('progressBar');
    const progressStep = document.getElementById('progressStep');
    const progressMessage = document.getElementById('progressMessage');
    
    if (progressBar) {
        progressBar.classList.remove('progress-bar-striped', 'progress-bar-animated');
        progressBar.classList.add('bg-danger');
    }
    
    if (progressStep) {
        progressStep.textContent = 'Analysis Failed';
        progressStep.className = 'fw-bold mb-2 text-danger';
    }
    
    if (progressMessage) {
        progressMessage.textContent = errorMessage;
    }
    
    // Show close button after error
    setTimeout(() => {
        if (progressModal) {
            progressModal.hide();
        }
        showAlert('danger', 'Analysis failed: ' + errorMessage);
    }, 2000);
}

function resetAnalyzeButton() {
    const analyzeBtn = document.getElementById('analyzeBtn');
    if (analyzeBtn) {
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = '<i class="fas fa-play me-2"></i>Start Analysis';
    }
}

function validateFiles() {
    const fileInput = document.getElementById('fileInput');
    if (!fileInput || !fileInput.files) return false;
    
    const files = fileInput.files;
    const allowedExtensions = ['.fna', '.fa', '.fasta'];
    const maxFileSize = 100 * 1024 * 1024; // 100MB
    
    if (files.length === 0) {
        showAlert('warning', 'Please select at least one file.');
        return false;
    }
    
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const fileName = file.name.toLowerCase();
        const fileSize = file.size;
        
        // Check file extension
        const hasValidExtension = allowedExtensions.some(ext => fileName.endsWith(ext));
        if (!hasValidExtension) {
            showAlert('warning', `Invalid file type: ${file.name}. Allowed types: ${allowedExtensions.join(', ')}`);
            return false;
        }
        
        // Check file size
        if (fileSize > maxFileSize) {
            showAlert('warning', `File too large: ${file.name}. Maximum size: 100MB`);
            return false;
        }
        
        // Check if file is empty
        if (fileSize === 0) {
            showAlert('warning', `Empty file detected: ${file.name}`);
            return false;
        }
    }
    
    return true;
}

function showAlert(type, message) {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at the top of the container
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv && alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

// File input styling and feedback
document.addEventListener('change', function(e) {
    if (e.target && e.target.id === 'fileInput') {
        const fileCount = e.target.files.length;
        const helpText = e.target.nextElementSibling;
        
        if (fileCount > 0) {
            helpText.textContent = `${fileCount} file(s) selected`;
            helpText.classList.add('text-success');
        } else {
            helpText.textContent = 'Supported formats: .fna, .fa, .fasta';
            helpText.classList.remove('text-success');
        }
    }
});

// Handle modal close events
document.addEventListener('hidden.bs.modal', function(e) {
    if (e.target && e.target.id === 'progressModal') {
        if (progressInterval) {
            clearInterval(progressInterval);
        }
        resetAnalyzeButton();
    }
});

// Add smooth scrolling for any anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth'
            });
        }
    });
});