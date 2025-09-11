"""
Retention time scoring utilities.

Score is computed via a Gaussian kernel on |rt_pred - rt_obs| with a chosen sigma.
"""

from __future__ import annotations

from typing import Optional
import math


def gaussian_rt_score(rt_pred: float, rt_obs: float, sigma: float = 0.5, max_score: float = 1.0) -> float:
    """Gaussian similarity on retention time difference.

    score = max_score * exp(-0.5 * (delta / sigma)^2)
    """
    if rt_pred is None or rt_obs is None:
        return 0.0
    delta = abs(rt_pred - rt_obs)
    if sigma <= 0:
        return 0.0
    return float(max_score * math.exp(-0.5 * (delta / sigma) ** 2))


