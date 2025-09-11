"""
Lambda max scoring utilities.

Score is computed via a Gaussian kernel on |λmax_pred - λmax_obs| with a chosen sigma.
"""

from __future__ import annotations

import math


def gaussian_lmax_score(lmax_pred: float, lmax_obs: float, sigma: float = 15.0, max_score: float = 1.0) -> float:
    """Gaussian similarity on lambda max difference (nm).

    score = max_score * exp(-0.5 * (delta / sigma)^2)
    """
    if lmax_pred is None or lmax_obs is None:
        return 0.0
    delta = abs(lmax_pred - lmax_obs)
    if sigma <= 0:
        return 0.0
    return float(max_score * math.exp(-0.5 * (delta / sigma) ** 2))


