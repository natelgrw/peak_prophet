"""
peak_decoder.py

A Python script that utilizes MOCCA2 to create peak decoder objects aiding in the extraction of
peak locations and peak widths in LC-MS ultraviolet and mass spectra. This script is compatible
with raw data files from Agilent, Schimadzu, and Waters machines.

Each peak decoder object contains essential functions to process LC-MS experiment 
files and return a list of peaks represented as tuples of length 2. The first and
second elements represent the starting and ending x coordinates of the peak.

Additionally, other supplemental functions exist to extract chromatogram wavelength
and absorbance data using MOCCA2.

Author: @natelgrw
Created: 4/22/2025
Last Edited: 5/8/2025
"""

#TODO: implement maxima and relative maxima calculations
#TODO: implement lambda max data for peaks
#TODO: implement plotting functions for 1D, 2D, and lambda max representations

from typing import Literal, List, Tuple, Optional
from mocca2 import Chromatogram
from mocca2.deconvolution.peak_models import PeakModel
import numpy as np
import matplotlib.pyplot as plt

class MoccaPeakDecoder:
    def __init__(self, 
                 file_path: str, 
                 rxn_type: str,
                 reactants: List[str],
                 solvents: List[str],
                 wavelength: Tuple[int, int] | None = None,
                 method: Literal['asls', 'arpls', 'flatfit'] = "flatfit",
                 time: tuple[int | None, int | None] = None):
        """
        Initializes a MoccaPeakDecoder object and accompanying chromatogram
        with a specified raw file data path, optional wavelength specifications, 
        baseline corrections, and time specifications. Also includes key reaction
        data on solvents and reactants.
        """
        self.file_path = file_path
        self.rxn_type = rxn_type
        self.reactants = reactants
        self.solvents = solvents
        self.wavelength = wavelength
        self.method = method
        self.time = time
        self.chromatogram = Chromatogram(sample=file_path)

        if self.wavelength != None:
            self.chromatogram.extract_wavelength(self.wavelength[0], self.wavelength[1])

        if self.time != None:
            self.chromatogram.extract_time(self.time[0], self.time[1], inplace=True)

        self.chromatogram.correct_baseline(self.method)

    def get_peaks(self,
                  deconvolve_algo: PeakModel | Literal['BiGaussian', 'BiGaussianTrailing', 'FraserSuzuki', 'Bemg'],
                  min_deconvolve_r2: float,
                  concentration_relax: bool,
                  max_num_peaks: int,
                  contraction_algo: Literal['mean', 'max', 'weighted_mean'] = 'mean',
                  min_h: float = 10.0,
                  min_time: float | None = None,
                  max_time: float | None = None,
                  ):
        """
        Calls find_peaks() and deconvolve_peaks() on the Chromatogram object
        derived from the input file path, returning a list of Peak objects stored 
        within the Chromatogram.
        """
        self.peak_params = {
        "deconvolution_model": str(deconvolve_algo),
        "min_r2": min_deconvolve_r2,
        "relax_concentration_constraints": concentration_relax,
        "max_components": max_num_peaks,
        "contraction_algorithm": contraction_algo,
        "min_height": min_h,
        "min_elution_time": min_time,
        "max_elution_time": max_time
        }

        self.chromatogram.find_peaks(contraction=contraction_algo, min_height=min_h, 
                                     min_elution_time=min_time, max_elution_time=max_time)
        self.chromatogram.deconvolve_peaks(model=deconvolve_algo, min_r2=min_deconvolve_r2, 
                                           relaxe_concs=concentration_relax, max_comps=max_num_peaks)

        return self.chromatogram.peaks

    def get_peak_times(self):
        """
        Iterates through all DeconvolvedPeak objects on the Chromatogram object, and
        returns a list of tuples with index 2 Each tuple representing a component peak,
        with the first index representing the start and the second representing the end
        of the peak.

        All subpeak components of a DeconvolvedPeak object are represented as tuples. If
        a DeconvolvedPeak object is marked as unresolved, subpeaks cannot be accurately
        modeled, and the whole DeconvolvedPeak is just treated as a singular tuple.
        """
        time_ranges = []
        time_axis = self.chromatogram.time

        for peak in self.chromatogram.peaks:
            # case 1: deconvolved peak can be resolved
            if peak.resolved and peak.components:
                for component in peak.components:
                    conc = component.concentration
                    tup_peak_indices = (conc > 1e-6).nonzero()[0]

                    if tup_peak_indices.size == 0:
                        continue

                    start_idx = peak.left + tup_peak_indices[0]
                    end_idx = peak.left + tup_peak_indices[-1]

                    time_ranges.append((time_axis[start_idx], time_axis[end_idx]))
            # case 2: deconvolved peak cannot be resolved
            else:
                start_idx = peak.left
                end_idx = peak.right

                time_ranges.append((time_axis[start_idx], time_axis[end_idx]))

        return time_ranges

    def get_peak_areas(self):
        """
        Iterates through all DeconvolvedPeak objects on the Chromatogram object, and
        returns a list of float values. Each float represents the integral
        underneath each component peak in a Chromatogram.

        If a DeconvolvedPeak is unresolvable, the entire DeconvolvedPeak is treated
        as a singular peak, and the integral is estimated manually to a large degree
        of accuracy.
        """
        areas = []
        time_axis = self.chromatogram.time
        data = self.chromatogram.data

        for peak in self.chromatogram.peaks:
            # case 1: deconvolved peak can be resolved
            if peak.resolved and peak.components:
                for component in peak.components:
                    areas.append(component.integral)
            # case 2: deconvolved peak cannot be resolved
            else:
                peak_data = data[:, peak.left : peak.right + 1]
                signal = peak_data.sum(axis=0)

                # approximate time increment
                dt = time_axis[1] - time_axis[0]

                area = np.trapezoid(signal, dx=dt)
                areas.append(area)

        return areas
    
    def get_maxima(self):
        """
        Compute apex (maximum) for each peak component or unresolved peak and
        return a list of dictionaries with apex time, apex value, and relative height.

        Returns
        -------
        List[dict]
            Each item contains: {"apex_time", "apex_value", "relative_height"}
        """
        maxima: List[dict] = []
        time_axis = self.chromatogram.time
        data = self.chromatogram.data
        # 1D chromatogram signal by summing across spectral axis
        signal_1d = data.sum(axis=0)
        if signal_1d.size == 0:
            return maxima
        global_max = float(signal_1d.max()) if signal_1d.max() != 0 else 1.0

        for peak in self.chromatogram.peaks:
            if peak.resolved and getattr(peak, 'components', None):
                for component in peak.components:
                    conc = component.concentration
                    if conc is None or conc.size == 0:
                        continue
                    local_idx = int(np.argmax(conc))
                    apex_idx = peak.left + local_idx
                    apex_idx = min(max(apex_idx, 0), signal_1d.size - 1)
                    apex_time = float(time_axis[apex_idx])
                    apex_value = float(signal_1d[apex_idx])
                    rel = apex_value / global_max if global_max else 0.0
                    maxima.append({
                        "apex_time": apex_time,
                        "apex_value": apex_value,
                        "relative_height": rel
                    })
            else:
                left = int(peak.left)
                right = int(peak.right)
                left = max(left, 0)
                right = min(right, signal_1d.size - 1)
                if right < left:
                    continue
                seg = signal_1d[left:right + 1]
                local_idx = int(np.argmax(seg))
                apex_idx = left + local_idx
                apex_time = float(time_axis[apex_idx])
                apex_value = float(signal_1d[apex_idx])
                rel = apex_value / global_max if global_max else 0.0
                maxima.append({
                    "apex_time": apex_time,
                    "apex_value": apex_value,
                    "relative_height": rel
                })

        return maxima

    def get_lambda_max(self):
        """
        Determine the lambda max (wavelength of maximum absorbance) at each peak apex.

        Returns
        -------
        List[dict]
            Each item contains: {"apex_time", "lambda_max", "absorbance_max"}
        """
        results: List[dict] = []
        data = self.chromatogram.data
        # Attempt to get wavelength axis; support common attribute names
        wavelengths = getattr(self.chromatogram, 'wavelengths', None)
        if wavelengths is None:
            wavelengths = getattr(self.chromatogram, 'wavelength', None)
        if wavelengths is None:
            # No spectral axis available
            return results

        # Get apex indices via maxima
        maxima = self.get_maxima()
        if not maxima:
            return results

        time_axis = self.chromatogram.time
        # Build a map from time to index for faster lookup
        time_to_index = {float(t): idx for idx, t in enumerate(time_axis)}

        for m in maxima:
            apex_time = m["apex_time"]
            # Find nearest index to apex_time
            # Prefer exact match; otherwise, use argmin on absolute difference
            apex_idx: Optional[int] = time_to_index.get(apex_time)
            if apex_idx is None:
                apex_idx = int(np.argmin(np.abs(time_axis - apex_time)))
            apex_idx = min(max(apex_idx, 0), data.shape[1] - 1)

            spectrum = data[:, apex_idx]
            if spectrum.size == 0:
                continue
            lam_idx = int(np.argmax(spectrum))
            lam_val = float(wavelengths[lam_idx]) if hasattr(wavelengths, '__len__') else float(wavelengths)
            abs_max = float(spectrum[lam_idx])
            results.append({
                "apex_time": float(apex_time),
                "lambda_max": lam_val,
                "absorbance_max": abs_max
            })

        return results

    def get_min_peak_distance(self):
        """
        Returns the minimum distance between two peaks in a Chromatogram.
        """
        peak_distances = []
        peak_data = self.get_peak_times()

        for i in range(len(peak_data) - 1):
            first = peak_data[i][1]
            second = peak_data[i+1][0]
            difference = second - first
            peak_distances.append(difference)

        return min(peak_distances)

    def get_summary(self):
        """
        Returns a comprehensive dictionary representative of data in a
        Chromatogram. Includes information about peak widths, peak areas,
        peak maxima, and a templates for compound identification.
        """
        times = self.get_peak_times()
        areas = self.get_peak_areas()
        min_peak_distance = self.get_min_peak_distance()

        return {
            "reaction": self.rxn_type,
            "reactants": self.reactants,
            "solvents": self.solvents,
            "lambda_range": self.wavelength,
            "baseline_method": self.method,
            "time_range": self.time,
            "peak_picking": self.peak_params,
            "peaks": [

            ],
            "min_distance": min_peak_distance
        }
    
    def plot_chromatogram_1d(self, show_peaks: bool = True):
        """
        Plot 1D chromatogram (time vs summed absorbance) and optionally shade peak regions.
        """
        time_axis = self.chromatogram.time
        signal_1d = self.chromatogram.data.sum(axis=0)
        plt.figure(figsize=(10, 4))
        plt.plot(time_axis, signal_1d, color='navy', lw=1.5)
        plt.xlabel('Time')
        plt.ylabel('Summed absorbance')
        plt.title('Chromatogram (1D)')
        if show_peaks and getattr(self.chromatogram, 'peaks', None):
            for peak in self.chromatogram.peaks:
                left = self.chromatogram.time[int(peak.left)]
                right = self.chromatogram.time[int(peak.right)]
                plt.axvspan(left, right, color='orange', alpha=0.2)
        plt.tight_layout()
        plt.show()

    def plot_chromatogram_2d(self):
        """
        Plot 2D chromatogram heatmap (wavelength vs time).
        """
        data = self.chromatogram.data
        time_axis = self.chromatogram.time
        wavelengths = getattr(self.chromatogram, 'wavelengths', None)
        if wavelengths is None:
            wavelengths = getattr(self.chromatogram, 'wavelength', None)

        plt.figure(figsize=(10, 5))
        if wavelengths is not None:
            extent = [float(time_axis[0]), float(time_axis[-1]), float(np.min(wavelengths)), float(np.max(wavelengths))]
            plt.imshow(data, aspect='auto', origin='lower', extent=extent, cmap='viridis')
            plt.ylabel('Wavelength')
        else:
            plt.imshow(data, aspect='auto', origin='lower', cmap='viridis')
            plt.ylabel('Spectral index')
        plt.xlabel('Time')
        plt.title('Chromatogram (2D)')
        cbar = plt.colorbar()
        cbar.set_label('Absorbance')
        plt.tight_layout()
        plt.show()

    def plot_lambda_absorption(self, max_traces: int = 5):
        """
        Plot spectral absorption at the apex of up to `max_traces` peaks.
        """
        data = self.chromatogram.data
        wavelengths = getattr(self.chromatogram, 'wavelengths', None)
        if wavelengths is None:
            wavelengths = getattr(self.chromatogram, 'wavelength', None)
        if wavelengths is None:
            return

        maxima = self.get_maxima()
        if not maxima:
            return

        time_axis = self.chromatogram.time
        plt.figure(figsize=(10, 5))
        count = 0
        for m in maxima:
            if count >= max_traces:
                break
            apex_time = m["apex_time"]
            apex_idx = int(np.argmin(np.abs(time_axis - apex_time)))
            spectrum = data[:, apex_idx]
            plt.plot(wavelengths, spectrum, lw=1.2, label=f"t={apex_time:.2f}")
            count += 1
        plt.xlabel('Wavelength')
        plt.ylabel('Absorbance')
        plt.title('Peak apex spectra')
        plt.legend()
        plt.tight_layout()
        plt.show()
