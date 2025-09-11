#!/usr/bin/env python3
"""
Retention Time Prediction using Puppeteer

This script uses Puppeteer to automate the rtpred.ca website for retention time prediction.
It works on both Mac and Linux servers without requiring chromedriver.

Usage:
    python retention_time_pred_puppeteer.py
"""

import asyncio
import os
import logging
import tempfile
from typing import List
from pyppeteer import launch

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        # These options work on both Mac and Linux servers
        browser = await launch({
            'headless': True,
            'args': [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
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

def _write_smiles_to_temp_csv(smiles_list: List[str]) -> str:
    """
    Write a list of SMILES to a temporary CSV file with one SMILES per line and no header.

    Parameters
    ----------
    smiles_list : List[str]
        List of SMILES strings

    Returns
    -------
    str
        Path to the created temporary CSV file
    """
    # Create a NamedTemporaryFile that persists after closing so the browser can access it
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    try:
        for smiles in smiles_list:
            temp_file.write(f"{smiles}\n")
        temp_file.flush()
        return temp_file.name
    finally:
        temp_file.close()

async def predict_retention_time_from_smiles(smiles_list: List[str]):
    """
    Predict retention times given a list of SMILES. This creates a temporary CSV
    with one SMILES per line (no header) and submits it to rtpred.ca.

    Parameters
    ----------
    smiles_list : List[str]
        List of SMILES strings

    Returns
    -------
    list
        List of dictionaries containing prediction results
    """
    csv_path = _write_smiles_to_temp_csv(smiles_list)
    try:
        return await predict_retention_time_puppeteer(csv_path)
    finally:
        # Clean up the temporary CSV file
        try:
            os.unlink(csv_path)
        except OSError:
            pass

async def main():
    """Main function to test the retention time prediction."""
    # Example SMILES list (update as needed)
    smiles_list = ["c1cc(ccc1N=Nc2ccc(cc2)C#N)N(CCO)CCO"]

    try:
        results = await predict_retention_time_from_smiles(smiles_list)
        
        print("\nResults:")
        for result in results:
            print(f"Index: {result['index']}, SMILES: {result['smiles']}, Retention Time: {result['retention_time']}")
            
    except Exception as e:
        logger.error(f"Prediction failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
