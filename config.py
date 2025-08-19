import os
from pathlib import Path

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'
    
    # File upload settings
    UPLOAD_FOLDER = Path('uploads')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size
    ALLOWED_EXTENSIONS = {'fna', 'faa', 'fasta'}
    
    # Data directories
    FNA_DIR = Path('data/fna')
    FAA_DIR = Path('data/faa') 
    HMMER_DIR = Path('data/hmmer')
    RESULTS_DIR = Path('data/results')
    PFAM_DB = Path('data/Pfam-A.hmm')
    
    # Tool paths (if not in system PATH)
    PRODIGAL_PATH = Path('/usr/bin/prodigal')  # or full path if needed
    HMMSCAN_PATH = Path('/usr/bin/hmmscan')    # or full path if needed