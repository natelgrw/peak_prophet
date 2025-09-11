"""
Aggregate scoring utilities.

Build a weighted aggregate score matrix for predicted vs observed peaks and
optionally compute an optimal assignment (Hungarian algorithm).
"""

from __future__ import annotations

from typing import List, Tuple, Optional, Dict
import numpy as np

from .score_ms import cosine_similarity_aligned
from .score_rt import gaussian_rt_score
from .score_lmax import gaussian_lmax_score

try:
    from scipy.optimize import linear_sum_assignment
    _HAS_SCIPY = True
except Exception:
    _HAS_SCIPY = False


def build_score_matrix(
    preds: List[Dict],
    obs: List[Dict],
    weights: Dict[str, float] | None = None,
    mz_tol: float = 0.01,
    ppm: Optional[float] = None,
    rt_sigma: float = 0.5,
    lmax_sigma: float = 15.0,
) -> np.ndarray:
    """
    Build an aggregate score matrix S (shape [len(preds), len(obs)]).

    Each pred dict may contain keys: 'mz', 'intensity', 'rt', 'lmax'.
    Each obs dict may contain the same keys.
    """
    if weights is None:
        weights = {"ms": 0.5, "rt": 0.3, "lmax": 0.2}

    P = len(preds)
    O = len(obs)
    S = np.zeros((P, O), dtype=float)

    for i, p in enumerate(preds):
        for j, o in enumerate(obs):
            score = 0.0
            wsum = 0.0
            # MS score
            if "mz" in p and "intensity" in p and "mz" in o and "intensity" in o:
                ms = cosine_similarity_aligned(p["mz"], p["intensity"], o["mz"], o["intensity"], mz_tol=mz_tol, ppm=ppm)
                score += weights.get("ms", 0.0) * ms
                wsum += weights.get("ms", 0.0)
            # RT score
            if p.get("rt") is not None and o.get("rt") is not None:
                rt = gaussian_rt_score(float(p["rt"]), float(o["rt"]), sigma=rt_sigma)
                score += weights.get("rt", 0.0) * rt
                wsum += weights.get("rt", 0.0)
            # Lmax score
            if p.get("lmax") is not None and o.get("lmax") is not None:
                lm = gaussian_lmax_score(float(p["lmax"]), float(o["lmax"]), sigma=lmax_sigma)
                score += weights.get("lmax", 0.0) * lm
                wsum += weights.get("lmax", 0.0)

            S[i, j] = (score / wsum) if wsum > 0 else 0.0
    return S


def optimal_assignment(score_matrix: np.ndarray) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Compute optimal 1-1 assignment that maximizes total aggregate score using Hungarian method.
    Returns row_indices, col_indices, total_score.
    If SciPy is not available, fall back to greedy matching.
    """
    S = np.asarray(score_matrix, dtype=float)
    if S.size == 0:
        return np.array([], dtype=int), np.array([], dtype=int), 0.0

    if _HAS_SCIPY:
        # Hungarian solves a minimization; convert to cost as (1 - score)
        cost = 1.0 - S
        r, c = linear_sum_assignment(cost)
        total = float(S[r, c].sum())
        return r, c, total

    # Greedy fallback: repeatedly pick best remaining pair
    S_copy = S.copy()
    rows = []
    cols = []
    total = 0.0
    while True:
        idx = np.unravel_index(np.argmax(S_copy), S_copy.shape)
        i, j = int(idx[0]), int(idx[1])
        best = float(S_copy[i, j])
        if best <= 0:
            break
        rows.append(i)
        cols.append(j)
        total += best
        S_copy[i, :] = -np.inf
        S_copy[:, j] = -np.inf
        if not np.isfinite(S_copy).any():
            break
    return np.array(rows, dtype=int), np.array(cols, dtype=int), total


