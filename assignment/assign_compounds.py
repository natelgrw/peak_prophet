"""
assign_compounds.py

Uses a compound matching score to assign compound_id
specifications to each peak in an LC-MS summary dictionary.

In this way, the LC-MS summary dictionary can be utilized to accurately
maximize compound separation. The distance between peaks classified with 
the same compound_id will be minimized, and the distance between peaks
classified with different compound_id will be maximized. Peaks that do not
have a compound_id (compound_id = None) will be ignored.

LC-MS Complete Summary Dictionary Example:

Summary = {
    "reaction": "Fischer esterification - methyl salicylate synthesis",
    "reactants": [
        "O=C(O)c1ccccc1O",
        "CO"
    ],
    "solvents": [
        "CCO",              
        "CN(C)C=O"         
    ],
    "lambda_range": (220, 400),
    "baseline_method": "asls",
    "time_range": (0.0, 12.0),
    "min_distance": 0.45,
    "peaks": [
        {
            "time_range": (2.1, 2.7),
            "all_maxima": [2.4],
            "area": 13450.7,
            "lambda_max": [272],
            "mass_prediction": (149.3, 154.4),
            "compound_id": 1,
            "compound_smiles": "O=C(O)c1ccccc1O"
        },
        {
            "time_range": (3.4, 3.9),
            "all_maxima": [3.6],
            "area": 18500.2,
            "lambda_max": [258],
            "mass": (135.8, 136.8),
            "compound_id": 2,
            "compound_smiles": "CO"
        },
        {
            "time_range": (5.2, 5.9),
            "all_maxima": [5.6],
            "area": 24310.9,
            "lambda_max": [280],
            "mass": (164.8, 166.4),
            "compound_id": 3,
            "compound_smiles": "COC(=O)c1ccccc1O"
        },
        {
            "time_range": (6.1, 6.5),
            "all_maxima": [6.3],
            "area": 3200.4,
            "lambda_max": [242],
            "mass": (150.1, 155.8),
            "compound_id": None,
            "compound_smiles": None
        }
    ]
}

Author: natelgrw
Created: 06/01/2025
Last Edited: 6/01/2025
"""

from __future__ import annotations

from typing import List, Dict, Tuple, Optional
import numpy as np

from decoding.peak_decoder import MoccaPeakDecoder
from predictions.rxn_classes import ChemicalReaction
from ms_pred.decode_ms import load_run, get_spectrum_at_rt
from scoring.score_ms import cosine_similarity_aligned
from scoring.score_rt import gaussian_rt_score
from scoring.score_lmax import gaussian_lmax_score
from scoring.score_aggregate import build_score_matrix, optimal_assignment


def build_observed_from_decoder(decoder: MoccaPeakDecoder, mzml_path: str, spectrum_tolerance_min: float = 0.2) -> List[Dict]:
    """Construct observed peak descriptors from a decoder and paired MS file.

    Each descriptor contains: 'rt', 'lmax' (single value if available), 'mz', 'intensity'.
    """
    obs: List[Dict] = []
    peak_times = decoder.get_peak_times()
    lam_info = decoder.get_lambda_max()
    lam_by_time = {}
    for entry in lam_info:
        lam_by_time[round(float(entry["apex_time"]), 3)] = float(entry["lambda_max"]) if entry.get("lambda_max") is not None else None

    run = load_run(mzml_path)
    for tr in peak_times:
        # Use midpoint as apex estimate if not available
        rt = float((tr[0] + tr[1]) / 2.0)
        mz, inten, actual = get_spectrum_at_rt(run, rt, tolerance=spectrum_tolerance_min)
        # Fallback: if no spectrum found within tolerance, leave spectrum empty
        lmax_val = lam_by_time.get(round(rt, 3))
        obs.append({
            "rt": actual if actual is not None else rt,
            "lmax": lmax_val,
            "mz": mz,
            "intensity": inten,
        })
    return obs


def build_predicted_from_reaction(reactants: List[str], solvent: str, conda_env: str = "uvvismlenv") -> List[Dict]:
    """Use predictions to generate predicted descriptors for products: RT, λmax, and optionally MS (not implemented).
    MS predictions are not available; its contribution will rely on future models.
    """
    rxn = ChemicalReaction(reactants=reactants, solvents=solvent)
    rxn.fetch_products_from_askcos_sync()
    rxn.predict_products_retention_times_sync()
    rxn.predict_products_lambda_max(conda_env=conda_env)

    preds: List[Dict] = []
    for p in rxn.get_products():
        preds.append({
            "smiles": p.get_smiles(),
            "rt": p.get_retention_time(),
            "lmax": p.get_lambda_max(),
            # Placeholder for MS prediction; leave empty arrays
            "mz": np.array([]),
            "intensity": np.array([]),
        })
    return preds


def assign_compounds(
    decoder: MoccaPeakDecoder,
    mzml_path: str,
    reactants: List[str],
    solvent: str,
    weights: Optional[Dict[str, float]] = None,
    mz_tol: float = 0.01,
    ppm: Optional[float] = None,
    rt_sigma: float = 0.5,
    lmax_sigma: float = 15.0,
) -> Dict:
    """Integrate pipeline: observed from decoding+MS, predicted from models; compute assignment.

    Returns a result dictionary with score matrix, assignment, and decorated records.
    """
    obs = build_observed_from_decoder(decoder, mzml_path)
    preds = build_predicted_from_reaction(reactants, solvent)

    S = build_score_matrix(preds, obs, weights=weights, mz_tol=mz_tol, ppm=ppm, rt_sigma=rt_sigma, lmax_sigma=lmax_sigma)
    rows, cols, total = optimal_assignment(S)

    assignments: List[Dict] = []
    for pi, oi in zip(rows, cols):
        assignments.append({
            "pred_index": int(pi),
            "obs_index": int(oi),
            "score": float(S[pi, oi]),
            "pred": preds[pi],
            "obs": obs[oi],
        })

    return {
        "score_matrix": S,
        "assignments": assignments,
        "total_score": float(total),
        "predicted": preds,
        "observed": obs,
    }
