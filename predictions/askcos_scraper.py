import asyncio
import os
import csv
from rdkit import Chem
from rdkit.Chem import Descriptors
from playwright.async_api import async_playwright

async def scrape_askcos(reactant_smiles_list, solvent_smiles):
    """
    Scrape ASKCOS forward prediction results for given reactants and solvent.
    
    Args:
        reactant_smiles_list (list): List of reactant SMILES strings
        solvent_smiles (str): Solvent SMILES string
        output_filename (str): Name of the output CSV file (default: "forward.csv")
    
    Returns:
        str: Path to the downloaded CSV file
    """
    # Join reactant SMILES with periods
    combined_reactants = ".".join(reactant_smiles_list)
    print(f"Combined reactants: {combined_reactants}")

    async with async_playwright() as p:
        # Launch Chromium headless browser
        browser = await p.chromium.launch(headless=True)  # set True for headless
        page = await browser.new_page()

        # Navigate to ASKCOS forward prediction page
        print("Navigating to ASKCOS forward page...")
        await page.goto("https://askcos.mit.edu/forward", wait_until="networkidle")

        # Wait for the button by text content using a locator
        print("Navigating to Product Prediction tab...")
        product_button = page.locator("button", has_text="Product Prediction")
        await product_button.wait_for(timeout=20000)  # waits up to 20s
        await product_button.click()
        print("Clicked Product Prediction tab")

        # Fill Reactants
        print("Navigating to Reactants tab")
        reactant_input = page.locator("input[placeholder='SMILES'][id^='input-']")
        await reactant_input.first.fill(combined_reactants)
        print("Entered Reactants")

        # Fill Solvents
        print("Navigating to Solvents tab")
        reactant_input = page.locator("input[placeholder='SMILES'][id^='input-']")
        await reactant_input.nth(2).fill(solvent_smiles)
        print("Entered Solvents")

        # Click "Get Results" button
        print("Navigating to Results button...")
        get_results_button = page.locator("button:has-text('Get Results')")
        await get_results_button.click()
        print("Clicked Get Results button")

        await asyncio.sleep(10)

        print("Navigating to Export button...")
        get_results_button = page.locator("button:has-text('Export')")
        await get_results_button.click()
        print("Clicked Export button")

        # Set up download path to your script folder
        download_path = os.path.dirname(os.path.abspath(__file__))

        # Listen for download event
        async with page.expect_download() as download_info:
            get_results_button = page.locator("button:has-text('Save')")
            await get_results_button.click()
        download = await download_info.value

        # Save to desired location
        dest_file = os.path.join(download_path, "forward.csv")
        await download.save_as(dest_file)
        print(f"Downloaded CSV saved to {dest_file}")

        await asyncio.sleep(5)

        results = []

        for smiles in reactant_smiles_list:
            mol_reactant = Chem.MolFromSmiles(smiles)
            mw_reactant = Descriptors.ExactMolWt(mol_reactant)
            results.append({
                "smiles": smiles,
                "probability": 1,
                "mol_weight": mw_reactant,
            })

        mol_solvent = Chem.MolFromSmiles(solvent_smiles)
        mw_solvent = Descriptors.ExactMolWt(mol_solvent)
        results.append({
                "smiles": solvent_smiles,
                "probability": 1,
                "mol_weight": mw_solvent,
            })

        script_dir = os.path.dirname(os.path.abspath(__file__))
        csv_file = os.path.join(script_dir, "forward.csv")
        with open(csv_file, "r") as file:
            reader = csv.reader(file)
            for row in reader:
                results.append({
                    "smiles": row[1],
                    "probability": row[2],
                    "mol_weight": row[4],
                })

        if os.path.exists(csv_file):
            os.remove(csv_file)
            print(f"Deleted file: {csv_file}")
        else:
            print(f"File not found: {csv_file}")

        return results

async def main():
    """Example usage of the scrape_askcos function"""
    # Example reactants and solvent
    reactants = ["CC(=O)OC(C)=O"]
    solvent = "CCO"
    
    # Call the function
    results = await scrape_askcos(reactants, solvent)
    print(results)

if __name__ == "__main__":
    asyncio.run(main())