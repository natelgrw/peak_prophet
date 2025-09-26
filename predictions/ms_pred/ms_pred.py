#!/usr/bin/env python3
"""
Mass Spectrometry Prediction using Adduct Analysis

This module predicts mass spectrometry adducts for a list of SMILES strings.
It returns a dictionary mapping SMILES to adduct masses and their relative probabilities.
"""

from typing import List, Dict, Tuple
from rdkit import Chem
from rdkit.Chem import Descriptors

positive_adducts = [{
    "mass": 1.007276,
    "adduct": "[M+3H]3+",
    "multiplicity": 0.33,
}, {
    "mass": 8.334590,
    "adduct": "[M+2H+Na]3+",
    "multiplicity": 0.33,
}, {
    "mass": 15.662453,
    "adduct": "[M+H+2Na]3+",
    "multiplicity": 0.33,
}, {
    "mass": 22.989218,
    "adduct": "[M+3Na]3+",
    "multiplicity": 0.33,
}, {
    "mass": 1.007276,
    "adduct": "[M+2H]2+",
    "multiplicity": 0.5,
}, {
    "mass": 9.520550,
    "adduct": "[M+H+NH4]2+",
    "multiplicity": 0.5,
}, {
    "mass": 11.998247,
    "adduct": "[M+H+Na]2+",
    "multiplicity": 0.5,
}, {
    "mass": 19.985217,
    "adduct": "[M+H+K]2+",
    "multiplicity": 0.5,
}, {
    "mass": 21.520550,
    "adduct": "[M+ACN+2H]2+",
    "multiplicity": 0.5,
}, {
    "mass": 22.989218,
    "adduct": "[M+2Na]2+",
    "multiplicity": 0.5,
}, {
    "mass": 42.033823,
    "adduct": "[M+2ACN+2H]2+",
    "multiplicity": 0.5,
}, {
    "mass": 62.547097,
    "adduct": "[M+3ACN+2H]2+",
    "multiplicity": 0.5,
}, {
    "mass": 1.007276,
    "adduct": "[M+H]+",
    "multiplicity": 1,
}, {
    "mass": 18.033823,
    "adduct": "[M+NH4]+",
    "multiplicity": 1,
}, {
    "mass": 22.989218,
    "adduct": "[M+Na]+",
    "multiplicity": 1,
}, {
    "mass": 33.033489,
    "adduct": "[M+CH3OH+H]+",
    "multiplicity": 1,
}, {
    "mass": 38.963158,
    "adduct": "[M+K]+",
    "multiplicity": 1,
}, {
    "mass": 42.033823,
    "adduct": "[M+ACN+H]+",
    "multiplicity": 1,
}, {
    "mass": 44.971160,
    "adduct": "[M+2Na-H]+",
    "multiplicity": 1,
}, {
    "mass": 61.065340,
    "adduct": "[M+IsoProp+H]+",
    "multiplicity": 1,
}, {
    "mass": 64.015765,
    "adduct": "[M+ACN+Na]+",
    "multiplicity": 1,
}, {
    "mass": 76.919040,
    "adduct": "[M+2K-H]+",
    "multiplicity": 1,
}, {
    "mass": 79.021220,
    "adduct": "[M+DMSO+H]+",
    "multiplicity": 1,
}, {
    "mass": 83.060370,
    "adduct": "[M+2ACN+H]+",
    "multiplicity": 1,
}, {
    "mass": 84.055110,
    "adduct": "[M+IsoProp+Na+H]+",
    "multiplicity": 1,
}, {
    "mass": 1.007276,
    "adduct": "[2M+H]+",
    "multiplicity": 2,
}, {
    "mass": 18.033823,
    "adduct": "[2M+NH4]+",
    "multiplicity": 2,
}, {
    "mass": 22.989218,
    "adduct": "[2M+Na]+",
    "multiplicity": 2,
}, {
    "mass": 38.963158,
    "adduct": "[2M+K]+",
    "multiplicity": 2,
}, {
    "mass": 42.033823,
    "adduct": "[2M+ACN+H]+",
    "multiplicity": 2,
}, {
    "mass": 64.015765,
    "adduct": "[2M+ACN+Na]+",
    "multiplicity": 2,
}]

negative_adducts = [{
    "mass": -1.007276,
    "multiplicity": 0.333333333,
    "adduct": "[M-3H]3-",
},
    {
    "mass": -1.007276,
    "multiplicity": 0.5,
    "adduct": "[M-2H]2-",
},
    {
    "mass": -19.01839,
    "multiplicity": 1,
    "adduct": "[M-H2O-H]-",
},
    {
    "mass": -1.007276,
    "multiplicity": 1,
    "adduct": "[M-H]-",
},
    {
    "mass": 20.974666,
    "multiplicity": 1,
    "adduct": "[M+Na-2H]-",
},
    {
    "mass": 34.969402,
    "multiplicity": 1,
    "adduct": "[M+Cl]-",
},
    {
    "mass": 36.948606,
    "multiplicity": 1,
    "adduct": "[M+K-2H]-",
},
    {
    "mass": 44.998201,
    "multiplicity": 1,
    "adduct": "[M+FA-H]-",
},
    {
    "mass": 59.013851,
    "multiplicity": 1,
    "adduct": "[M+Hac-H]-",
},
    {
    "mass": 78.918885,
    "multiplicity": 1,
    "adduct": "[M+Br]-",
},
    {
    "mass": 112.985586,
    "multiplicity": 1,
    "adduct": "[M+TFA-H]-",
},
    {
    "mass": -1.007276,
    "multiplicity": 2,
    "adduct": "[2M-H]-",
},
    {
    "mass": 44.998201,
    "multiplicity": 2,
    "adduct": "[2M+FA-H]-",
},
    {
    "mass": 59.013851,
    "multiplicity": 2,
    "adduct": "[2M+Hac-H]-",
},
    {
    "mass": -1.007276,
    "multiplicity": 3,
    "adduct": "[3M-H]-",
}]


def predict_ms_adducts(smiles_list: List[str]) -> Dict[str, Dict[float, float]]:
    """
    Predict mass spectrometry adducts for a list of SMILES strings.
    
    Args:
        smiles_list: List of SMILES strings to predict adducts for
        
    Returns:
        Dictionary mapping SMILES to adduct masses and their relative probabilities
        Format: {smiles: {adduct_mass: probability}}
    """
    results = {}
    
    for smiles in smiles_list:
        try:
            # Calculate molecular weight
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                continue
                
            mol_weight = Descriptors.ExactMolWt(mol)
            
            # Calculate adduct masses and probabilities for ALL adducts
            adduct_predictions = {}
            
            # Include ALL positive adducts
            for adduct in positive_adducts:
                adduct_mass = mol_weight * adduct["multiplicity"] + adduct["mass"]
                probability = _get_adduct_probability(adduct["adduct"])
                adduct_predictions[adduct_mass] = probability
            
            # Include ALL negative adducts
            for adduct in negative_adducts:
                adduct_mass = mol_weight * adduct["multiplicity"] + adduct["mass"]
                probability = _get_adduct_probability(adduct["adduct"])
                adduct_predictions[adduct_mass] = probability
            
            results[smiles] = adduct_predictions
            
        except Exception as e:
            print(f"Error processing SMILES {smiles}: {e}")
            continue
    
    return results


def _get_adduct_probability(adduct_name: str) -> float:
    """
    Get relative probability for different adduct types based on mass spec literature.
    Probabilities are normalized relative to [M+H]+ = 1.0
    """
    # High probability adducts (very common)
    if adduct_name == "[M+H]+":
        return 1.0
    elif adduct_name == "[M-H]-":
        return 0.95
    elif adduct_name == "[M+Na]+":
        return 0.85
    elif adduct_name == "[M+NH4]+":
        return 0.75
    elif adduct_name == "[M+K]+":
        return 0.65
    elif adduct_name == "[M+Cl]-":
        return 0.70
    
    # Medium-high probability adducts
    elif adduct_name == "[M+2H]2+":
        return 0.60
    elif adduct_name == "[M-H2O-H]-":
        return 0.55
    elif adduct_name == "[M+Na-2H]-":
        return 0.50
    elif adduct_name == "[M+K-2H]-":
        return 0.45
    elif adduct_name == "[M+FA-H]-":
        return 0.40
    elif adduct_name == "[M+Hac-H]-":
        return 0.35
    elif adduct_name == "[M+CH3OH+H]+":
        return 0.30
    elif adduct_name == "[M+ACN+H]+":
        return 0.25
    elif adduct_name == "[M+ACN+Na]+":
        return 0.20
    elif adduct_name == "[M+Br]-":
        return 0.15
    elif adduct_name == "[M+TFA-H]-":
        return 0.10
    
    # Dimer adducts (less common)
    elif adduct_name == "[2M+H]+":
        return 0.08
    elif adduct_name == "[2M+NH4]+":
        return 0.06
    elif adduct_name == "[2M+Na]+":
        return 0.05
    elif adduct_name == "[2M+K]+":
        return 0.04
    elif adduct_name == "[2M+ACN+H]+":
        return 0.03
    elif adduct_name == "[2M+ACN+Na]+":
        return 0.02
    elif adduct_name == "[2M-H]-":
        return 0.07
    elif adduct_name == "[2M+FA-H]-":
        return 0.05
    elif adduct_name == "[2M+Hac-H]-":
        return 0.04
    
    # Trimer adducts (rare)
    elif adduct_name == "[3M-H]-":
        return 0.01
    
    # Triply charged adducts (rare)
    elif adduct_name == "[M+3H]3+":
        return 0.02
    elif adduct_name == "[M+2H+Na]3+":
        return 0.015
    elif adduct_name == "[M+H+2Na]3+":
        return 0.01
    elif adduct_name == "[M+3Na]3+":
        return 0.005
    elif adduct_name == "[M-3H]3-":
        return 0.01
    
    # Doubly charged adducts
    elif adduct_name == "[M+2H]2+":
        return 0.60
    elif adduct_name == "[M+H+NH4]2+":
        return 0.10
    elif adduct_name == "[M+H+Na]2+":
        return 0.08
    elif adduct_name == "[M+H+K]2+":
        return 0.06
    elif adduct_name == "[M+ACN+2H]2+":
        return 0.05
    elif adduct_name == "[M+2Na]2+":
        return 0.04
    elif adduct_name == "[M+2ACN+2H]2+":
        return 0.03
    elif adduct_name == "[M+3ACN+2H]2+":
        return 0.02
    elif adduct_name == "[M-2H]2-":
        return 0.08
    
    # Other solvent adducts
    elif adduct_name == "[M+IsoProp+H]+":
        return 0.15
    elif adduct_name == "[M+2Na-H]+":
        return 0.12
    elif adduct_name == "[M+2K-H]+":
        return 0.08
    elif adduct_name == "[M+DMSO+H]+":
        return 0.06
    elif adduct_name == "[M+2ACN+H]+":
        return 0.04
    elif adduct_name == "[M+IsoProp+Na+H]+":
        return 0.03
    
    # Additional specific cases for remaining adducts
    elif adduct_name == "[M+ACN+2H]2+":
        return 0.051  # Acetonitrile doubly charged
    elif adduct_name == "[2M+Na]+":
        return 0.052  # Dimer with sodium
    elif adduct_name == "[2M+FA-H]-":
        return 0.053  # Dimer with formic acid
    
    # Default for any missed adducts
    else:
        return 0.05


def main():
    """Example usage of the MS adduct predictor."""
    # Example SMILES list
    test_smiles = [
        "CC(=O)OC(C)=O",  # Acetic anhydride
        "CCO",            # Ethanol
        "CC(=O)O"         # Acetic acid
    ]
    
    print("Predicting MS adducts...")
    results = predict_ms_adducts(test_smiles)
    
    print("\nResults:")
    for smiles, adducts in results.items():
        print(f"\n{smiles}:")
        # Show top 5 most probable adducts
        sorted_adducts = sorted(adducts.items(), key=lambda x: x[1], reverse=True)
        for mass, prob in sorted_adducts[:10]:
            print(f"  {mass:.4f} Da (prob: {prob:.3f})")


if __name__ == "__main__":
    main()
