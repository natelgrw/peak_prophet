# API Integration Guide

This guide explains how to use the Lambda Max Prediction API and the Puppeteer-based Retention Time Prediction API.

## Lambda Max Prediction API

### Overview
The Lambda Max Prediction API uses the uvvisml chemprop models to predict lambda max values for molecules in specific solvents.

### Setup

1. **Activate the environment with chemprop:**
   ```bash
   conda activate uvvismlenv
   ```

2. **Install FastAPI dependencies:**
   ```bash
   pip install fastapi uvicorn python-multipart
   ```

3. **Download the uvvisml models (if not already done):**
   ```bash
   cd uvvisml/uvvisml
   bash get_model_files.sh
   ```

### Running the API

```bash
uvicorn lambda_max_api:app --host 0.0.0.0 --port 8001
```

### Usage

#### Input Format
Upload a CSV file with the following columns:
- `smiles`: SMILES strings of the compounds
- `solvent`: SMILES strings of the solvents

Example CSV:
```csv
smiles,solvent
CCN(CC)c1ccc2c(C(F)(F)F)cc(=O)oc2c1,C1CCCCC1
C[SiH](C)c1cccc2ccccc12,CCO
```

#### API Endpoints

- `GET /`: API information
- `POST /predict_lambda_max`: Upload CSV and get predictions
- `GET /health`: Health check

#### Example Response
```json
{
  "message": "Prediction completed successfully",
  "num_compounds": 2,
  "predictions": {
    "(CCN(CC)c1ccc2c(C(F)(F)F)cc(=O)oc2c1, C1CCCCC1)": 378.09,
    "(C[SiH](C)c1cccc2ccccc12, CCO)": 295.17
  }
}
```

## Retention Time Prediction API (Puppeteer)

### Overview
The Retention Time Prediction API uses Puppeteer to automate the rtpred.ca website for retention time predictions. This works on both Mac and Linux servers without requiring chromedriver.

### Setup

1. **Install puppeteer dependencies:**
   ```bash
   cd rtpred
   pip install -r requirements_puppeteer.txt
   ```

2. **Install Node.js dependencies (if needed):**
   ```bash
   # Puppeteer will automatically download Chromium
   python -c "import pyppeteer; asyncio.run(pyppeteer.launch())"
   ```

### Running the API

```bash
cd rtpred
uvicorn app_puppeteer:app --host 0.0.0.0 --port 8000
```

### Usage

#### Input Format
Upload a CSV file containing SMILES data. The exact column name may vary, but the file should contain molecular structures.

#### API Endpoints

- `GET /`: API information
- `POST /predict_retention_time`: Upload CSV and get predictions
- `GET /health`: Health check

#### Example Response
```json
{
  "message": "Prediction completed successfully",
  "num_compounds": 1,
  "predictions": [
    {
      "index": "1",
      "smiles": "CCN(CC)c1ccc2c(C(F)(F)F)cc(=O)oc2c1",
      "retention_time": "5.23"
    }
  ]
}
```

## Testing

### Lambda Max API Test
```bash
# Create a test CSV file
echo "smiles,solvent" > test_lambda_max.csv
echo "CCN(CC)c1ccc2c(C(F)(F)F)cc(=O)oc2c1,C1CCCCC1" >> test_lambda_max.csv

# Test with curl
curl -X POST "http://localhost:8001/predict_lambda_max" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@test_lambda_max.csv"
```

### Retention Time API Test
```bash
# Test with curl
curl -X POST "http://localhost:8000/predict_retention_time" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@rtpred/test_mols.csv"
```

## Standalone Scripts

### Lambda Max Prediction
```bash
# Create a simple test script
python -c "
from lambda_max_api import predict_lambda_max
tuples = [('CCN(CC)c1ccc2c(C(F)(F)F)cc(=O)oc2c1', 'C1CCCCC1')]
results = predict_lambda_max(tuples)
print(results)
"
```

### Retention Time Prediction
```bash
cd rtpred
python retention_time_pred_puppeteer.py
```

## Deployment Notes

### For Mac Development
- Both APIs work out of the box
- Puppeteer automatically handles Chromium installation

### For Linux Servers (e.g., Coley Lab molgpu)
- Puppeteer works without additional setup
- No chromedriver required
- Headless mode is automatically enabled

### Environment Variables
You can set these environment variables for customization:
- `PUPPETEER_ARGS`: Additional Chrome arguments
- `CHEMPROP_MODEL_PATH`: Custom model path for lambda max prediction

## Troubleshooting

### Lambda Max API Issues
1. **Models not found**: Run `bash get_model_files.sh` in uvvisml/uvvisml
2. **Chemprop not found**: Ensure you're in the correct conda environment
3. **Memory issues**: Reduce batch size or use smaller model

### Retention Time API Issues
1. **Puppeteer timeout**: Increase timeout values in the script
2. **Website changes**: Update selectors if rtpred.ca changes
3. **Memory issues**: Close browser properly in finally block

### Common Solutions
- Restart the API server
- Check log files for detailed error messages
- Ensure all dependencies are installed
- Verify file permissions and paths

## Integration with Peak Prophet

Both APIs can be integrated into your peak detection pipeline:

```python
# Example integration
import requests

def get_lambda_max_predictions(smiles_solvent_tuples):
    # Convert to CSV and call API
    pass

def get_retention_time_predictions(smiles_list):
    # Convert to CSV and call API
    pass
```

## Performance Considerations

- Lambda Max API: ~1-2 seconds per compound
- Retention Time API: ~5-10 seconds per compound (includes web scraping)
- Both APIs support batch processing
- Consider caching results for repeated predictions
