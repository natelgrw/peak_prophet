from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import asyncio
import tempfile
import shutil
import os
import logging
from pyppeteer import launch
import pandas as pd

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Retention Time Prediction API (Puppeteer)", version="2.0.0")

async def predict_retention_time_puppeteer(csv_file_path: str):
    """
    Use Puppeteer to predict retention times from the rtpred.ca website.
    
    Parameters
    ----------
    csv_file_path : str
        Path to the CSV file containing SMILES data
        
    Returns
    -------
    list
        List of dictionaries containing prediction results
    """
    browser = None
    try:
        # Launch browser with appropriate options for headless operation
        browser = await launch({
            'headless': True,
            'args': [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu'
            ]
        })
        
        page = await browser.newPage()
        
        # Set viewport
        await page.setViewport({'width': 1280, 'height': 720})
        
        # Navigate to the website
        logger.info("Navigating to rtpred.ca...")
        await page.goto('https://rtpred.ca/predict/', {'waitUntil': 'networkidle0'})
        
        # Wait for the page to load
        await page.waitForSelector('#selected_CM', {'timeout': 10000})
        
        # Select "CS22" from the dropdown
        logger.info("Selecting CS22 method...")
        await page.select('#selected_CM', 'CS22')
        
        # Wait for file input to be available
        await page.waitForSelector('#csv_input_predict', {'timeout': 5000})
        
        # Upload the CSV file
        logger.info(f"Uploading file: {csv_file_path}")
        file_input = await page.querySelector('#csv_input_predict')
        await file_input.uploadFile(csv_file_path)
        
        # Click the submit button
        logger.info("Submitting prediction request...")
        
        # Try multiple methods to find the submit button
        submit_button = None
        
        # Method 1: Try CSS selector
        try:
            submit_button = await page.querySelector("button[type='submit']")
        except:
            pass
            
        # Method 2: Try XPath using evaluateHandle
        if not submit_button:
            try:
                submit_button = await page.evaluateHandle('''
                    () => {
                        const xpath = "//button[normalize-space()='Submit']";
                        const result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                        return result.singleNodeValue;
                    }
                ''')
            except:
                pass
                
        # Method 3: Find by text content
        if not submit_button:
            try:
                submit_button = await page.evaluateHandle('''
                    () => {
                        const buttons = document.querySelectorAll('button');
                        for (const button of buttons) {
                            if (button.textContent.trim() === 'Submit') {
                                return button;
                            }
                        }
                        return null;
                    }
                ''')
            except:
                pass
        
        # Click the button if found
        if submit_button:
            try:
                await submit_button.click()
                logger.info("Submit button clicked successfully")
            except Exception as e:
                logger.error(f"Error clicking submit button: {e}")
                raise Exception("Submit button found but could not be clicked")
        else:
            raise Exception("Submit button not found")
        
        # Wait for results table to appear
        logger.info("Waiting for results...")
        await page.waitForSelector('#new_pred table tbody', {'timeout': 30000})
        
        # Extract results from the table
        results = await page.evaluate('''
            () => {
                const rows = document.querySelectorAll('#new_pred table tbody tr');
                const results = [];
                rows.forEach(row => {
                    const cols = row.querySelectorAll('td');
                    if (cols.length >= 3) {
                        results.push({
                            index: cols[0].textContent.trim(),
                            smiles: cols[1].textContent.trim(),
                            retention_time: cols[2].textContent.trim()
                        });
                    }
                });
                return results;
            }
        ''')
        
        logger.info(f"Extracted {len(results)} predictions")
        return results
        
    except Exception as e:
        logger.error(f"Error during prediction: {e}")
        raise e
    finally:
        if browser:
            await browser.close()

@app.get("/")
async def root():
    return {
        "message": "Retention Time Prediction API (Puppeteer) is running!",
        "usage": "Use POST /predict_retention_time with CSV file containing SMILES data."
    }

@app.post("/predict_retention_time")
async def predict_retention_time(file: UploadFile = File(...)):
    """
    Predict retention times from a CSV file using the rtpred.ca website.
    
    The CSV file should contain SMILES data in a column.
    """
    # Validate file extension
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)

    try:
        # Save uploaded file
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        logger.info(f"Processing file: {file.filename}")
        
        # Run prediction using Puppeteer
        results = await predict_retention_time_puppeteer(temp_path)
        
        return JSONResponse(content={
            "message": "Prediction completed successfully",
            "num_compounds": len(results),
            "predictions": results
        })

    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
    finally:
        file.file.close()
        shutil.rmtree(temp_dir)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "retention_time_prediction_api_puppeteer"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
