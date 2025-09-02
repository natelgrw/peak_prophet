import os
import shutil
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Tuple, Dict
import pandas as pd
import subprocess
import logging
import tempfile

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_input_csv(smiles_solvent_tuples: List[Tuple[str, str]], output_file: str):
    df = pd.DataFrame(smiles_solvent_tuples, columns=['smiles', 'solvent'])
    df.to_csv(output_file, index=False)
    logger.info(f"Created input CSV file: {output_file}")
    return output_file

def run_chemprop_prediction(input_file: str, output_file: str):
    checkpoint_dir = "uvvisml/models/lambda_max_abs/chemprop/combined/production/fold_0"
    if not os.path.exists(checkpoint_dir):
        logger.error(f"Checkpoint directory not found: {checkpoint_dir}")
        logger.info("Please download the models first: cd uvvisml/uvvisml && bash get_model_files.sh")
        return False

    cmd = [
        "chemprop_predict",
        "--test_path", input_file,
        "--preds_path", output_file,
        "--checkpoint_dir", checkpoint_dir,
        "--number_of_molecules", "2"
    ]

    logger.info(f"Running command: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info("Chemprop prediction completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Chemprop prediction failed: {e}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        return False

def extract_predictions(results_file: str) -> Dict[Tuple[str, str], float]:
    try:
        df = pd.read_csv(results_file)
        logger.info(f"Read results file: {results_file}")

        predictions = {}
        for _, row in df.iterrows():
            predictions[(row['smiles'], row['solvent'])] = row['peakwavs_max']
        return predictions
    except Exception as e:
        logger.error(f"Error extracting predictions: {e}")
        return {}

def predict_lambda_max(smiles_solvent_tuples: List[Tuple[str, str]]) -> Dict[Tuple[str, str], float]:
    with tempfile.TemporaryDirectory() as temp_dir:
        input_file = os.path.join(temp_dir, "input.csv")
        output_file = os.path.join(temp_dir, "results.csv")

        create_input_csv(smiles_solvent_tuples, input_file)

        if not run_chemprop_prediction(input_file, output_file):
            return {}

        return extract_predictions(output_file)

@app.get("/")
async def root():
    return {"message": "Lambda Max Prediction API is running! Use POST /predict_lambda_max with CSV file."}

@app.post("/predict_lambda_max")
async def predict_lambda_max_api(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)
    try:
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        df = pd.read_csv(temp_path)
        if 'smiles' not in df.columns or 'solvent' not in df.columns:
            raise HTTPException(status_code=400, detail="CSV must have 'smiles' and 'solvent' columns")

        smiles_solvent_list = list(df[['smiles', 'solvent']].itertuples(index=False, name=None))

        predictions = predict_lambda_max(smiles_solvent_list)
        if not predictions:
            raise HTTPException(status_code=500, detail="Prediction failed")

        results = [
            {"smiles": k[0], "solvent": k[1], "lambda_max": v}
            for k, v in predictions.items()
        ]
        return JSONResponse(content={"predictions": results})

    finally:
        file.file.close()
        shutil.rmtree(temp_dir)