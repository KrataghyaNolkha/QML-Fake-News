import sys
from pathlib import Path
import numpy as np
import pandas as pd

# Allow running as: python scripts/generate_variance.py
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from qmlfakenews.quantum_kernel import QuantumKernelFactory
from qmlfakenews.diagnostics import kernel_target_alignment, spectrum_stats

def main():
    print("Loading data...")
    data_dir = repo_root / "data"
    outputs_dir = repo_root / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    (outputs_dir / "tables").mkdir(exist_ok=True)

    from qmlfakenews.data import load_facebook_factcheck_csv, engineer_facebook_factcheck_features, make_train_test_split
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    
    df = load_facebook_factcheck_csv(data_dir / "facebook-fact-check.csv")
    X, y, feature_names = engineer_facebook_factcheck_features(df)
    
    X = StandardScaler().fit_transform(X)
    X = PCA(n_components=2, random_state=42).fit_transform(X)
    
    split = make_train_test_split(X, y, ["PC1", "PC2"], test_size=0.2, random_seed=42)

    print("Evaluating Pauli-XYZ Gram Matrix for N=250...")
    factory = QuantumKernelFactory("pauli_xyz", num_qubits=2, reps=2)
    kernel = factory.build()

    np.random.seed(42)
    diag_idx = np.random.choice(len(split.X_train), size=250, replace=False)
    X_diag = split.X_train[diag_idx]
    y_diag = split.y_train[diag_idx]

    K = np.asarray(kernel.evaluate(x_vec=X_diag, y_vec=X_diag), dtype=float)

    print("Computing subsets...")
    variance_rows = []
    subset_sizes = [100, 150, 200, 250]
    num_trials = 5

    for size in subset_sizes:
        for trial in range(num_trials if size < 250 else 1):
            if size == 250:
                idx = np.arange(250)
            else:
                idx = np.random.choice(250, size=size, replace=False)
            
            K_sub = K[idx][:, idx]
            y_sub = y_diag[idx]
            
            align = kernel_target_alignment(K_sub, y_sub, centered=True)
            spec = spectrum_stats(K_sub, centered=True)
            
            variance_rows.append({
                "subset_size": size,
                "trial": trial,
                "kernel_alignment": align,
                "condition_number": spec.condition_number,
                "spectral_gap": spec.spectral_gap
            })

    var_df = pd.DataFrame(variance_rows)
    var_df.to_csv(outputs_dir / "tables" / "diagnostic_variance.csv", index=False)
    print("Done! Saved to diagnostic_variance.csv")

if __name__ == "__main__":
    main()
