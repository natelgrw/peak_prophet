# PeakProphet: Automated LC–MS Peak Characterization

PeakProphet is an end-to-end pipeline for LC–MS peak characterization. It integrates chromatogram processing, product/property prediction, mass spectrometry parsing, and multi-criteria scoring into a unified workflow that maps observed peaks to candidate compounds.

Current Version: **1.0.0**

## 🔮 Prediction Mechanism
- Generates candidate products given reactants and solvent using the ASKCOS web server.
- Predicts retention times using online RT models.
- Predicts λ<sub>max</sub> using UV–Vis ML checkpoints.
- Provides unified PredictedProduct and ChemicalReaction classes to organize predicted values.

## 🧪 Decoding & MS Utilities
- Process LC–UV chromatograms: baseline correction, peak finding, deconvolution.
- Extract peak apexes and λ<sub>max</sub> at apex.
- Provide plotting utilities for chromatogram visualization.
- Parse mass spectrometry data (.mzML): extract TIC/BPC, pull spectra near target retention times.

## 🧮 Scoring & Assignment
- Score candidates against observed peaks by:
- Retention time (Gaussian kernel).
- λ<sub>max</sub> (Gaussian kernel).
- MS spectra similarity (cosine similarity).
- Combine feature-level scores into a weighted aggregate.
- Perform optimal assignment of predicted compounds to peaks.

## ⚙️ Installation

- Python 3.10+
- Conda

Key Dependencies:
- `mocca2` for chromatogram processing and peak extraction
- `playwright` and `pyppeteer` for ASKCOS and RTPred web server automation
- `chemprop` for UVVisML lambda max prediction model operations
- `pymzml` for mass spectra extraction and data processing
- `scipy` for peak assignment and scoring

## 🧠 Models Used

- Forward Synthesis Product Prediction: **ASKCOS**
  ```
  @article{askcos2025,
    title        = {ASKCOS: Open-Source, Data-Driven Synthesis Planning},
    author       = {Zhengkai Tu and Sourabh J. Choure and Mun Hong Fong and Jihye Roh and Itai Levin and Kevin Yu and Joonyoung F. Joung and Nathan Morgan and Shih-Cheng Li and Xiaoqi Sun and Huiqian Lin and Mark Murnin and Jordan P. Liles and Thomas J. Struble and Michael E. Fortunato and Mengjie Liu and William H. Green and Klavs F. Jensen and Connor W. Coley},
    journal      = {Accounts of Chemical Research},
    year         = {2025},
    volume       = {58},
    number       = {11},
    pages        = {1764--1775},
    doi          = {10.1021/acs.accounts.5c00155},
    url          = {https://askcos.mit.edu},
  }
  ```

- Retention Time Prediction: **RTPred**
  ```
  @article{rtpred2025,
    title={RTPred: A web server for accurate, customized liquid chromatography retention time prediction of chemicals},
    author={Zakir, Mahi and LeVatte, Marcia A. and Wishart, David S.},
    journal={Journal of Chromatography A},
    year={2025},
    volume={1747}
    doi={10.1016/j.chroma.2025.465816},
    url={https://rtpred.ca}
  }
  ```
  
- Lambda Max Prediction: **UVVisML**

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