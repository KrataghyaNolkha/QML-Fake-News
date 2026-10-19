import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from scipy.stats import t, shapiro

repo_root = Path(__file__).resolve().parents[1]

# 1. Load the raw data from your outputs directory
csv_path = repo_root / 'outputs' / 'tables' / 'kernel_geometry_performance.csv'
print(f"Reading data from: {csv_path}")
df = pd.read_csv(csv_path)
if 'correlation_included' in df.columns:
    df = df[df['correlation_included'].astype(bool)].copy()

# 2. Replicate Regression Processing
df_reg = df.copy()
df_reg['log10_condition_number'] = np.log10(pd.to_numeric(df_reg['condition_number'], errors='coerce'))
df_reg = df_reg.replace([np.inf, -np.inf], pd.NA).dropna(subset=['accuracy', 'kernel_alignment', 'spectral_gap', 'log10_condition_number'])

X = df_reg[['kernel_alignment', 'log10_condition_number', 'spectral_gap']].astype(float)
y = df_reg['accuracy'].astype(float).to_numpy()

X_scaled = StandardScaler().fit_transform(X)
y_scaled = StandardScaler().fit_transform(y.reshape(-1, 1)).ravel()

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

t_stats = beta / se_beta
p_values = [2 * (1 - t.cdf(np.abs(ts), n - k)) for ts in t_stats]

t_crit = t.ppf(0.975, n - k)
ci_lower = beta - t_crit * se_beta
ci_upper = beta + t_crit * se_beta

stat, p_res = shapiro(residuals)

res_df = pd.DataFrame({
    'Predictor': ['Intercept', 'Alignment', 'Log10(Condition)', 'Spectral Gap'],
    'Beta': beta,
    'p-value': p_values,
    '95% CI Lower': ci_lower,
    '95% CI Upper': ci_upper
})

print("\n--- STEP 6: REGRESSION STATISTICS ---")
print(f"R-squared: {r_squared:.4f}")
print(res_df.to_string())
print(f"Shapiro-Wilk test on residuals: W={stat:.3f}, p={p_res:.3f}")


# 3. Replicate Discrepancy / Outlier Processing
print("\n--- STEP 7: PEARSON/SPEARMAN DISCREPANCY ---")
df_corr = pd.read_csv(repo_root / 'outputs' / 'tables' / 'kernel_geometry_correlations.csv')
print("\n--- GEOMETRY CORRELATION RECONCILIATION ---")
cond = df_corr[df_corr['metric'].eq('log10_condition_number')]
for _, row in cond.iterrows():
    treatment = row.get('outlier_handling', 'unspecified')
    print(
        f"{treatment}: n={int(row['n'])}, Pearson r={row['pearson_r']:.3f}, "
        f"Spearman rho={row['spearman_r']:.3f}"
    )
