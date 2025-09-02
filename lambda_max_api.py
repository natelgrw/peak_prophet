#!/usr/bin/env python3
"""
Lambda Max Prediction API

This FastAPI application provides an endpoint for predicting lambda max values
from a CSV file containing SMILES and solvent information.

IMPORTANT: Run this API from an activated conda environment where chemprop is installed.
For example:
    conda activate uvvismlenv
    uvicorn lambda_max_api:app --host 0.0.0.0 --port 8001
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import subprocess
import tempfile
import os
import logging
from typing import List, Tuple, Dict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Lambda Max Prediction API", version="1.0.0")

def create_input_csv(smiles_solvent_tuples: List[Tuple[str, str]], output_file: str = "input.csv"):
    """
    Create a CSV file from a list of (smiles, solvent) tuples.
    
    Parameters
    ----------
    smiles_solvent_tuples : List[Tuple[str, str]]
        List of (smiles, solvent) tuples
    output_file : str
        Path to the output CSV file
        
    Returns
    -------
    str
        Path to the created CSV file
    """
    # Create DataFrame
    df = pd.DataFrame(smiles_solvent_tuples, columns=['smiles', 'solvent'])
    
    # Write to CSV
    df.to_csv(output_file, index=False)
    logger.info(f"Created input CSV file: {output_file}")
    logger.info(f"Input data shape: {df.shape}")
    
    return output_file

def run_chemprop_prediction(input_file: str, output_file: str = "results.csv"):
    """
    Run chemprop prediction using the uvvisml model.
    
    Parameters
    ----------
    input_file : str
        Path to the input CSV file
    output_file : str
        Path to the output CSV file
        
    Returns
    -------
    bool
        True if prediction was successful, False otherwise
    """
    # Define the checkpoint directory
    checkpoint_dir = "uvvisml/uvvisml/models/lambda_max_abs/chemprop/combined/production/fold_0"
    
    # Check if checkpoint directory exists
    if not os.path.exists(checkpoint_dir):
        logger.error(f"Checkpoint directory not found: {checkpoint_dir}")
        logger.info("Please download the models first: cd uvvisml/uvvisml && bash get_model_files.sh")
        return False
    
    # Build the chemprop_predict command
    cmd = [
        "chemprop_predict",
        "--test_path", input_file,
        "--preds_path", output_file,
        "--checkpoint_dir", checkpoint_dir,
        "--number_of_molecules", "2"
    ]
    
    logger.info(f"Running command: {' '.join(cmd)}")
    
    try:
        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info("Chemprop prediction completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Chemprop prediction failed: {e}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during prediction: {e}")
        return False

def extract_predictions(results_file: str) -> Dict[Tuple[str, str], float]:
    """
    Extract predictions from the results CSV file.
    
    Parameters
    ----------
    results_file : str
        Path to the results CSV file
        
    Returns
    -------
    Dict[Tuple[str, str], float]
        Dictionary mapping (smiles, solvent) tuples to lambda max values
    """
    try:
        # Read the results CSV
        df = pd.read_csv(results_file)
        logger.info(f"Read results file: {results_file}")
        logger.info(f"Results shape: {df.shape}")
        
        # Create the dictionary
        predictions = {}
        for _, row in df.iterrows():
            smiles = row['smiles']
            solvent = row['solvent']
            lambda_max = row['peakwavs_max']
            
            predictions[(smiles, solvent)] = lambda_max
        
        logger.info(f"Extracted {len(predictions)} predictions")
        return predictions
        
    except Exception as e:
        logger.error(f"Error extracting predictions: {e}")
        return {}

def predict_lambda_max(smiles_solvent_tuples: List[Tuple[str, str]]) -> Dict[Tuple[str, str], float]:
    """
    Main function to predict lambda max values for a list of (smiles, solvent) tuples.
    
    Parameters
    ----------
    smiles_solvent_tuples : List[Tuple[str, str]]
        List of (smiles, solvent) tuples to predict for
        
    Returns
    -------
    Dict[Tuple[str, str], float]
        Dictionary mapping (smiles, solvent) tuples to predicted lambda max values
    """
    logger.info(f"Starting lambda max prediction for {len(smiles_solvent_tuples)} compounds")
    
    # Create input CSV file
    input_file = create_input_csv(smiles_solvent_tuples)
    
    # Run chemprop prediction
    output_file = "results.csv"
    if not run_chemprop_prediction(input_file, output_file):
        logger.error("Prediction failed")
        return {}
    
    # Extract predictions
    predictions = extract_predictions(output_file)
    
    # Clean up temporary files
    try:
        if os.path.exists(input_file):
            os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)
        logger.info("Cleaned up temporary files")
    except Exception as e:
        logger.warning(f"Could not clean up temporary files: {e}")
    
    return predictions

@app.get("/")
async def root():
    return {
        "message": "Lambda Max Prediction API is running!",
        "usage": "Use POST /predict_lambda_max with CSV file containing 'smiles' and 'solvent' columns."
    }

@app.post("/predict_lambda_max")
async def predict_lambda_max_endpoint(file: UploadFile = File(...)):
    """
    Predict lambda max values from a CSV file.
    
    The CSV file should have two columns:
    - smiles: SMILES strings of the compounds
    - solvent: SMILES strings of the solvents
    
    Returns a dictionary mapping (smiles, solvent) tuples to predicted lambda max values.
    """
    # Validate file extension
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    try:
        # Read the uploaded CSV file
        df = pd.read_csv(file.file)
        
        # Validate required columns
        required_columns = ['smiles', 'solvent']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {missing_columns}. Required columns: {required_columns}"
            )
        
        # Convert DataFrame to list of tuples
        smiles_solvent_tuples = list(zip(df['smiles'], df['solvent']))
        
        logger.info(f"Processing {len(smiles_solvent_tuples)} compounds from uploaded file")
        
        # Run prediction
        predictions = predict_lambda_max(smiles_solvent_tuples)
        
        if not predictions:
            raise HTTPException(status_code=500, detail="Prediction failed. Check server logs for details.")
        
        # Convert tuple keys to strings for JSON serialization
        serializable_predictions = {}
        for (smiles, solvent), lambda_max in predictions.items():
            key = f"({smiles}, {solvent})"
            serializable_predictions[key] = lambda_max
        
        return JSONResponse(content={
            "message": "Prediction completed successfully",
            "num_compounds": len(predictions),
            "predictions": serializable_predictions
        })
        
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    except pd.errors.ParserError:
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid CSV.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        file.file.close()

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "lambda_max_prediction_api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
