#!/bin/bash

# RT Prediction API - Molgpu Server Environment Setup
# This script sets up the complete environment needed for the rtpred API

echo "Setting up RT Prediction API environment on molgpu server..."

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "Error: conda not found. Please install Anaconda/Miniconda first."
    exit 1
fi

# Check if lcgenv environment exists
if conda env list | grep -q "lcgenv"; then
    echo "lcgenv environment already exists. Updating dependencies..."
else
    echo "Creating lcgenv conda environment..."
    conda create -n lcgenv python=3.10 -y
fi

# Activate environment and install dependencies
echo "Installing dependencies in lcgenv environment..."

# Source conda and activate environment
source $(conda info --base)/etc/profile.d/conda.sh
conda activate lcgenv

# Install core dependencies
echo "Installing core dependencies..."
conda install -c conda-forge -c defaults -c pytorch -c rdkit \
    python=3.10 \
    pip \
    rdkit \
    numpy \
    pandas \
    scipy \
    matplotlib \
    scikit-learn \
    pytorch \
    torchvision \
    torchaudio \
    tqdm \
    openpyxl \
    xgboost \
    -y

# Install dependencies from lcgenv.yml
echo "Installing dependencies from lcgenv.yml..."
conda env update -f lcgenv.yml

# Install additional pip dependencies not in conda
echo "Installing additional pip dependencies..."
pip install fastapi==0.104.1 \
    uvicorn==0.24.0 \
    python-multipart==0.0.6 \
    pyppeteer==1.0.2 \
    websockets==10.4

# Verify installation
echo "Verifying installation..."
python -c "
import fastapi
import uvicorn
import pyppeteer
import chemprop
import pandas
import numpy
print('✅ All dependencies installed successfully!')
"

# Create a conda environment activation script
echo "Creating environment activation script..."
cat > activate_lcgenv.sh << 'EOF'
#!/bin/bash
# Script to activate lcgenv environment
source $(conda info --base)/etc/profile.d/conda.sh
conda activate lcgenv
echo "lcgenv environment activated!"
echo "Python path: $(which python)"
echo "Pip path: $(which pip)"
EOF

chmod +x activate_lcgenv.sh

# Update the systemd service file to use the correct conda path
echo "Updating systemd service file with correct conda paths..."

# Get the actual conda installation path
CONDA_PATH=$(conda info --base)
ENV_PATH="$CONDA_PATH/envs/lcgenv"

# Update the service file
sed -i "s|Environment=PATH=.*|Environment=PATH=$ENV_PATH/bin|g" rtpred-api.service
sed -i "s|ExecStart=.*|ExecStart=$ENV_PATH/bin/uvicorn app_puppeteer:app --host 0.0.0.0 --port 8000|g" rtpred-api.service

echo "✅ Environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Test the environment: ./activate_lcgenv.sh"
echo "2. Start the API service: ./start_rtpred_api.sh"
echo "3. Verify it's working: curl http://molgpu:8000/health"
echo ""
echo "Environment details:"
echo "- Conda path: $CONDA_PATH"
echo "- Environment path: $ENV_PATH"
echo "- Python: $ENV_PATH/bin/python"
echo "- Uvicorn: $ENV_PATH/bin/uvicorn"
