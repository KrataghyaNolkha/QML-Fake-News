from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "response_to_reviewers.docx"


def add_response(doc: Document, label: str, response: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.keep_together = True
    r = p.add_run(label + " ")
    r.bold = True
    p.add_run(response)


def main() -> None:
    doc = Document()
    doc.core_properties.author = "Anonymous"
    doc.core_properties.last_modified_by = "Anonymous"
    doc.core_properties.title = "Response to Reviewers"
    section = doc.sections[0]
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.9)
    section.right_margin = Inches(0.9)

    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.add_run("Response to Reviewers")
    doc.add_paragraph("Paper 687 | MPCIT 2026")
    doc.add_paragraph(
        "We thank the reviewers for their careful assessment. We revised the manuscript and regenerated the primary results from the full Facebook fact-check dataset. The responses below describe changes made in the revised manuscript and identify the scope of experiments explicitly."
    )

    doc.add_heading("Reviewer 1", level=1)
    add_response(doc, "Comment 1. Condition-number scales differ between tables.",
                 "We audited the diagnostic implementation and standardized the reported definition. We center and symmetrize the Gram matrix, add a diagonal ridge of 10^-8, and report the largest positive eigenvalue divided by the smallest positive eigenvalue. The regenerated run gives values on the 10^8–10^9 scale. We could not reproduce the earlier 30–45 values under this definition and removed them rather than presenting them as comparable results.")
    add_response(doc, "Comment 2. Table II contains negative spectral gaps.",
                 "We made descending eigenvalue ordering explicit and recomputed the results. The reported gap is lambda_1 minus lambda_2 after centering and ridge stabilization; the regenerated values are nonnegative. The implementation rejects invalid nonsquare or nonfinite matrices.")
    add_response(doc, "Comment 3. Regression coefficients conflict.",
                 "We regenerated one standardized OLS model from the 25-row geometry-performance table, with accuracy as the response and alignment, log10(condition number), and spectral gap as predictors. The standardized coefficients are 0.431, -0.450, and -0.345, respectively; R-squared is 0.452. The corresponding predictor p-values are 0.059, 0.391, and 0.460. We removed conflicting coefficient sets and describe this small-sample model as exploratory.")
    add_response(doc, "Comment 4. Per-seed support-vector counts were missing.",
                 "We include the regenerated ten-seed table with the seed, each model's accuracy and count, and the ratio calculated for each seed. No seed was excluded in the completed run.")
    add_response(doc, "Comment 5. The single-run and aggregate ratios differ.",
                 "We distinguish the single-run count ratio from the ten-seed mean. The regenerated mean of per-seed ratios is 15.61, with a percentile-bootstrap 95% interval of 13.61–17.91 (n=10); this replaces the previous 25.34 claim. The manuscript also states that Pegasos active-set counts and SVC support-vector counts arise from different solvers and do not by themselves establish equivalent inference cost.")

    doc.add_heading("Reviewer 5", level=1)
    add_response(doc, "Comment 1. The geometry analysis has only 19 configurations.",
                 "The regenerated full preset contains 25 evaluated configurations. We report the sample size and treat the correlations as exploratory associations. We did not claim causal effects or out-of-sample prediction.")
    add_response(doc, "Comment 2. Condition-number correlations conflict.",
                 "We regenerated one authoritative correlation table from the current geometry rows. For log10(condition number), Pearson r is -0.521 and Spearman rho is -0.517 across all 25 configurations. Under the recorded absolute z-score > 2 rule, n=23, Pearson r is -0.672 and Spearman rho is -0.600. The table now includes the transformation, outlier rule, p-values, and Pearson confidence intervals.")
    add_response(doc, "Comment 3. Support-vector counts may not be comparable.",
                 "We report solver-specific counts and the exact Pegasos and classical settings in the run manifest. The ten-seed comparison uses matched PCA(2) representations and split seeds. We no longer characterize the ratio as a computational advantage. Longer-iteration sensitivity runs are not claimed as completed.")
    add_response(doc, "Comment 4. The main geometry study is limited to low qubit counts.",
                 "We state the tested qubit range and restrict conclusions to the evaluated configurations. The geometry subset has n=400. A higher-qubit geometry sweep is not claimed as completed.")
    add_response(doc, "Comment 5. Cross-dataset validation does not replicate the full geometry analysis.",
                 "We retain the breast-cancer table only as a classification sanity check and state that the geometry protocol was not replicated there. We excluded WELFake and LIAR from confirmatory claims and manuscript tables because the saved outputs contain conflicting runs and incomplete provenance; a matched reproducible evaluation remains future work.")
    add_response(doc, "Comment 6. Noise results are simulator-only.",
                 "We identify the AerSimulator and modeled depolarizing gate errors. The finite-shot stress test uses 512 shots, a stratified 60-example training subset, a 30-example kernel-statistics subset, and the full held-out split for accuracy. The manuscript reports the nonmonotonic accuracy values alongside the decreasing mean kernel similarity and makes no hardware-robustness claim.")
    add_response(doc, "Comment 7. Correlations are at risk of causal interpretation.",
                 "We replaced causal or predictive phrasing with exploratory association language and report the sample size, p-values, and confidence intervals. The multivariate coefficients are not statistically significant at 0.05.")
    add_response(doc, "Comment 8. Classical models outperform the quantum model on other representations.",
                 "We identify the representation for each comparison. The quantum result is compared directly with the PCA(2) RBF baseline; higher full-feature and engineered-feature classical results are reported separately. We do not claim that the quantum models outperform the strongest classical model overall.")
    add_response(doc, "Comment 9. Reproducibility details are incomplete.",
                 "The revised methods describe the split, seed, preprocessing, feature maps, matrix centering, ridge, eigengap and condition-number definitions, geometry subset, and noise protocol. A machine-readable run manifest records qubits, repetitions, Pegasos settings, shots, noise values, and software versions.")
    add_response(doc, "Comment 10. Novelty is not clearly positioned.",
                 "We position the contribution as a joint empirical evaluation of established geometry diagnostics in this fake-news metadata setting, not as a new metric or a demonstrated quantum advantage. We added recent work on quantum-kernel concentration and generalization.")

    doc.add_heading("Reviewer 6", level=1)
    add_response(doc, "Comment 1. Add implementation detail.",
                 "We added verified feature-map, preprocessing, regularization, split, diagnostic, and noise details and refer to the run manifest for exact settings. No unrecorded circuit constants are asserted.")
    add_response(doc, "Comment 2. Standardize Table I.",
                 "The report generator now applies a consistent 8-point table font, centered cell alignment, repeated header rows, header shading, and scientific notation for large values. The regenerated manuscript applies yellow highlighting to the revised text.")
    add_response(doc, "Comment 3. Add recent related work and align the title with results.",
                 "We added peer-reviewed 2024 work on concentration and generalization and 2026 work on benign overfitting with quantum kernels. The title remains focused on geometry analysis for fake-news detection; the abstract and conclusion now state that the results are exploratory and do not demonstrate quantum advantage.")

    doc.add_heading("Resubmission checks", level=1)
    doc.add_paragraph(
        "The revised manuscript is anonymized in its document properties and has no author-identifying title-page fields. All revised manuscript text is highlighted yellow. Tables and figures are regenerated from the completed full-dataset run."
    )
    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            run.font.name = "Times New Roman"
            run.font.size = Pt(10.5)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
