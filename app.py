from flask import Flask, request, render_template, send_file, flash, redirect, url_for, jsonify
import os
import zipfile
from pathlib import Path
from werkzeug.utils import secure_filename
import pandas as pd
import threading
import time
from backend import translate_fna_to_faa, run_hmmer_search, read_results, count_pfam_hits
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Global variable to track job status
job_status = {
    'running': False,
    'current_step': '',
    'progress': 0,
    'message': '',
    'error': None
}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def reset_job_status():
    global job_status
    job_status = {
        'running': False,
        'current_step': '',
        'progress': 0,
        'message': '',
        'error': None
    }

def update_job_status(step, progress, message):
    global job_status
    job_status['current_step'] = step
    job_status['progress'] = progress
    job_status['message'] = message

def run_analysis_pipeline():
    global job_status
    try:
        job_status['running'] = True
        
        # Step 1: Translation
        update_job_status('translation', 25, 'Translating FNA files to FAA...')
        translate_fna_to_faa(app.config['FNA_DIR'], app.config['FAA_DIR'])
        time.sleep(1)  # Brief pause for UI feedback
        
        # Step 2: HMMER search
        update_job_status('hmmer', 50, 'Running HMMER searches...')
        run_hmmer_search(app.config['FAA_DIR'], app.config['HMMER_DIR'], app.config['PFAM_DB'])
        time.sleep(1)
        
        # Step 3: Process results
        update_job_status('results', 75, 'Processing results...')
        read_results(app.config['HMMER_DIR'])
        
        # Step 4: Count PFAM hits
        update_job_status('counting', 90, 'Counting PFAM hits...')
        # Find the first .tbl file for counting
        tbl_files = list(app.config['HMMER_DIR'].glob("*.tbl"))
        if tbl_files:
            count_pfam_hits(str(tbl_files[0]))
        
        update_job_status('complete', 100, 'Analysis complete!')
        time.sleep(2)
        
    except Exception as e:
        job_status['error'] = str(e)
        job_status['message'] = f'Error: {str(e)}'
    finally:
        job_status['running'] = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files[]' not in request.files:
        flash('No files selected')
        return redirect(request.url)
    
    files = request.files.getlist('files[]')
    uploaded_files = []
    
    for file in files:
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = app.config['FNA_DIR'] / filename
            file.save(str(file_path))
            uploaded_files.append(filename)
    
    if uploaded_files:
        flash(f'Successfully uploaded {len(uploaded_files)} files')
        return redirect(url_for('index'))
    else:
        flash('No valid files uploaded')
        return redirect(url_for('index'))

@app.route('/analyze', methods=['POST'])
def analyze():
    global job_status
    
    if job_status['running']:
        return jsonify({'error': 'Analysis already running'}), 400
    
    # Check if we have FNA files
    fna_files = list(app.config['FNA_DIR'].glob("*.fna"))
    if not fna_files:
        return jsonify({'error': 'No FNA files found. Please upload files first.'}), 400
    
    # Check if PFAM database exists
    if not app.config['PFAM_DB'].exists():
        return jsonify({'error': f'PFAM database not found at {app.config["PFAM_DB"]}'}), 400
    
    reset_job_status()
    
    # Start analysis in background thread
    analysis_thread = threading.Thread(target=run_analysis_pipeline)
    analysis_thread.daemon = True
    analysis_thread.start()
    
    return jsonify({'message': 'Analysis started', 'status': 'started'})

@app.route('/status')
def get_status():
    return jsonify(job_status)

@app.route('/results')
def results():
    results_file = Path("hmmer_results.xlsx")
    counts_file = Path("pfam_counts.xlsx")
    
    results_exist = results_file.exists()
    counts_exist = counts_file.exists()
    
    # Get list of generated files
    hmmer_files = list(app.config['HMMER_DIR'].glob("*.tbl"))
    faa_files = list(app.config['FAA_DIR'].glob("*.faa"))
    
    return render_template('results.html', 
                         results_exist=results_exist,
                         counts_exist=counts_exist,
                         hmmer_files=hmmer_files,
                         faa_files=faa_files)

@app.route('/download/<filename>')
def download_file(filename):
    file_path = Path(filename)
    if file_path.exists():
        return send_file(str(file_path), as_attachment=True)
    else:
        flash('File not found')
        return redirect(url_for('results'))

@app.route('/download_all')
def download_all():
    # Create a zip file with all results
    zip_path = Path("all_results.zip")
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        # Add Excel files
        for file in ["hmmer_results.xlsx", "pfam_counts.xlsx"]:
            if Path(file).exists():
                zipf.write(file)
        
        # Add HMMER output files
        for file in app.config['HMMER_DIR'].glob("*.tbl"):
            zipf.write(file, f"hmmer_output/{file.name}")
        
        # Add FAA files
        for file in app.config['FAA_DIR'].glob("*.faa"):
            zipf.write(file, f"faa_files/{file.name}")
    
    return send_file(str(zip_path), as_attachment=True)

@app.route('/clear_data', methods=['POST'])
def clear_data():
    try:
        # Clear directories
        for directory in [app.config['FNA_DIR'], app.config['FAA_DIR'], app.config['HMMER_DIR']]:
            for file in directory.glob("*"):
                if file.is_file():
                    file.unlink()
        
        # Clear result files
        for file in ["hmmer_results.xlsx", "pfam_counts.xlsx", "all_results.zip"]:
            file_path = Path(file)
            if file_path.exists():
                file_path.unlink()
        
        reset_job_status()
        flash('All data cleared successfully')
        
    except Exception as e:
        flash(f'Error clearing data: {str(e)}')
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Ensure directories exist
    for directory in [app.config['FNA_DIR'], app.config['FAA_DIR'], 
                     app.config['HMMER_DIR'], app.config['UPLOAD_FOLDER']]:
        directory.mkdir(parents=True, exist_ok=True)
    
    app.run(debug=True, host='127.0.0.1', port=8080)