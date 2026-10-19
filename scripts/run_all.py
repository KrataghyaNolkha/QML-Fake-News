from __future__ import annotations

import argparse
import json
import sys
import platform
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import pandas as pd

# Allow running as: python scripts/run_all.py
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from qmlfakenews.report_docx import write_paper_docx


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="Run a reduced/fast set of experiments")
    parser.add_argument("--full", action="store_true", help="Run deeper sweeps (slower)")
    parser.add_argument(
        "--doc-only",
        action="store_true",
        help="Do not rerun experiments; regenerate plots + paper_draft.docx from existing outputs/ tables",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress progress prints")
    parser.add_argument(
        "--data-csv",
        type=str,
        default=None,
        help="Optional path to the dataset CSV (defaults to new_research/data/facebook-fact-check.csv)",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    if args.data_csv:
        data_csv = Path(args.data_csv).expanduser().resolve()
    else:
        # Default location (preferred)
        data_csv = repo_root / "data" / "facebook-fact-check.csv"
        # Backward/alternate location
        if not data_csv.exists():
            alt = repo_root / "facebook-fact-check.csv"
            if alt.exists():
                data_csv = alt
    outputs_dir = repo_root / "outputs"

    if args.doc_only:
        # Reuse existing summary if available; otherwise fall back to empty.
        summary_path = outputs_dir / "summary.json"
        if summary_path.exists():
            try:
                summary = json.loads(summary_path.read_text())
            except Exception:
                summary = {}
        else:
            summary = {}
    else:
        from qmlfakenews.experiments import run_all

        preset = "full" if args.full else "standard"
        summary = run_all(
            data_csv=data_csv,
            outputs_dir=outputs_dir,
            seed=42,
            quick=bool(args.quick),
            preset=preset,
            verbose=not bool(args.quiet),
        )
        def package_version(name: str) -> str | None:
            try:
                return version(name)
            except PackageNotFoundError:
                return None

        run_manifest = {
            "dataset_path": str(data_csv),
            "dataset_samples": summary.get("n_samples"),
            "random_seed_main": 42,
            "split": {"test_size": 0.25, "stratified": True},
            "preprocessing": {
                "drop_columns": ["Debate", "account_id", "post_id", "Post URL"],
                "missing_values": {"share_count": "fill with 0", "reaction_count": "drop row", "comment_count": "drop row"},
                "excluded_rating": "no factual content",
                "label_mapping": {"mostly true": 1, "mostly false": -1, "mixture of true and false": -1},
                "categorical_columns": ["Category", "Page", "Date Published", "Post Type"],
                "categorical_encoding": "scikit-learn LabelEncoder applied before the train/test split",
                "pca": "scikit-learn PCA; fit on training split, transform held-out split; random_state=42",
                "quantum_scaling": "MinMaxScaler(feature_range=(0, pi)) fitted after PCA on training split",
                "classical_pca_scaling": "StandardScaler fitted after PCA on training split",
                "qubit_dimension_mismatch": "truncate excess PCA components or zero-pad missing components",
                "engineered_classical_features": "engagement counts; log1p counts and totals; safe count ratios and engagement fractions; publication year/month/day-of-week; top-20 Category and Post Type one-hot indicators with other category",
                "polynomial_classical_features": "degree-2 PolynomialFeatures with include_bias=False",
            },
            "classical_baselines": {
                "logistic_regression": {"max_iter": 5000, "class_weight": "balanced"},
                "random_forest": {"n_estimators": 500, "random_state": 42, "class_weight": "balanced_subsample"},
                "rbf_svc": {"kernel": "rbf", "C": 1.0, "gamma": "scale"},
                "metrics_positive_label": 1,
                "five_fold_cv": "StratifiedKFold(shuffle=True, random_state=42); PCA(2) is fitted before folds, while full-feature scaler is fit within fold pipelines",
            },
            "quantum_implementation": {
                "kernel": "squared state fidelity |<phi(x)|phi(z)>|^2",
                "ideal_backend": "exact Qiskit statevector simulation with cached feature states",
                "feature_maps": {
                    "z": "Qiskit ZFeatureMap",
                    "zz": "Qiskit ZZFeatureMap; linear entanglement",
                    "pauli_xyz": "Qiskit PauliFeatureMap; paulis X,Y,Z; full entanglement",
                    "ry_custom": "one-layer circuit with one RY(theta_i) per qubit; reps does not alter this circuit",
                },
                "pegasos": {"lambda": 0.02, "main_updates": 200 if args.full else (60 if args.quick else 90), "sampling": "one uniform training example per update; seeded NumPy generator; update on margin < 1"},
            },
            "preset": preset,
            "quick": bool(args.quick),
            "pca_components": [2, 3, 4] if args.full else ([2] if args.quick else [2, 3, 4]),
            "qubits": [2, 3, 4] if args.full else ([2] if args.quick else [2, 3]),
            "feature_maps": ["z", "zz", "pauli_xyz", "ry_custom"],
            "repetitions": [1, 2, 4, 6] if args.full else ([2] if args.quick else [1, 2, 3]),
            "pegasos_iterations_main": 200 if args.full else (60 if args.quick else 90),
            "pegasos_lambda": 0.02,
            "geometry_subset_n": 400 if args.full else (200 if args.quick else 250),
            "geometry_sweep": {
                "rows": len(pd.read_csv(outputs_dir / "tables" / "kernel_geometry_performance.csv")),
                "distinct_model_settings": int(pd.read_csv(outputs_dir / "tables" / "kernel_geometry_performance.csv")["correlation_included"].sum()),
                "deduplication_fields": ["feature_map", "reps", "pca_components", "qubits", "pegasos_iterations"],
                "distinct_settings_by_qubits": {str(int(q)): int(n) for q, n in pd.read_csv(outputs_dir / "tables" / "kernel_geometry_performance.csv").query("correlation_included == True").groupby("qubits").size().items()},
                "design": "Feature-map and depth sweeps fix qubits=2; Pauli-XYZ PCA/qubit tradeoff spans 2, 3, and 4 qubits at PCA dimensions 2, 3, and 4.",
            },
            "cross_dataset_scope": {
                "generalization_established": False,
                "breast_cancer": "classification sanity check only; fake-news geometry protocol not replicated",
                "welfake_liar": "excluded from claims and manuscript tables due to conflicting runs and incomplete provenance",
            },
            "seed_sweep_support_counts": {
                "seeds": list(range(10)),
                "split": "stratified 75/25; paired by seed",
                "pca_components": 2,
                "classical_model": "RBF SVC, C=1.0, gamma=scale, on StandardScaler-transformed PCA features",
                "classical_count": "sum of scikit-learn SVC n_support_ across classes",
                "quantum_model": "Pauli-XYZ quantum kernel, 2 qubits, 2 repetitions, Pegasos lambda=0.02, 100 sampled updates",
                "quantum_input_scaling": "MinMaxScaler to [0, pi] after PCA",
                "quantum_count": "distinct training examples added to Pegasos active set after a margin-violating update",
                "count_comparison": "descriptive solver-specific counts only; no ratio, significance test, or efficiency claim",
            },
            "condition_number": "largest positive eigenvalue / smallest positive eigenvalue after centering and diagonal ridge 1e-8",
            "spectral_gap": "largest eigenvalue - second-largest eigenvalue after centering and diagonal ridge 1e-8",
            "noise": {
                "probabilities": [0.0, 0.001, 0.005, 0.01, 0.02] if args.full else ([0.0] if args.quick else [0.0, 0.01, 0.03, 0.05, 0.1]),
                "shots": 512 if args.full else (512 if args.quick else 512),
                "pegasos_iterations": 40 if args.full else (40 if args.quick else 40),
                "stratified_training_subset_n": 60 if args.full else min(60, 200 if args.quick else 250),
                "kernel_statistics_subset_n": 30,
                "test_split": "full held-out test split",
                "simulator": "AerSimulator with depolarizing gate errors",
                "method": "Qiskit ComputeUncompute with BackendSamplerV2",
                "one_qubit_error": "depolarizing_error(p, 1) on rx, ry, rz, x, y, z, h, s, sdg, t, tdg",
                "two_qubit_error": "depolarizing_error(min(1, 2*p), 2) on cx, cz, swap",
                "transpiler_optimization_level": 1,
                "hardware_calibrated": False,
            },
            "software": {
                "python": platform.python_version(),
                "numpy": package_version("numpy"),
                "pandas": package_version("pandas"),
                "scikit_learn": package_version("scikit-learn"),
                "qiskit": package_version("qiskit"),
                "qiskit_machine_learning": package_version("qiskit-machine-learning"),
                "qiskit_aer": package_version("qiskit-aer"),
            },
        }
        (outputs_dir / "run_manifest.json").write_text(json.dumps(run_manifest, indent=2))

    # Load produced tables
    baselines_2d = _safe_read_csv(outputs_dir / "tables" / "baselines_pca2.csv")
    baselines_2d_cv = _safe_read_csv(outputs_dir / "tables" / "baselines_pca2_cv.csv")
    baselines_full = _safe_read_csv(outputs_dir / "tables" / "baselines_full.csv")
    baselines_full_cv = _safe_read_csv(outputs_dir / "tables" / "baselines_full_cv.csv")
    baselines_poly2 = _safe_read_csv(outputs_dir / "tables" / "baselines_poly2_full.csv")
    baselines_engineered = _safe_read_csv(outputs_dir / "tables" / "baselines_engineered_full.csv")
    aux_bc_full = _safe_read_csv(outputs_dir / "tables" / "aux_breastcancer_baselines_full.csv")
    aux_bc_pca2 = _safe_read_csv(outputs_dir / "tables" / "aux_breastcancer_baselines_pca2.csv")
    aux_bc_qmaps = _safe_read_csv(outputs_dir / "tables" / "aux_breastcancer_quantum_featuremaps.csv")
    seed_sweep = _safe_read_csv(outputs_dir / "tables" / "seed_sweep_pca2.csv")
    seed_sweep_summary = _safe_read_csv(outputs_dir / "tables" / "seed_sweep_summary.csv")
    kernel_diagnostics = _safe_read_csv(outputs_dir / "tables" / "kernel_diagnostics.csv")
    geometry_perf = _safe_read_csv(outputs_dir / "tables" / "kernel_geometry_performance.csv")
    geometry_corr = _safe_read_csv(outputs_dir / "tables" / "kernel_geometry_correlations.csv")
    q_featuremaps = _safe_read_csv(outputs_dir / "tables" / "quantum_featuremap_comparison.csv")
    pca_tradeoff = _safe_read_csv(outputs_dir / "tables" / "pca_qubits_tradeoff.csv")
    noise_robustness = _safe_read_csv(outputs_dir / "tables" / "noise_robustness.csv")
    pegasos_convergence = _safe_read_csv(outputs_dir / "tables" / "pegasos_convergence.csv")

    if not args.doc_only:
        from qmlfakenews.plotting import (
            save_accuracy_vs_qubits_plot,
            save_convergence_plot,
            save_geometry_scatter_plots,
            save_noise_plot,
            save_tradeoff_plot,
        )

        fig_dir = outputs_dir / "figures"
        if not pegasos_convergence.empty:
            save_convergence_plot(pegasos_convergence, fig_dir / "pegasos_convergence.png")
        if not pca_tradeoff.empty:
            save_tradeoff_plot(pca_tradeoff, fig_dir / "pca_tradeoff.png")
            save_accuracy_vs_qubits_plot(pca_tradeoff, fig_dir / "accuracy_vs_qubits.png")
        if not noise_robustness.empty:
            save_noise_plot(noise_robustness, fig_dir / "noise_robustness.png")
        if not geometry_perf.empty:
            save_geometry_scatter_plots(geometry_perf, fig_dir)

    headline_results = {
        "Samples": summary.get("n_samples"),
        "Raw features": summary.get("n_features"),
        "Poly(2) features": summary.get("n_features_poly2"),
        "Engineered features": summary.get("n_features_engineered"),
        "PCA(2) explained variance": summary.get("pca2_explained_variance"),
        "Engineered PCA(2) explained variance": summary.get("pca2_engineered_explained_variance"),
    }

    # Paper draft
    write_paper_docx(
        out_path=outputs_dir / "paper_draft.docx",
        headline_results=headline_results,
        baselines_2d=baselines_2d,
        baselines_2d_cv=baselines_2d_cv,
        baselines_full=baselines_full,
        baselines_full_cv=baselines_full_cv,
        baselines_poly2=baselines_poly2,
        baselines_engineered=baselines_engineered,
        aux_breastcancer_baselines_full=aux_bc_full,
        aux_breastcancer_baselines_pca2=aux_bc_pca2,
        aux_breastcancer_quantum_featuremaps=aux_bc_qmaps,
        seed_sweep=seed_sweep,
        seed_sweep_summary=seed_sweep_summary,
        quantum_featuremaps=q_featuremaps,
        kernel_diagnostics=kernel_diagnostics,
        geometry_performance=geometry_perf,
        geometry_correlations=geometry_corr,
        pca_tradeoff=pca_tradeoff,
        noise_robustness=noise_robustness,
        pegasos_convergence=pegasos_convergence,
    )

    (outputs_dir / "summary.json").write_text(json.dumps(summary, indent=2))


def _safe_read_csv(path: Path) -> pd.DataFrame:
    try:
        if path.exists():
            return pd.read_csv(path)
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


if __name__ == "__main__":
    main()
