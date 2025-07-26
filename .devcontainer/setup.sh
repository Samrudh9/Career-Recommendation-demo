#!/bin/bash

set -e

echo "🔧 Setting up Career App environment..."

# System packages if needed
apt-get update && apt-get install -y libpoppler-cpp-dev

# Python dependencies
pip install --upgrade pip
pip install -r requirements.txt || {
    echo "Fallback: manual pip install"
    pip install numpy pandas scikit-learn flask spacy pdfplumber==0.10.2 python-dotenv
}

# Language models
python -m spacy download en_core_web_sm

echo "✅ Setup complete!"
