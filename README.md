# Geometry-Aware Analysis of Quantum Kernels for Fake News Detection

This repository contains the implementation framework, experimental logs, and high-resolution results for the paper "Geometry-Aware Analysis of Quantum Kernels for Fake News Detection." The project focuses on the mechanistic interpretation of Quantum Machine Learning (QML) models, specifically analyzing how kernel geometry governs performance.

## Project Summary

We investigate quantum-kernel SVMs using the Pegasos algorithm for fake news detection. Our analysis goes beyond headline accuracy to study:
- **Kernel Geometry Diagnostics**: Label alignment, spectral gaps, and condition numbers.
- **Sparsity Advantage**: Demonstrating that quantum kernels achieve comparable accuracy with ~25x fewer support vectors than classical RBF baselines.
- **NISQ Robustness**: Evaluating performance under depolarizing noise models.
- **Cross-Dataset Validation**: Results on Facebook engagement metadata, WELFake, and LIAR datasets.

## Repository Structure

- **`qmlfakenews/`**: Core Python library containing implementations for quantum feature maps, Pegasos optimizer, kernel diagnostics, and data preprocessing.
- **`scripts/`**: The execution scripts for the pipeline.
  - `run_all.py`: The central execution script for running experiments, generating tables, and creating the Word document (`paper_draft.docx`).
  - `generate_variance.py`: Utility to compute quantum diagnostic variances across data subsets.
  - `verify_results.py`: Independent script to cross-check regression and correlation statistics.
  - `extract_nb.py`: Utility to reliably extract empirical metrics from research notebooks.
- **`outputs/`**: Contains raw empirical results in CSV format, including seed sweeps and noise robustness profiles.
  - `high_res_figures/`: Publication-ready, 300 DPI scatter plots and line charts showcasing geometric correlations.
- **`notebooks/`**: Original exploratory Jupyter notebooks (`pvqc_*.ipynb`) used for initial sweeps and algorithm prototyping.
- **`data/`**: Directory for datasets (e.g. `facebook-fact-check.csv`).

## Key Results
- **Geometric Correlation**: Confirmed that Gram matrix conditioning is a stronger predictor of stability than alignment alone.
- **Support Vector Sparsity**: Pegasos-driven quantum models utilized significantly fewer samples for the decision boundary, implying more efficient inference in resource-constrained environments.
- **Noise Profiles**: Detailed mapping of accuracy vs. depolarizing noise, showing kernel-level degradation trajectories.

---
*Note: This repository is intended for code and result sharing. Proprietary manuscript drafts and LaTeX source files are excluded.*
