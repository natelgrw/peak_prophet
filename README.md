# PeakProphet: End-to-End LC–MS Peak Characterization Pipeline

PeakProphet is an end-to-end pipeline for LC–UV–MS peak characterization. It combines chromatogram decoding (MOCCA2), product prediction (ASKCOS), retention time prediction (RTPred), λ<sub>max</sub> prediction (UVVisML/Chemprop), MS parsing (pymzML), and multi-criteria scoring/assignment into a single workflow to help map observed peaks to candidate compounds.

## 🧩 What’s in this Repository

### 🔮 Predictions
The predictions layer generates candidate products and their properties given reactants and solvent. We automate ASKCOS for product proposals (`predictions/askcos_scraper.py`), predict retention times via the rtpred.ca interface (`predictions/rt_pred/rt_pred.py`), and predict λ<sub>max</sub> using UVVisML (Chemprop) checkpoints (`predictions/lmax_pred/lmax_pred.py`). These are orchestrated through a convenient `ChemicalReaction` abstraction in `predictions/rxn_classes.py`.

### 🧪 Decoding & MS Utilities
PeakProphet uses MOCCA2 to process LC–UV chromatograms. The module `decoding/peak_decoder.py` performs baseline correction, peak finding and deconvolution, computes apexes and λ<sub>max</sub> at apex, and provides 1D/2D plotting utilities. For mass spectrometry, `ms_pred/decode_ms.py` reads `.mzML` files with `pymzml`, extracts TIC/BPC, and retrieves spectra near target retention times.

### 🧮 Scoring & Assignment
To compare predicted candidates to observed peaks, PeakProphet includes feature-wise scorers and an aggregate matcher. `scoring/score_ms.py` computes cosine similarity on aligned centroid spectra, `scoring/score_rt.py` scores retention time differences using a Gaussian kernel, and `scoring/score_lmax.py` does the same for λ<sub>max</sub>. `scoring/score_aggregate.py` builds a weighted score matrix and performs optimal assignment (Hungarian method, with a greedy fallback). The integrator `assignment/assign_compounds.py` ties decoding, predictions, MS, and scoring together to assign compounds to peaks.

### 📓 Notebooks
Interactive notebooks demonstrate each stage of the workflow: product and property predictions (`predictions/predictions_demo.ipynb`), chromatogram decoding (`decoding/peak_decoder_demo.ipynb`), MS parsing and plots (`ms_pred/ms_demo.ipynb`), and multi-criteria scoring (`scoring/scoring_demo.ipynb`).

### ▶️ Pipeline Entry Point
The script `run_pipeline.py` executes an end-to-end example on `data_raw/F8.mzML`, running decoding, predictions, scoring, and assignment, and printing a concise summary of the results.

## ⚙️ Installation

- Python 3.10+
- Recommended: Conda for environment management

Key dependencies (see files for details):
- MOCCA2 (chromatogram processing)
- Playwright and Pyppeteer (automation for ASKCOS and RTPred)
- Chemprop with UVVisML checkpoints (λ<sub>max</sub> prediction)
- `pymzml` (MS parsing)
- `scipy` (optional for Hungarian assignment; greedy fallback provided)

UVVisML prediction is executed in a dedicated conda environment, e.g. `uvvismlenv`, via:

```
conda run -n uvvismlenv chemprop_predict ...
```

so your active Python environment doesn’t need to switch.

## 🚀 Quickstart

1) Prepare data
- Place your `.mzML` file(s) into `data_raw/` (example: `F8.mzML`).

2) Run the pipeline

```
python run_pipeline.py
```

This will:
- Load and baseline-correct the chromatogram
- Find and deconvolve peaks
- Predict products (ASKCOS), RT (RTPred), and λ<sub>max</sub> (UVVisML)
- Extract observed MS spectra and λ<sub>max</sub> at peak apexes
- Score predicted vs observed and compute optimal assignments

3) Explore the demos
- Open the notebooks in `predictions/`, `decoding/`, `ms_pred/`, and `scoring/` for step-by-step examples.

## 🧠 Models Used

- 🔵 Retention Time: **RTPred** (`https://rtpred.ca/`) via headless browser automation
- 🟣 Lambda Max: **UVVisML (Chemprop)** models with provided checkpoints (`predictions/lmax_pred/uvvisml/`)

## 📚 Notes on Data

While PeakProphet can be used with any compatible `.mzML` and reaction inputs, you may also leverage open datasets (e.g., λ<sub>max</sub>, RT) to benchmark and extend the models. See the included notebooks for guidance.

## ✒️ Citation

If you use PeakProphet in a project, please consider citing related datasets and models, for example:

```
@dataset{natelgrwamaxdataset,
  title={AMAX: A Benchmark Dataset for UV-Vis Lambda Max Prediction in LC-MS},
  author={Leung, Nathan},
  institution={Coley Research Group @ MIT},
  year={2025},
  howpublished={\url{https://huggingface.co/datasets/natelgrw/AMAX}}
}
```

Also consider citing RTPred and UVVisML/Chemprop where applicable.

## 📫 Contact

Questions or suggestions are welcome. Please open an issue or reach out to the author.

## 📖 References

### λ<sub>max</sub> prediction

```
@article{greenman2022multi,
  title={Multi-fidelity prediction of molecular optical peaks with deep learning},
  author={Greenman, Kevin P. and Green, William H. and G{\'{o}}mez-Bombarelli, Rafael},
  journal={Chemical Science},
  year={2022},
  volume={13},
  issue={4},
  pages={1152-1162},
  publisher={The Royal Society of Chemistry},
  doi={10.1039/D1SC05677H},
  url={http://dx.doi.org/10.1039/D1SC05677H}
}
```

### Retention time prediction

```
@misc{rtpred2025,
  title={RTPred: Retention time prediction for liquid chromatography},
  year={2025},
  howpublished={\url{https://www.sciencedirect.com/science/article/pii/S0021967325001645}},
  note={ScienceDirect article; please use the final journal citation when available}
}
```
