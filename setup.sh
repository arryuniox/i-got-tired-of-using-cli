#!/bin/bash

# Setup script for Bioinformatics Pipeline Webapp
# Run this script from the project root directory

echo "🧬 Setting up Bioinformatics Pipeline Webapp..."

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p templates static/css static/js data/{fna,faa,hmmer,results} uploads

# Create empty __init__.py for Python package
touch __init__.py

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Set permissions for upload directories
echo "🔐 Setting directory permissions..."
chmod 755 data uploads
chmod 755 data/*

# Check for required tools
echo "🔧 Checking for required tools..."

check_tool() {
    if command -v $1 &> /dev/null; then
        echo "✅ $1 is installed"
    else
        echo "❌ $1 is NOT installed - please install it"
        return 1
    fi
}

TOOLS_OK=true

if ! check_tool "prodigal"; then
    TOOLS_OK=false
    echo "   Install with: conda install -c bioconda prodigal"
fi

if ! check_tool "hmmscan"; then
    TOOLS_OK=false
    echo "   Install with: conda install -c bioconda hmmer"
fi

if [ "$TOOLS_OK" = true ]; then
    echo "✅ All required tools are installed!"
else
    echo "❌ Some tools are missing. Please install them before running the webapp."
fi

# Check for PFAM database
echo "🗄️  Checking PFAM database configuration..."
echo "⚠️  IMPORTANT: You need to update the PFAM_DB path in config.py"
echo "   Download PFAM database from: http://ftp.ebi.ac.uk/pub/databases/Pfam/current_release/"
echo "   Update config.py with the correct path to Pfam-A.hmm"

echo ""
echo "🚀 Setup complete! Next steps:"
echo "1. Update PFAM_DB path in config.py"
echo "2. Run the webapp: python app.py"
echo "3. Open browser to: http://localhost:5000"
echo ""
echo "📚 Make sure you have:"
echo "   - Prodigal installed and in PATH"
echo "   - HMMER installed and in PATH"
echo "   - PFAM database downloaded and path updated in config.py"