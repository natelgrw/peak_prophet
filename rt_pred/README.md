# RT Prediction API

FastAPI service for retention time prediction using rtpred.ca with Puppeteer.

## Quick Start

### Deploy on molgpu server:
```bash
chmod +x deploy_to_molgpu.sh
./deploy_to_molgpu.sh deploy
```

### Manage service:
```bash
./deploy_to_molgpu.sh start    # Start API
./deploy_to_molgpu.sh stop     # Stop API
./deploy_to_molgpu.sh restart  # Restart API
./deploy_to_molgpu.sh status   # Check status
./deploy_to_molgpu.sh logs     # View logs
```

## API Usage

### Health check:
```bash
curl http://molgpu:8000/health
```

### Predict retention time:
```bash
curl -X POST "http://molgpu:8000/predict_retention_time" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@test_mols.csv"
```

### Interactive docs:
- http://molgpu:8000/docs

## Files

- `app.py` - FastAPI application
- `rtpred.py` - Standalone testing script
- `deploy_to_molgpu.sh` - Deployment & management script
- `setup_molgpu_env.sh` - Conda environment setup
- `lcgenv.yml` - Conda environment dependencies
- `test_mols.csv` - Test data
