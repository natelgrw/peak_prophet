# PeakProphet: Automated LC–MS Peak Characterization

PeakProphet is an end-to-end pipeline for LC–MS peak characterization. It integrates chromatogram processing, product/property prediction, mass spectrometry parsing, and multi-criteria scoring into a unified workflow that maps observed peaks to candidate compounds.

Current Version: **1.0.0**

## 🔮 Prediction Mechanism

PeakProphet employs a comprehensive multi-modal prediction pipeline that generates candidate compounds and predicts their analytical properties:

### Product Prediction
- **ASKCOS Integration**: Generates candidate products given reactants and solvent using the ASKCOS web server
- **SMILES-based**: All products are represented as SMILES strings with associated probabilities and molecular weights

### Analytical Property Prediction

#### Retention Time Prediction
- **RTPred Integration**: Uses online RT models via web scraping (rtpred.ca)
- **CS22 Method**: Employs the CS22 chromatographic method for accurate retention time estimation
- **Batch Processing**: Handles multiple compounds simultaneously for efficiency

#### UV-Vis Absorption Prediction  
- **ChemProp Models**: Predicts λ<sub>max</sub> using UV–Vis ML checkpoints trained on experimental data
- **Multi-fidelity Approach**: Leverages deep learning models for accurate absorption peak prediction
- **Solvent-aware**: Considers solvent effects on absorption spectra

#### Mass Spectrometry Adduct Prediction
- **Comprehensive Coverage**: Predicts **46 adducts** (31 positive + 15 negative) for each compound
- **Literature-based Probabilities**: Assigns realistic relative abundances based on mass spectrometry literature
- **Adduct Types Include**:
  - **Common adducts**: `[M+H]+`, `[M-H]-`, `[M+Na]+`, `[M+K]+`, `[M+NH4]+`
  - **Solvent adducts**: `[M+ACN+H]+`, `[M+CH3OH+H]+`, `[M+DMSO+H]+`
  - **Doubly charged**: `[M+2H]2+`, `[M+H+Na]2+`, `[M+2Na]2+`
  - **Dimer adducts**: `[2M+H]+`, `[2M+Na]+`, `[2M-H]-`
  - **Triply charged**: `[M+3H]3+`, `[M+2H+Na]3+`
  - **Negative adducts**: `[M+Cl]-`, `[M+Br]-`, `[M+FA-H]-`, `[M+TFA-H]-`

### Data Organization
- **PredictedProduct Class**: Unified representation with SMILES, probability, molecular weight, retention time, λ<sub>max</sub>, and MS adducts
- **ChemicalReaction Class**: Manages reaction context and orchestrates all prediction methods
- **Dictionary Format**: MS adducts stored as `{adduct_mass: relative_probability}` for easy integration with scoring algorithms

## 🧪 Decoding & MS Utilities
- Process LC–UV chromatograms: baseline correction, peak finding, deconvolution.
- Extract peak apexes and λ<sub>max</sub> at apex.
- Provide plotting utilities for chromatogram visualization.
- Parse mass spectrometry data (.mzML): extract TIC/BPC, pull spectra near target retention times.

## 🧮 Scoring & Assignment

PeakProphet employs a sophisticated multi-criteria scoring system that evaluates predicted compounds against observed LC-MS peaks:

### Scoring Criteria

#### Retention Time Scoring
- **Gaussian Kernel**: Evaluates RT matches using Gaussian similarity functions
- **Tolerance-based**: Accounts for chromatographic variability and measurement uncertainty

#### UV-Vis Absorption Scoring  
- **λ<sub>max</sub> Matching**: Compares predicted vs observed absorption maxima
- **Gaussian Kernel**: Provides probabilistic scoring for absorption peak alignment

#### Mass Spectrometry Scoring
- **Adduct Matching**: Compares predicted adduct masses against observed MS peaks
- **Probability-weighted**: Uses literature-based adduct probabilities for scoring
- **Multi-adduct Support**: Evaluates all 46 predicted adducts for comprehensive MS matching
- **Cosine Similarity**: Measures spectral similarity between predicted and observed MS data

### Assignment Algorithm
- **Weighted Aggregation**: Combines RT, UV, and MS scores into unified compound-peak similarity scores
- **Optimal Assignment**: Uses combinatorial optimization to assign predicted compounds to observed peaks
- **Multi-modal Integration**: Leverages all analytical dimensions (RT, UV, MS) for robust peak identification

## ⚙️ Installation

- Python 3.10+
- Conda

Key Dependencies:
- `mocca2` for chromatogram processing and peak extraction
- `playwright` and `pyppeteer` for ASKCOS and RTPred web server automation
- `chemprop` for UVVisML lambda max prediction model operations
- `pymzml` for mass spectra extraction and data processing
- `scipy` for peak assignment and scoring
- `rdkit` for molecular weight calculation and SMILES processing
- `pandas` and `numpy` for data manipulation and numerical computations

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
