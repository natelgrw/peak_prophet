"""
Mass spectrum similarity scoring utilities.

We align predicted and observed centroid spectra within an m/z tolerance and
compute cosine similarity on the aligned intensity vectors.
"""

from __future__ import annotations

from typing import List, Tuple, Optional
import numpy as np


def _match_peaks(pred_mz: np.ndarray, obs_mz: np.ndarray, mz_tol: float, ppm: Optional[float]) -> Tuple[List[int], List[int]]:
    """Return index pairs of matched peaks within tolerance.

    Matches each predicted peak to at most one observed peak (greedy by nearest m/z).
    """
    pred_idx: List[int] = []
    obs_idx: List[int] = []
    if pred_mz.size == 0 or obs_mz.size == 0:
        return pred_idx, obs_idx

    # Sort observed for fast nearest search
    order = np.argsort(obs_mz)
    obs_sorted = obs_mz[order]

    used = np.zeros(obs_sorted.size, dtype=bool)

    for i, m in enumerate(pred_mz):
        # binary search position
        j = int(np.searchsorted(obs_sorted, m))
        candidates = []
        if j < obs_sorted.size:
            candidates.append(j)
        if j - 1 >= 0:
            candidates.append(j - 1)

        best_k = -1
        best_delta = np.inf
        for k in candidates:
            if used[k]:
                continue
            dm = abs(obs_sorted[k] - m)
            tol = (ppm * m / 1e6) if ppm is not None else mz_tol
            if dm <= tol and dm < best_delta:
                best_delta = dm
                best_k = k

        if best_k >= 0:
            used[best_k] = True
            pred_idx.append(i)
            obs_idx.append(best_k)

    # Map back observed indices to original order
    obs_idx = [int(order[k]) for k in obs_idx]
    return pred_idx, obs_idx


def cosine_similarity_aligned(
    pred_mz: List[float] | np.ndarray,
    pred_intensity: List[float] | np.ndarray,
    obs_mz: List[float] | np.ndarray,
    obs_intensity: List[float] | np.ndarray,
    mz_tol: float = 0.01,
    ppm: Optional[float] = None,
    normalize: bool = True,
) -> float:
    """Cosine similarity between predicted and observed spectra after alignment.

    Parameters
    ----------
    pred_mz, obs_mz : arrays
        Centroid m/z values.
    pred_intensity, obs_intensity : arrays
        Corresponding intensities.
    mz_tol : float
        Absolute m/z tolerance in Da if ppm is None.
    ppm : Optional[float]
        Parts-per-million tolerance; if provided, used instead of mz_tol.
    normalize : bool
        If True, scale each spectrum vector to unit norm prior to cosine.

    Returns
    -------
    float in [0, 1]
    """
    pred_mz = np.asarray(pred_mz, dtype=float)
    pred_int = np.asarray(pred_intensity, dtype=float)
    obs_mz = np.asarray(obs_mz, dtype=float)
    obs_int = np.asarray(obs_intensity, dtype=float)

    if pred_mz.size == 0 or obs_mz.size == 0:
        return 0.0

    # Keep only positive intensities
    pred_mask = pred_int > 0
    obs_mask = obs_int > 0
    pred_mz, pred_int = pred_mz[pred_mask], pred_int[pred_mask]
    obs_mz, obs_int = obs_mz[obs_mask], obs_int[obs_mask]
    if pred_mz.size == 0 or obs_mz.size == 0:
        return 0.0

    # Align by greedy nearest within tolerance
    ip, io = _match_peaks(pred_mz, obs_mz, mz_tol=mz_tol, ppm=ppm)
    if len(ip) == 0:
        return 0.0

    v1 = pred_int[ip]
    v2 = obs_int[io]

    if normalize:
        n1 = np.linalg.norm(v1)
        n2 = np.linalg.norm(v2)
        if n1 == 0 or n2 == 0:
            return 0.0
        v1 = v1 / n1
        v2 = v2 / n2

    sim = float(np.dot(v1, v2))
    # Clamp to [0, 1]
    if sim < 0:
        sim = 0.0
    if sim > 1:
        sim = 1.0
    return sim


