#!/usr/bin/env python3
"""
Lambda Max Predictor

This script takes a list of (smiles, solvent) tuples and returns a dictionary
with predicted lambda max values using the uvvisml chemprop models.

IMPORTANT: Run this script from an activated conda environment where chemprop is installed.
For example:
    conda activate uvvismlenv
    python lambda_max_pred.py

Usage:
    python lambda_max_pred.py
"""

import os
import sys
import pandas as pd
import subprocess
import tempfile
from typing import List, Tuple, Dict
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_input_csv(smiles_solvent_tuples: List[Tuple[str, str]], output_file: str = "input.csv"):
    """Create CSV file from (SMILES, solvent) pairs for chemprop input."""
    df = pd.DataFrame(smiles_solvent_tuples, columns=['smiles', 'solvent'])
    df.to_csv(output_file, index=False)
    logger.info(f"Created input CSV: {output_file} ({df.shape[0]} rows)")
    return output_file

def run_chemprop_prediction(input_file: str = "input.csv", output_file: str = "results.csv"):
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
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    checkpoint_dir = os.path.join(script_dir, "uvvisml")
    
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

def run_chemprop_prediction_in_conda_env(input_file: str = "input.csv", output_file: str = "results.csv", conda_env: str = "uvvismlenv") -> bool:
    """Run chemprop prediction in specified conda environment."""
    # Find model directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    checkpoint_dir = os.path.join(script_dir, "uvvisml")
    
    if not os.path.exists(checkpoint_dir):
        logger.error(f"Model directory not found: {checkpoint_dir}")
        return False

    # Build command
    cmd = [
        "conda", "run", "-n", conda_env,
        "chemprop_predict",
        "--test_path", input_file,
        "--preds_path", output_file,
        "--checkpoint_dir", checkpoint_dir,
        "--number_of_molecules", "2",
    ]

    logger.info(f"Running chemprop in {conda_env}...")
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info("Prediction completed")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Prediction failed: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error: {e}")
        return False

def extract_predictions(results_file: str) -> Dict[Tuple[str, str], float]:
    """Extract lambda max predictions from chemprop results CSV."""
    try:
        df = pd.read_csv(results_file)
        predictions = {}
        
        for _, row in df.iterrows():
            smiles = row['smiles']
            solvent = row['solvent']
            lambda_max = row['peakwavs_max']
            predictions[(smiles, solvent)] = lambda_max
        
        logger.info(f"Extracted {len(predictions)} predictions")
        return predictions
        
    except Exception as e:
        logger.error(f"Error reading results: {e}")
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

def predict_lambda_max_in_conda_env(smiles_solvent_tuples: List[Tuple[str, str]], conda_env: str = "uvvismlenv") -> Dict[Tuple[str, str], float]:
    """
    Predict lambda max values for molecules using chemprop models.
    
    Takes a list of (SMILES, solvent) pairs and returns predicted lambda max values.
    Runs in the specified conda environment to avoid dependency conflicts.
    """
    logger.info(f"Predicting lambda max for {len(smiles_solvent_tuples)} molecules")

    # Create input CSV file
    input_file = create_input_csv(smiles_solvent_tuples)
    output_file = "results.csv"

    # Run chemprop prediction
    if not run_chemprop_prediction_in_conda_env(input_file, output_file, conda_env=conda_env):
        logger.error("Chemprop prediction failed")
        return {}

    # Extract results
    predictions = extract_predictions(output_file)

    # Clean up files
    for file_path in [input_file, output_file]:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

    return predictions

def main():
    """Example usage of the lambda max predictor."""
    # Example (smiles, solvent) tuples
    test_tuples = [
        ("CN1CC[C@]23[C@@H]4[C@H]1CC5=C2C(=C(C=C5)OC)O[C@H]3[C@H](C=C4)O", "O")
    ]

    print("Testing lambda max prediction...")
    print(f"Input: {test_tuples}")

    # Run prediction
    results = predict_lambda_max(test_tuples)

    print("\nResults:")
    for (smiles, solvent), lambda_max in results.items():
        print(f"({smiles}, {solvent}): {lambda_max:.2f} nm")

if __name__ == "__main__":
    main() 