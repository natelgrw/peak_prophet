"""
decode_ms.py

Utilities to read and analyze mass spectrometry data from .mzML files.

Dependencies:
- pymzml
- matplotlib (for plotting)

Functions:
- load_run(mzml_path): load mzML file (pymzml Reader)
- extract_tic(run): total ion chromatogram [(rt, tic)]
- extract_bpc(run): base peak chromatogram [(rt, bpi)]
- get_spectrum_at_rt(run, target_rt): closest MS1 spectrum to target RT
- plot_tic(tic), plot_bpc(bpc), plot_spectrum(mz, intensity)
"""

from __future__ import annotations

from typing import List, Tuple, Optional
import math

import pymzml
import numpy as np
import matplotlib.pyplot as plt


def load_run(mzml_path: str) -> pymzml.run.Reader:
    """Load an mzML file and return a pymzml Reader."""
    return pymzml.run.Reader(mzml_path)


def _is_ms1(spectrum: pymzml.spec.Spectrum) -> bool:
    try:
        ms_level = spectrum.ms_level
        return ms_level == 1
    except Exception:
        return False


def extract_tic(run: pymzml.run.Reader) -> List[Tuple[float, float]]:
    """Extract Total Ion Chromatogram as list of (retention_time, TIC)."""
    tic: List[Tuple[float, float]] = []
    for spec in run:
        if not _is_ms1(spec):
            continue
        rt = _get_retention_time(spec)
        if rt is None:
            continue
        tic_value = float(spec.TIC) if getattr(spec, "TIC", None) is not None else float(np.sum(spec.i))
        tic.append((rt, tic_value))
    return tic


def extract_bpc(run: pymzml.run.Reader) -> List[Tuple[float, float]]:
    """Extract Base Peak Chromatogram as list of (retention_time, base_peak_intensity)."""
    bpc: List[Tuple[float, float]] = []
    for spec in run:
        if not _is_ms1(spec):
            continue
        rt = _get_retention_time(spec)
        if rt is None:
            continue
        if len(spec.i) == 0:
            continue
        bpi = float(np.max(spec.i))
        bpc.append((rt, bpi))
    return bpc


def get_spectrum_at_rt(run: pymzml.run.Reader, target_rt: float, tolerance: float = 0.2) -> Tuple[np.ndarray, np.ndarray, Optional[float]]:
    """
    Return the MS1 spectrum (m/z, intensity, actual_rt) closest to target_rt (minutes) within tolerance.
    If none found within tolerance, returns empty arrays and None RT.
    """
    closest_spec = None
    closest_delta = math.inf
    closest_rt: Optional[float] = None
    for spec in run:
        if not _is_ms1(spec):
            continue
        rt = _get_retention_time(spec)
        if rt is None:
            continue
        delta = abs(rt - target_rt)
        if delta < closest_delta:
            closest_delta = delta
            closest_spec = spec
            closest_rt = rt
    if closest_spec is None or closest_delta > tolerance:
        return np.array([]), np.array([]), None
    mz = np.array(closest_spec.mz)
    intensity = np.array(closest_spec.i)
    return mz, intensity, closest_rt


def _get_retention_time(spec: pymzml.spec.Spectrum) -> Optional[float]:
    """Get retention time in minutes if available."""
    try:
        # pymzml provides scan_time in minutes for many files; else parse from scanList
        rt = spec.scan_time_in_minutes()
        if rt is not None:
            return float(rt)
    except Exception:
        pass
    try:
        # Fallback: try seconds and convert to minutes
        rt_sec = spec.scan_time_in_seconds()
        if rt_sec is not None:
            return float(rt_sec) / 60.0
    except Exception:
        pass
    return None


def plot_tic(tic: List[Tuple[float, float]]):
    """Plot Total Ion Chromatogram."""
    if not tic:
        return None
    rt, intensity = zip(*tic)
    fig, ax = plt.subplots(figsize=(9, 3))
    ax.plot(rt, intensity, color="black", lw=1.2)
    ax.set_xlabel("Retention time (min)")
    ax.set_ylabel("TIC")
    ax.set_title("Total Ion Chromatogram")
    fig.tight_layout()
    return fig


def plot_bpc(bpc: List[Tuple[float, float]]):
    """Plot Base Peak Chromatogram."""
    if not bpc:
        return None
    rt, intensity = zip(*bpc)
    fig, ax = plt.subplots(figsize=(9, 3))
    ax.plot(rt, intensity, color="steelblue", lw=1.2)
    ax.set_xlabel("Retention time (min)")
    ax.set_ylabel("Base peak intensity")
    ax.set_title("Base Peak Chromatogram")
    fig.tight_layout()
    return fig


def plot_spectrum(mz: np.ndarray, intensity: np.ndarray, title: Optional[str] = None):
    """Plot a centroided spectrum (stick plot)."""
    if mz.size == 0:
        return None
    fig, ax = plt.subplots(figsize=(9, 3))
    for x, y in zip(mz, intensity):
        ax.vlines(x, 0, y, colors="darkred", lw=1)
    ax.set_xlabel("m/z")
    ax.set_ylabel("Intensity")
    ax.set_title(title or "MS1 Spectrum")
    fig.tight_layout()
    return fig


def demo(mzml_path: str, rt_to_plot: Optional[float] = None):
    """Quick demonstration: load file, plot TIC/BPC, and a spectrum near rt_to_plot."""
    run = load_run(mzml_path)
    tic = extract_tic(run)
    # Re-open for a fresh iterator
    run = load_run(mzml_path)
    bpc = extract_bpc(run)

    fig1 = plot_tic(tic)
    fig2 = plot_bpc(bpc)

    fig3 = None
    if rt_to_plot is not None:
        run = load_run(mzml_path)
        mz, inten, actual_rt = get_spectrum_at_rt(run, rt_to_plot)
        title = f"Spectrum near {actual_rt:.2f} min" if actual_rt is not None else "Spectrum"
        fig3 = plot_spectrum(mz, inten, title=title)
    return {
        "tic": tic,
        "bpc": bpc,
        "fig_tic": fig1,
        "fig_bpc": fig2,
        "fig_spectrum": fig3,
    }


if __name__ == "__main__":
    # Example usage: update path as needed
    example_path = "/Users/nathanleung/Documents/Programming/Research Projects/peak_prophet/data_raw/F8.mzML"
    out = demo(example_path, rt_to_plot=5.0)
    print(f"TIC points: {len(out['tic'])}, BPC points: {len(out['bpc'])}")


