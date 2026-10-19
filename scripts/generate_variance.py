from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit


repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from qmlfakenews.data import load_facebook_factcheck_csv, make_train_test_split, preprocess_facebook_factcheck
from qmlfakenews.diagnostics import kernel_target_alignment, spectrum_stats
from qmlfakenews.preprocess import fit_transform_pca, pad_or_trim_features
from qmlfakenews.quantum_kernel import QuantumKernelFactory


def main() -> None:
    data_csv = repo_root / "data" / "facebook-fact-check.csv"
    outputs_dir = repo_root / "outputs"
    tables_dir = outputs_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading data from {data_csv}...")
    df = load_facebook_factcheck_csv(data_csv)
    X, y, feature_names = preprocess_facebook_factcheck(df)
    split = make_train_test_split(X, y, feature_names, test_size=0.25, random_seed=42)

    # Match the paper's full-preset geometry pool and quantum preprocessing.
    pca_q = fit_transform_pca(split.X_train, split.X_test, n_components=2, for_quantum=True)
    Xq_train = pad_or_trim_features(pca_q.X_train, 2)
    pool_n = min(400, len(Xq_train))
    subset_sizes = (100, 150, 200, 250)
    if pool_n < max(subset_sizes):
        raise ValueError(f"Need at least {max(subset_sizes)} training examples; found {pool_n}.")

    pool_splitter = StratifiedShuffleSplit(n_splits=1, train_size=pool_n, random_state=42)
    pool_idx, _ = next(pool_splitter.split(Xq_train, split.y_train))
    X_pool = Xq_train[pool_idx]
    y_pool = split.y_train[pool_idx]

    print(f"Evaluating Pauli-XYZ Gram matrix for a stratified pool of n={pool_n}...")
    kernel = QuantumKernelFactory("pauli_xyz", num_qubits=2, reps=2, seed=42).build()
    K_pool = np.asarray(kernel.evaluate(x_vec=X_pool, y_vec=X_pool), dtype=float)

    print("Computing five random subsets for each size...")
    rng = np.random.default_rng(42)
    rows: list[dict[str, float | int]] = []
    for size in subset_sizes:
        for trial in range(5):
            idx = rng.choice(pool_n, size=size, replace=False)
            K_sub = K_pool[np.ix_(idx, idx)]
            y_sub = y_pool[idx]
            spec = spectrum_stats(K_sub, centered=True)
            rows.append(
                {
                    "subset_size": size,
                    "trial": trial,
                    "pool_size": pool_n,
                    "kernel_alignment": kernel_target_alignment(K_sub, y_sub, centered=True),
                    "condition_number": spec.condition_number,
                    "spectral_gap": spec.spectral_gap,
                }
            )

    out_path = tables_dir / "diagnostic_variance.csv"
    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(f"Saved {len(rows)} trials to {out_path}.")


if __name__ == "__main__":
    main()
