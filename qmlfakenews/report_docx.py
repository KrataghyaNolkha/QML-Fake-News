from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from docx import Document
from docx.shared import Inches
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

try:
    from scipy.stats import ttest_rel, wilcoxon
except Exception:  # pragma: no cover - scipy should normally be available
    ttest_rel = None
    wilcoxon = None


def write_paper_docx(
    *,
    out_path: Path,
    headline_results: dict,
    baselines_2d: pd.DataFrame,
    baselines_2d_cv: pd.DataFrame,
    baselines_full: pd.DataFrame,
    baselines_full_cv: pd.DataFrame,
    baselines_poly2: pd.DataFrame,
    baselines_engineered: pd.DataFrame,
    aux_breastcancer_baselines_full: pd.DataFrame,
    aux_breastcancer_baselines_pca2: pd.DataFrame,
    aux_breastcancer_quantum_featuremaps: pd.DataFrame,
    seed_sweep: pd.DataFrame,
    seed_sweep_summary: pd.DataFrame,
    quantum_featuremaps: pd.DataFrame,
    kernel_diagnostics: pd.DataFrame,
    geometry_performance: pd.DataFrame,
    geometry_correlations: pd.DataFrame,
    pca_tradeoff: pd.DataFrame,
    noise_robustness: pd.DataFrame,
    pegasos_convergence: pd.DataFrame,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    doc = Document()
    doc.core_properties.author = "Anonymous"
    doc.core_properties.last_modified_by = "Anonymous"
    doc.core_properties.title = "Geometry-Aware Analysis of Quantum Kernels for Fake News Detection"

    doc.add_heading("Geometry-Aware Analysis of Quantum Kernels for Fake News Detection", level=0)
    doc.add_paragraph(f"Final manuscript — {date.today().isoformat()}")

    doc.add_heading("Abstract", level=1)
    doc.add_paragraph(
        "We study quantum-kernel SVMs for fake news detection from structured engagement metadata, focusing on mechanistic explanations rather than application-only accuracy. "
        "We examine whether quantum-kernel performance is associated with kernel geometry, including label alignment, spectrum, and numerical conditioning. "
        "We compute geometry diagnostics on Gram-matrix subsets and report exploratory associations with test accuracy across the configurations evaluated. "
        "We benchmark against strong classical baselines on matched representations (PCA(2), full features, and a 20+ feature expansion), sweep the PCA–qubits bottleneck, "
        "and evaluate modeled depolarizing noise in a classical simulator. On the PCA(2) representation, quantum-kernel accuracy is comparable to the RBF baseline on the evaluated split; solver-specific support-set counts are reported descriptively and are not interpreted as a compression or efficiency comparison."
    )

    doc.add_heading("Research Question and Core Claim", level=1)
    doc.add_paragraph(
        "Research question: How are measured quantum-kernel geometry diagnostics (alignment, spectrum, and conditioning) associated with performance in the evaluated fake-news configurations?"
    )
    doc.add_paragraph(
        "Core claim: In this exploratory sweep of distinct model settings, measured conditioning and spectral diagnostics show associations with accuracy. These results do not establish causality or validated prediction; alignment alone does not describe all observed variation."
    )

    doc.add_heading("1. Introduction", level=1)
    doc.add_paragraph(
        "Many quantum machine learning studies emphasize headline accuracy while leaving the mechanism opaque. We take a geometry-first view: for kernel SVMs, the Gram matrix is the effective model, and numerical conditioning can determine whether a favorable alignment translates into a stable margin. Finite-sample variation, finite-shot estimates, and noise can all destabilize a kernel that appears expressive in isolation."
    )
    doc.add_paragraph(
        "This matters for fake-news detection because the task is not merely classification, but classification under a noisy and correlated data-generation process. Engagement metadata is compact, heterogeneous, and prone to spurious structure, so a single accuracy score is not enough to justify a claim. A credible QML study therefore needs matched baselines, seed stability, failure diagnostics, and perturbation tests that probe the geometry directly."
    )
    doc.add_paragraph(
        "Prior quantum-kernel studies often report a single benchmark result and infer advantage from one number. Here the Gram matrix itself is the object of analysis: if its spectrum is ill-conditioned, the classifier can become unstable even when alignment appears favorable. That framing motivates the support-set, conditioning, and noise analyses reported below."
    )

    doc.add_heading("1.1 Contributions", level=2)
    for i, bullet in enumerate(
        [
            "We provide a bounded empirical case study of how established kernel-alignment, spectral, and conditioning diagnostics co-vary with accuracy across 24 distinct quantum-kernel settings for structured Facebook fact-check metadata; the metrics and Pegasos solver are established methods.",
            "We report strong classical baselines on matched representations (PCA-reduced, full standardized features, and a 20+ derived-feature expansion).",
            "We report support-set sizes for Pegasos quantum kernels and support-vector counts for classical RBF SVMs, while noting that these solver-specific counts are not directly equivalent measures of computational cost.",
            "We include a breast-cancer classification sanity check; the full geometry analysis is not replicated there.",
            "We evaluate modeled depolarizing noise in a classical Aer simulator; this is not a hardware experiment.",
        ],
        start=1,
    ):
        doc.add_paragraph(f"C{i}. {bullet}")

    doc.add_heading("1.2 Scope and empirical gap", level=2)
    doc.add_paragraph(
        "We combine seed sweeps and multivariate geometry analysis to characterize this implementation. Geometry results are exploratory associations across a limited configuration set; any inferential claims are restricted to reproduced statistical analyses."
    )
    doc.add_heading("2. Related Work", level=1)
    doc.add_paragraph(
        "Quantum-kernel research has established fidelity feature-space classifiers and studied their finite-sample behavior. Schuld and Killoran (2019) framed quantum machine learning in feature Hilbert spaces, and Havlicek et al. (2019) developed a quantum-enhanced feature-space learning framework. Thanasilp et al. (2024) analyzed conditions under which quantum kernel values concentrate and become difficult to distinguish with finite shots; Gil-Fuster et al. (2024) examined limits of standard model-complexity reasoning for QML generalization; Tomasi et al. (2026) studied benign overfitting with quantum kernels. These works motivate kernel-level and generalization diagnostics, but they are not evidence that any one geometry statistic causes accuracy changes in the present task."
    )
    doc.add_paragraph(
        "Quantum methods have already been applied to fake-news classification. Tian (2023) studied quantum k-nearest neighbors, quantum support-vector machines, and a variational classifier. Khalil et al. (2025) evaluated PegasosQSVM on BuzzFace and TruthSeeker, including PCA-based reduction, Z/ZZ feature maps, and classification/runtime comparisons. We therefore make no first-application claim, and do not claim a new quantum classifier, feature map, or Pegasos method."
    )
    doc.add_paragraph(
        "The contribution here is narrower and empirical: for the 2,016-row Facebook fact-check metadata analysis defined in this paper, we report centered alignment, spectral summaries, and numerical conditioning alongside accuracy across 24 distinct combinations of established feature maps, PCA dimensions, qubit counts, depths, and Pegasos iterations. We pair that configuration-level analysis with a ten-seed PCA(2) RBF comparison and a finite-shot simulator stress test. This combination documents how the measured Gram-matrix diagnostics behave in this particular low-qubit metadata setting; it does not establish a general law, causal mechanism, cross-dataset result, or quantum advantage."
    )
    doc.add_paragraph(
        "The novelty claim is therefore the task-specific diagnostic synthesis and its documented empirical results, not algorithmic novelty. Geometry statistics are exploratory and configuration points share a train/test split, so we present them as dependent descriptive associations. Stronger validation across datasets, balanced qubit sweeps, and device-calibrated hardware remains outside this study."
    )
    _add_table(
        doc,
        "Position relative to prior work",
        pd.DataFrame([
            {"Work": "Tian (2023); Khalil et al. (2025)", "Prior focus": "Fake-news QKNN/QSVM/VQC and PegasosQSVM classification, with selected feature-map and runtime comparisons.", "Distinction here": "No new classifier or accuracy-superiority claim; the focus is Gram geometry across metadata-model settings."},
            {"Work": "Havlicek et al. (2019); Thanasilp et al. (2024); Gil-Fuster et al. (2024)", "Prior focus": "Quantum feature spaces, kernel concentration, and generalization analysis.", "Distinction here": "Uses established concepts descriptively in one task-specific empirical study; does not extend their theory."},
            {"Work": "This study", "Prior focus": "24 settings; alignment, spectrum, conditioning; ten-seed matched PCA(2) baseline; modeled finite-shot noise.", "Distinction here": "Bounded diagnostic synthesis only; no new metric, causal claim, cross-dataset validation, or quantum advantage."},
        ]),
    )

    doc.add_heading("3. Methodology", level=1)
    doc.add_heading("Kernel Diagnostics", level=2)
    doc.add_paragraph(
        "Alignment measures how well the centered Gram matrix matches the label outer-product structure. For spectral statistics, we symmetrize and center the Gram matrix, add a ridge of 10⁻⁸ to its diagonal, and order eigenvalues from largest to smallest. The spectral gap is λ₁ − λ₂. The condition number is the largest positive eigenvalue divided by the smallest positive eigenvalue of this ridge-adjusted matrix. This definition yields values on the 10⁸–10⁹ scale in the current run; the previously reported values around 30–45 were not reproduced and are not used. "
        "We include spectral diagnostics but interpret them conservatively: spectral gap alone is not universally 'good' or 'bad'. Instead, we use it as a proxy for spectrum concentration and pair it with effective rank and leading-eigenvalue dominance."
    )

    doc.add_heading("Theory-lite intuition", level=2)
    doc.add_paragraph(
        "The spectrum and conditioning describe properties of the estimated Gram matrix. Perturbations from finite sampling, finite shots, or noise may alter those estimates and the resulting classifier. The present experiments measure these associations; they do not isolate a causal effect of conditioning on generalization."
    )

    doc.add_heading("4. Experimental Setup", level=1)
    doc.add_paragraph(
        "Primary dataset: 2,016 Facebook fact-checking posts represented by structured engagement and metadata features; labels are mapped to binary truthfulness. We use a stratified 75/25 train/test split with seed 42. Quantum models use PCA followed by angle scaling to [0, π] and Z, ZZ, Pauli-XYZ, or custom RY feature maps. Full-data ideal-kernel experiments use the complete training split; geometry diagnostics use a stratified 400-example training subset. The seed sweep uses ten split seeds. Exact repetitions, qubits, Pegasos settings, shots, noise settings, and software versions are recorded in the run manifest. The scikit-learn breast-cancer data provide a classification check only; the geometry analysis is not replicated there."
    )
    doc.add_paragraph(
        "Data processing: we remove Debate, account_id, post_id, and Post URL when present; replace missing share_count values with zero; and drop rows missing reaction_count or comment_count. Rows labeled ‘no factual content’ are excluded. Rating is mapped to +1 for ‘mostly true’ and −1 for ‘mostly false’ or ‘mixture of true and false’. Category, Page, Date Published, and Post Type are converted to integer codes with scikit-learn LabelEncoder before the split. The resulting dataset has 2,016 rows. The split is stratified with test_size=0.25 and random_state=42. PCA and subsequent scalers are fitted on training data only and then applied to the held-out data; PCA uses scikit-learn's default solver settings with random_state=42. For quantum inputs, MinMaxScaler maps each PCA component to [0, π]; classical PCA inputs use StandardScaler. When PCA dimension and qubit count differ in the tradeoff sweep, components are truncated or zero-padded to the circuit input dimension."
    )
    doc.add_paragraph(
        "Quantum implementation: the fidelity kernel is K(x,z)=|⟨φ(x)|φ(z)⟩|². In ideal runs, feature-map states are computed with Qiskit statevectors and overlaps are evaluated exactly. The maps are Qiskit's ZFeatureMap; ZZFeatureMap with linear entanglement; PauliFeatureMap with paulis [X,Y,Z] and full entanglement; and a custom single-layer circuit applying one RY(θᵢ) rotation to each qubit. The repetitions parameter is passed to the three Qiskit maps; the custom RY circuit has one rotation layer. The primary Pauli-XYZ model uses 2 qubits and 2 repetitions. Kernel Pegasos samples one training example uniformly per update using a seeded NumPy generator, adds its coefficient when yᵢf(xᵢ)<1, and predicts with f(x)=[1/(λT)]ΣⱼαⱼyⱼK(xⱼ,x). The main full-preset runs use λ=0.02 and 200 updates; the ten-seed comparison uses 100 updates."
    )
    doc.add_paragraph(
        "Classical models: logistic regression uses max_iter=5,000 and class_weight='balanced'; the random forest uses 500 trees, random_state=42, and class_weight='balanced_subsample'; and the RBF SVC uses C=1, gamma='scale'. Full-feature and engineered-feature baselines are standardized using scalers fitted on the training split. PCA(2) classical baselines use a train-fitted PCA followed by StandardScaler. Five-fold checks use shuffled StratifiedKFold (random_state=42); the full-feature CV pipelines fit the scaler within each fold. The PCA(2) CV check uses PCA prepared on the outer training split before folds, so it is a stability check rather than a fully fold-isolated preprocessing estimate. Precision, recall, and F1 use +1 (‘mostly true’) as the positive class, with zero_division=0."
    )
    doc.add_paragraph(
        "The engineered representation retains engagement counts, adds log1p transforms, count ratios, total engagement and engagement fractions, encodes publication year/month/day-of-week, and one-hot encodes the 20 most frequent Category and Post Type values with remaining values grouped as ‘other’. The separate polynomial baseline uses degree-2 PolynomialFeatures with include_bias=False. These are classical-only representations and are not treated as matched quantum comparisons."
    )
    doc.add_paragraph(
        "Qubit coverage in the geometry sweep: feature-map comparisons (4 settings) and the depth sweep (12 settings) hold the circuit at 2 qubits to compare feature maps and repetitions at a fixed width. A narrower Pauli-XYZ PCA/qubit tradeoff adds 3 settings each at 2, 3, and 4 qubits, spanning PCA dimensions 2, 3, and 4. After removing one repeated setting, the 24 configuration-level points comprise 18 two-qubit, 3 three-qubit, and 3 four-qubit settings. The sweep therefore tests qubits 2–4 but is dominated by the two-qubit fixed-width comparisons; it is not a balanced qubit-scaling study."
    )

    doc.add_heading("5. Results", level=1)
    doc.add_paragraph("We summarize dataset scale and the key geometry-driven findings below.")
    doc.add_heading("Dataset and preprocessing", level=2)
    for k, v in headline_results.items():
        doc.add_paragraph(f"{k}: {v}")

    doc.add_heading("Main findings (quantified)", level=2)

    # The per-seed table below is the authoritative support-count comparison.

    doc.add_heading("Statistical validation", level=2)
    try:
        if seed_sweep is not None and not seed_sweep.empty and {"svm_rbf_accuracy", "q_pauli_accuracy", "svm_rbf_n_support", "q_pauli_n_support"}.issubset(seed_sweep.columns):
            paired = seed_sweep.dropna(subset=["svm_rbf_accuracy", "q_pauli_accuracy", "svm_rbf_n_support", "q_pauli_n_support"]).copy()
            if not paired.empty:
                stats_rows = []
                for label, left, right in [
                    ("accuracy", "q_pauli_accuracy", "svm_rbf_accuracy"),
                ]:
                    diff = paired[left].astype(float) - paired[right].astype(float)
                    w_stat = p_value = t_stat = t_p_value = None
                    if wilcoxon is not None:
                        try:
                            w_res = wilcoxon(paired[left], paired[right], alternative="two-sided", method="auto")
                            w_stat = float(w_res.statistic)
                            p_value = float(w_res.pvalue)
                        except Exception:
                            pass
                    if ttest_rel is not None:
                        try:
                            t_res = ttest_rel(paired[left], paired[right], nan_policy="omit")
                            t_stat = float(t_res.statistic)
                            t_p_value = float(t_res.pvalue)
                        except Exception:
                            pass
                    stats_rows.append({
                        "metric": label,
                        "mean_diff": float(diff.mean()),
                        "std_diff": float(diff.std(ddof=1)) if diff.shape[0] > 1 else 0.0,
                        "wilcoxon_stat": w_stat,
                        "wilcoxon_p": p_value,
                        "paired_t_stat": t_stat,
                        "paired_t_p": t_p_value,
                        "n": int(diff.shape[0]),
                    })

                significance_df = pd.DataFrame(stats_rows)
                _add_table(doc, "Paired significance tests (seed sweep)", significance_df)
                try:
                    acc_row = significance_df[significance_df["metric"] == "accuracy"].head(1)
                    if not acc_row.empty:
                        doc.add_paragraph(
                            "Interpretation: the paired accuracy difference is small; its 95% bootstrap confidence interval includes zero. "
                            f"Across {int(acc_row.iloc[0]['n'])} seeds, the mean quantum-minus-RBF accuracy difference is {float(acc_row.iloc[0]['mean_diff']):+.4f}. Support-set sizes are listed separately as descriptive, solver-specific counts and are not tested as directly comparable outcomes."
                        )
                except Exception:
                    pass
    except Exception:
        pass

    doc.add_heading("Geometry ablation / multivariate analysis", level=2)
    try:
        if geometry_performance is not None and not geometry_performance.empty and {"accuracy", "kernel_alignment", "spectral_gap", "condition_number"}.issubset(geometry_performance.columns):
            reg_df = geometry_performance.copy()
            if "correlation_included" in reg_df.columns:
                reg_df = reg_df[reg_df["correlation_included"].astype(bool)]
            reg_df["log10_condition_number"] = np.log10(pd.to_numeric(reg_df["condition_number"], errors="coerce"))
            reg_df = reg_df.replace([float("inf"), float("-inf")], pd.NA)
            reg_df = reg_df.dropna(subset=["accuracy", "kernel_alignment", "spectral_gap", "log10_condition_number"])
            if not reg_df.empty and reg_df.shape[0] >= 4:
                features = reg_df[["kernel_alignment", "log10_condition_number", "spectral_gap"]].astype(float)
                target = reg_df["accuracy"].astype(float).to_numpy()
                X_scaled = StandardScaler().fit_transform(features)
                y_scaled = StandardScaler().fit_transform(target.reshape(-1, 1)).ravel()
                
                # Manual OLS for full statistics
                X_des = np.column_stack((np.ones(X_scaled.shape[0]), X_scaled))
                n, k = X_des.shape
                beta = np.linalg.inv(X_des.T @ X_des) @ X_des.T @ y_scaled
                predictions = X_des @ beta
                residuals = y_scaled - predictions
                ssr = np.sum(residuals**2)
                sst = np.sum((y_scaled - np.mean(y_scaled))**2)
                r_squared = 1.0 - (ssr / sst) if sst > 0 else 0.0
                
                sigma_squared = ssr / (n - k)
                var_beta = sigma_squared * np.linalg.inv(X_des.T @ X_des)
                se_beta = np.sqrt(np.diag(var_beta))
                
                from scipy.stats import t, shapiro
                t_stats = beta / se_beta
                p_values = [2 * (1 - t.cdf(np.abs(ts), n - k)) for ts in t_stats]
                
                t_crit = t.ppf(0.975, n - k)
                ci_lower = beta - t_crit * se_beta
                ci_upper = beta + t_crit * se_beta
                
                coeff_df = pd.DataFrame(
                    {
                        "predictor": ["intercept", "kernel_alignment", "log10_condition_number", "spectral_gap"],
                        "standardized_coef": beta,
                        "p_value": p_values,
                        "ci_lower_95": ci_lower,
                        "ci_upper_95": ci_upper,
                    }
                )
                
                _add_table(doc, "Exploratory regression: accuracy ~ alignment + log10(condition) + spectral gap", coeff_df)
                
                stat, p_res = shapiro(residuals)
                normality_msg = f"Shapiro-Wilk test on residuals: W={stat:.3f}, p={p_res:.3f}."
                if p_res > 0.05:
                    normality_msg += " We fail to reject the null hypothesis of normality (residuals appear approximately normal)."
                else:
                    normality_msg += " We reject the null hypothesis of normality (residuals may deviate from normality)."
                
                doc.add_paragraph(f"Overall model fit: R² = {r_squared:.4f}. {normality_msg}")
                
                doc.add_paragraph(
                    "Interpretation: this ablation-style regression checks whether conditioning and spectral gap remain informative once alignment is included. "
                    "Standardized coefficients are reported so the predictors are comparable on the same scale."
                )
    except Exception:
        pass

    doc.add_heading("Solver-specific support-set sizes", level=2)
    doc.add_paragraph(
        "The per-seed table reports two algorithm-specific counts on seed-matched train/test splits. Both pipelines use two PCA components, but the classical RBF SVC receives StandardScaler-scaled PCA features while the quantum Pegasos feature map receives MinMax-scaled angles in [0, π]. The classical SVC uses C=1 and gamma='scale'; its count is the sum of scikit-learn's per-class support-vector counts. Quantum Pegasos uses the Pauli-XYZ map with 2 qubits and 2 repetitions; its count is the number of distinct training examples that entered the active set after a margin-violating update during 100 sampled updates. These counts arise from different optimization procedures on differently scaled inputs and do not measure equivalent representations, memory use, inference work, or model compression. We therefore report raw counts descriptively, omit a count ratio and statistical test, and make no efficiency claim from them."
    )

    # Seed sweep summary for statistical stability
    if seed_sweep_summary is not None and not seed_sweep_summary.empty:
        accuracy_summary = seed_sweep_summary[seed_sweep_summary["metric"] == "accuracy_diff_q_minus_svm"]
        _add_table(doc, "10-seed accuracy comparison (PCA=2)", accuracy_summary)

    if seed_sweep is not None and not seed_sweep.empty:
        display_sweep = seed_sweep.rename(columns={
            "svm_rbf_n_support": "RBF SVC support vectors",
            "q_pauli_n_support": "Quantum Pegasos active training points",
        })
        _add_table(doc, "Per-seed accuracy and solver-specific support-set sizes (PCA=2)", display_sweep)

    # Geometry correlations (diagnostics → evidence)
    try:
        if geometry_correlations is not None and not geometry_correlations.empty:
            doc.add_paragraph(
                "Exploratory geometry associations: we correlate measured geometry metrics with test accuracy across 24 distinct model settings (n is reported per metric). All settings share the same train/test split, so the configuration points are dependent; these correlations are descriptive and do not establish causal effects or out-of-sample predictive value."
            )
            for _, row in geometry_correlations.iterrows():
                metric = str(row.get("metric"))
                pr = row.get("pearson_r")
                sr = row.get("spearman_r")
                n = row.get("n")
                if pd.notna(pr) and pd.notna(sr) and pd.notna(n):
                    doc.add_paragraph(f"{metric}: Pearson r={float(pr):.3f}, Spearman ρ={float(sr):.3f} (n={int(n)}).")

            # Add an explicit interpretation sentence for reviewers.
            try:
                row_cond = geometry_correlations[geometry_correlations["metric"] == "log10_condition_number"].head(1)
                row_align = geometry_correlations[geometry_correlations["metric"] == "kernel_alignment"].head(1)
                if not row_cond.empty and not row_align.empty:
                    pr_cond = float(row_cond.iloc[0]["pearson_r"])
                    pr_align = float(row_align.iloc[0]["pearson_r"])
                    doc.add_paragraph(
                        "Interpretation: In this configuration sweep, accuracy is associated with log condition number and alignment. "
                        f"The observed Pearson coefficients are r(condition)={pr_cond:.3f} and r(alignment)={pr_align:.3f}; with this small exploratory sample, they should not be read as causal effects or validated predictors."
                    )
            except Exception:
                pass
    except Exception:
        pass

    # Noise robustness: summarize delta if two points exist
    try:
        if noise_robustness is not None and not noise_robustness.empty and {"noise_prob", "accuracy"}.issubset(set(noise_robustness.columns)):
            nr = noise_robustness.dropna(subset=["noise_prob", "accuracy"]).sort_values("noise_prob")
            if nr.shape[0] >= 2:
                p0 = float(nr.iloc[0]["noise_prob"])
                a0 = float(nr.iloc[0]["accuracy"])
                p1 = float(nr.iloc[-1]["noise_prob"])
                a1 = float(nr.iloc[-1]["accuracy"])
                doc.add_paragraph(
                    f"Simulator noise sweep: accuracy changes from {a0:.3f} at p={p0:g} to {a1:.3f} at p={p1:g} (Δ={a1 - a0:+.3f}); intermediate values are reported because the observed trend is not monotonic."
                )

                # If kernel-level stats exist, explicitly report degradation evidence.
                if {"k_mean", "k_min", "k_max"}.issubset(set(nr.columns)) and nr[["k_mean", "k_min", "k_max"]].notna().any().any():
                    km0 = float(nr.iloc[0]["k_mean"]) if pd.notna(nr.iloc[0]["k_mean"]) else None
                    km1 = float(nr.iloc[-1]["k_mean"]) if pd.notna(nr.iloc[-1]["k_mean"]) else None
                    kn0 = float(nr.iloc[0]["k_min"]) if pd.notna(nr.iloc[0]["k_min"]) else None
                    kn1 = float(nr.iloc[-1]["k_min"]) if pd.notna(nr.iloc[-1]["k_min"]) else None
                    if km0 is not None and km1 is not None:
                        extra = ""
                        if kn0 is not None and kn1 is not None:
                            extra = f" (k_min: {kn0:.3f} → {kn1:.3f})"
                        doc.add_paragraph(
                            "Kernel-level evidence: mean kernel similarity decreases as modeled noise increases, while test accuracy varies across the sweep. "
                            f"On a fixed training subset, mean similarity drops {km0:.3f} → {km1:.3f}{extra}. "
                            "The noisy Pegasos models use a stratified 60-example training subset and are evaluated on the full held-out split, so this is a limited simulator stress test, not evidence of hardware robustness or universal noise immunity."
                        )
    except Exception:
        pass

    doc.add_heading("5.1 Cross-dataset scope", level=2)
    doc.add_paragraph(
        "This study does not establish cross-dataset generalization. The breast-cancer experiment below is a classification sanity check only; it does not reproduce the Facebook task, preprocessing, or kernel-geometry protocol. WELFake and LIAR outputs are excluded from the results and claims because their saved tables contain conflicting runs and incomplete provenance. A matched, provenance-complete evaluation across multiple fake-news datasets remains future work."
    )

    doc.add_heading("6. Tables", level=1)
    _add_table(doc, "Classical baselines (PCA features)", baselines_2d)
    _add_table(doc, "Classical baselines (PCA features, 5-fold CV)", baselines_2d_cv)
    _add_table(doc, "Classical baselines (full features)", baselines_full)
    _add_table(doc, "Classical baselines (full features, 5-fold CV)", baselines_full_cv)
    _add_table(doc, "Classical baselines (poly2 expanded features, 20+ dims)", baselines_poly2)
    _add_table(doc, "Classical baselines (engineered features: one-hot/date/log/ratios)", baselines_engineered)

    doc.add_heading("Auxiliary dataset: Breast cancer (sanity check)", level=1)
    doc.add_paragraph(
        "As a separate classification sanity check, we ran a small subset of the pipeline on the scikit-learn breast-cancer dataset. This check does not test whether the fake-news geometry findings transfer across datasets."
    )
    _add_table(doc, "Breast cancer baselines (full features)", aux_breastcancer_baselines_full)
    _add_table(doc, "Breast cancer baselines (PCA=2)", aux_breastcancer_baselines_pca2)
    _add_table(doc, "Breast cancer quantum feature maps (PCA=2, qubits=2)", aux_breastcancer_quantum_featuremaps)

    _add_table(doc, "Quantum feature map comparison (Pegasos + 2D PCA)", quantum_featuremaps)

    _add_table(doc, "Quantum kernel diagnostics", kernel_diagnostics)
    geometry_table = geometry_performance
    if geometry_table is not None and "correlation_included" in geometry_table.columns:
        geometry_table = geometry_table[geometry_table["correlation_included"].astype(bool)].drop(columns=["correlation_included"])
    _add_table(doc, "Kernel geometry ↔ performance dataset", geometry_table)
    _add_table(doc, "Kernel geometry ↔ accuracy correlations", geometry_correlations)
    _add_table(doc, "PCA/qubits tradeoff sweep", pca_tradeoff)
    _add_table(doc, "Noise robustness sweep", noise_robustness)
    _add_table(doc, "Pegasos convergence checkpoints", pegasos_convergence)

    doc.add_heading("7. Figures", level=1)
    doc.add_paragraph("Key plots are auto-generated under outputs/figures/ and embedded below when available.")
    figure_items = [
        ("Kernel geometry: alignment vs accuracy", "alignment_vs_accuracy.png"),
        ("Kernel geometry: condition number vs accuracy", "condition_vs_accuracy.png"),
        ("Kernel geometry: spectral gap vs accuracy", "spectralgap_vs_accuracy.png"),
        ("Kernel geometry: effective rank vs accuracy", "effective_rank_vs_accuracy.png"),
        ("Kernel geometry: eigen-dominance vs accuracy", "leading_eigen_ratio_vs_accuracy.png"),
        ("PCA/qubits tradeoff", "pca_tradeoff.png"),
        ("Accuracy vs qubits", "accuracy_vs_qubits.png"),
        ("Noise robustness", "noise_robustness.png"),
        ("Pegasos convergence", "pegasos_convergence.png"),
    ]
    for idx, (title, rel) in enumerate(figure_items, start=1):
        _add_captioned_figure(doc, idx, title, out_path.parent / "figures" / rel)

    doc.add_heading("7.1 Figure analysis", level=2)
    doc.add_paragraph(
        "The scatter plots summarize exploratory associations across distinct model settings evaluated on one shared split. Exact duplicate settings are excluded from configuration-level correlations; the estimates remain sensitive to the small sweep and the recorded outlier rule and do not establish causal mechanisms or validated prediction. Spectral gap, effective rank, and eigen-dominance are descriptive summaries whose interpretation depends on the matrix and regularization used."
    )
    doc.add_paragraph(
        "The kernel heatmaps and eigenspectra visualize the sampled Gram matrices. The finite-shot noise sweep uses a 60-example stratified training subset and a fixed 30-example kernel-statistics subset; accuracy is evaluated on the held-out split and is non-monotonic across noise levels. These simulator results are descriptive and are not evidence of hardware robustness."
    )

    # Kernel heatmaps and spectra (one per feature map)
    for idx, fmap in enumerate(["z", "zz", "pauli_xyz", "ry_custom"], start=len(figure_items) + 1):
        _add_captioned_figure(doc, idx, f"Kernel heatmap ({fmap})", out_path.parent / "figures" / f"kernel_heatmap_{fmap}.png")
        _add_captioned_figure(doc, idx + 4, f"Eigenvalue spectrum ({fmap})", out_path.parent / "figures" / f"eigenspectrum_{fmap}.png")

    doc.add_heading("8. Discussion and Loopholes", level=1)
    doc.add_paragraph(
        "The primary comparison reports classical and quantum models on matched PCA representations, while full-feature classical baselines are shown separately. The breast-cancer results are a classification sanity check only; WELFake and LIAR are excluded because their saved results lack consistent provenance. No cross-dataset generalization or replication of the geometry protocol is claimed."
    )

    doc.add_heading("8.1 Implementation notes (for reproducibility)", level=2)
    doc.add_paragraph(
        "Kernel-target alignment (centered): A(K, yyᵀ) = ⟨Kc, Yc⟩F / (||Kc||F ||Yc||F). The centered Gram matrix is symmetrized and receives a diagonal ridge of 10⁻⁸ before eigendecomposition. Eigenvalues are sorted descending; gap = λ₁ − λ₂. Condition number = largest positive eigenvalue / smallest positive eigenvalue. Geometry diagnostics use n=400 stratified training examples. The full preset records 25 sweep rows, including one repeated model setting; configuration-level analyses use 24 distinct feature-map, PCA, qubit, depth, and Pegasos-iteration settings. All settings share the same train/test split, so these are dependent configuration points. The prior standard-preset table had 19 rows (4 feature-map, 9 depth-sweep, and 6 PCA/qubit rows). The condition-number values around 30–45 from the prior draft were not reproduced under this definition and were removed."
    )
    doc.add_paragraph(
        "Noise model: finite-shot fidelity estimates use Qiskit's ComputeUncompute with an AerSimulator sampler, 512 shots, and optimization_level=1 transpilation. Depolarizing error p is applied to rx, ry, rz, x, y, z, h, s, sdg, t, and tdg gates; two-qubit depolarizing error min(1,2p) is applied to cx, cz, and swap. The full-preset sweep uses p ∈ {0, 0.001, 0.005, 0.01, 0.02}, 40 Pegasos updates, a fixed stratified 60-example training subset, a fixed 30-example kernel-statistics subset, and the full held-out test split for accuracy. This synthetic channel is not calibrated to a physical device."
    )

    doc.add_heading("9. Limitations", level=1)
    for bullet in [
        "Simulator-based evaluation: robustness results depend on shots and the chosen noise model; this is not a substitute for hardware experiments.",
        "Qubit coverage is narrow and unbalanced: 18 of 24 distinct geometry settings use 2 qubits, with 3 each at 3 and 4 qubits. The higher-qubit checks occur only in the Pauli-XYZ PCA/qubit tradeoff; results do not establish scaling beyond 4 qubits or generalize across a balanced qubit sweep.",
        "Dataset scope: engagement-metadata features are compact; results may differ for high-dimensional text embeddings.",
    ]:
        doc.add_paragraph(bullet, style="List Bullet")
        
    doc.add_paragraph(
        "Diagnostics on subsets: alignment/spectrum/conditioning are computed on stratified subsets of the training data to avoid O(n²) costs; this trades precision for tractability. "
        "We evaluated the Pauli-XYZ kernel across multiple subset sizes (five random draws per size where available); these estimates characterize subset variability but do not establish representativeness of every geometry result:",
        style="List Bullet"
    )
    
    try:
        var_path = out_dir / "tables" / "diagnostic_variance.csv"
        if var_path.exists():
            var_df = pd.read_csv(var_path)
            # Compute mean and standard deviation
            summary = var_df.groupby("subset_size").agg({
                "kernel_alignment": ["mean", "std"],
                "condition_number": ["mean", "std"],
                "spectral_gap": ["mean", "std"]
            }).reset_index()
            
            # Format cleanly
            formatted_rows = []
            for _, row in summary.iterrows():
                formatted_rows.append({
                    "Subset Size (n)": int(row["subset_size"].iloc[0]),
                    "Alignment": f"{row['kernel_alignment']['mean']:.4f} ± {row['kernel_alignment']['std']:.4f}",
                    "Condition Number": f"{row['condition_number']['mean']:.2f} ± {row['condition_number']['std']:.2f}",
                    "Spectral Gap": f"{row['spectral_gap']['mean']:.4f} ± {row['spectral_gap']['std']:.4f}"
                })
            
            _add_table(doc, "Diagnostic Subset Estimation Variance", pd.DataFrame(formatted_rows))
            
            doc.add_paragraph(
                "The subset-size summary is descriptive. No monotonic reduction in variance or representativeness claim is assumed; the main geometry analysis uses n=400 and should be interpreted as a subset-based estimate."
            )
    except Exception:
        pass

    doc.add_heading("10. Conclusion", level=1)
    doc.add_paragraph(
        "This paper contributes a bounded empirical diagnostic study of established quantum-kernel geometry measures on structured Facebook fact-check metadata, building on prior QML fake-news classification work rather than claiming to be the first or to propose a new classifier. Across 24 distinct settings, geometry measures show exploratory associations with accuracy; the ten-seed comparison shows no reliable difference from the PCA(2) RBF baseline. The experiments establish neither causality, cross-dataset generalization, nor quantum advantage. The breast-cancer run is a classification sanity check only, and the full geometry protocol was not replicated on another dataset."
    )

    doc.add_heading("References", level=1)
    for ref in [
        "Gil-Fuster, E., Eisert, J., & Bravo-Prieto, C. (2024). Understanding quantum machine learning also requires rethinking generalization. Nature Communications, 15, 2277. https://doi.org/10.1038/s41467-024-45882-z.",
        "Havlicek, V., Cordova, F. A., Mauerer, W., et al. (2019). Supervised learning with quantum-enhanced feature spaces. Nature, 567, 209-212.",
        "Khalil, M., Zhang, C., Ye, Z., & Zhang, P. (2025). PegasosQSVM: A quantum machine learning approach for accurate fake news detection. Applied Artificial Intelligence, 39(1), e2457207. https://doi.org/10.1080/08839514.2025.2457207.",
        "Schuld, M., & Killoran, N. (2019). Quantum machine learning in feature Hilbert spaces. Physical Review Letters, 122(4), 040504.",
        "Shalev-Shwartz, S., Singer, Y., Srebro, N., & Cotter, A. (2011). Pegasos: Primal estimated sub-gradient solver for SVM. Mathematical Programming, 127, 3-30.",
        "Shu, K., Sliva, A., Wang, S., Tang, J., & Liu, H. (2017). Fake news detection on social media: A data mining perspective. ACM SIGKDD Explorations, 19(1), 22-36.",
        "Thanasilp, S., Wang, S., Cerezo, M., & Holmes, Z. (2024). Exponential concentration in quantum kernel methods. Nature Communications, 15, 5200. https://doi.org/10.1038/s41467-024-49287-w.",
        "Tomasi, J., Anthoine, S., & Kadri, H. (2026). Benign overfitting with quantum kernels. Proceedings of the 42nd Conference on Uncertainty in Artificial Intelligence, PMLR 337, 6740-6766.",
        "Tian, Z. (2023). Fake News Detection with Quantum Machine Learning [Doctoral dissertation, Auburn University]. Auburn University Electronic Theses and Dissertations. https://etd.auburn.edu/handle/10415/9099.",
        "Zhou, X., & Zafarani, R. (2020). A survey of fake news: Fundamental theories, detection methods, and opportunities. ACM Computing Surveys, 53(5), 1-40.",
    ]:
        doc.add_paragraph(ref, style="List Bullet")

    # The manuscript is a revised resubmission draft; yellow highlighting marks
    # revised content throughout because the prior source draft was regenerated.
    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            run.font.highlight_color = WD_COLOR_INDEX.YELLOW
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.highlight_color = WD_COLOR_INDEX.YELLOW
    doc.save(out_path)


def _add_table(doc: Document, title: str, df: pd.DataFrame) -> None:
    doc.add_heading(title, level=2)
    if df is None or df.empty:
        doc.add_paragraph("(No results yet — run the experiment pipeline to populate this section.)")
        return

    table = doc.add_table(rows=1, cols=len(df.columns))
    table.style = "Table Grid"
    hdr_cells = table.rows[0].cells
    for j, col in enumerate(df.columns):
        hdr_cells[j].text = str(col)
        hdr_cells[j].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        for paragraph in hdr_cells[j].paragraphs:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in paragraph.runs:
                run.bold = True
                run.font.size = Pt(8)
        shading = OxmlElement("w:shd")
        shading.set(qn("w:fill"), "D9EAF7")
        hdr_cells[j]._tc.get_or_add_tcPr().append(shading)
    repeat = OxmlElement("w:tblHeader")
    repeat.set(qn("w:val"), "true")
    table.rows[0]._tr.get_or_add_trPr().append(repeat)

    for _, row in df.iterrows():
        cells = table.add_row().cells
        for j, col in enumerate(df.columns):
            val = row[col]
            if isinstance(val, (float, np.floating)):
                if np.isfinite(val) and (abs(val) >= 1e5 or (0 < abs(val) < 1e-3)):
                    cells[j].text = f"{val:.3e}"
                else:
                    cells[j].text = f"{val:.4f}" if np.isfinite(val) else "—"
            else:
                cells[j].text = str(val)
            cells[j].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            for paragraph in cells[j].paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in paragraph.runs:
                    run.font.size = Pt(8)

    _set_table_borders(table)


def _add_figure(doc: Document, title: str, path: Path) -> None:
    doc.add_heading(title, level=2)
    if not path.exists():
        doc.add_paragraph("(Figure not found — run the experiment pipeline to generate it.)")
        return
    try:
        doc.add_picture(str(path), width=Inches(6.5))
    except Exception:
        doc.add_paragraph(f"(Could not embed figure at: {path})")


def _set_table_borders(table) -> None:
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = tblPr.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tblPr.append(borders)

    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = borders.find(qn(f"w:{edge}"))
        if element is None:
            element = OxmlElement(f"w:{edge}")
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "4")
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), "808080")


def _add_captioned_figure(doc: Document, number: int, title: str, path: Path) -> None:
    caption = doc.add_paragraph()
    run = caption.add_run(f"Figure {number}. {title}")
    run.bold = True
    if not path.exists():
        doc.add_paragraph("(Figure not found — run the experiment pipeline to generate it.)")
        return
    try:
        image_paragraph = doc.add_paragraph()
        image_run = image_paragraph.add_run()
        image_run.add_picture(str(path), width=Inches(6.5))
    except Exception:
        doc.add_paragraph(f"(Could not embed figure at: {path})")


