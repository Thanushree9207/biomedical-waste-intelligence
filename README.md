# Biomedical Waste Intelligence

An exploratory machine-learning project for analyzing reported biomedical waste (BMW) generation and treatment across Indian states and union territories, and estimating future generation from historical reports.

## Project Overview

The project combines a six-year state/UT panel with exploratory analysis, chronological model evaluation, and forecasts for 2024–2027. It also inspects the supplied Excel workbook and produces data-quality reports. Results are intended for learning and exploration, not operational or regulatory decisions.

## Problem Statement

BMW generation and treatment figures are reported across annual publications and may have gaps, inconsistent labels, and changes in reporting coverage. This project organizes the available figures into an analysis-ready workbook and explores whether historical state and year patterns can help estimate BMW generation.

## Objectives

- Inspect the workbook's sheets, columns, missing values, duplicates, and numeric fields.
- Explore state/UT and year-level reporting coverage and BMW patterns.
- Compare candidate regressors using time-ordered validation.
- Estimate state/UT BMW generation for 2024–2027.
- Keep missing observations distinct from zero and document the limits of the source data and predictions.

## Dataset Description

The input is `datasets/biomedical dataset.xlsx`, a workbook containing annual and derived tables. The `State-wise 6 Years` sheet has a designed panel of 36 standardized state/UT reporting labels across 2018–2023 (216 state-year rows). Its fields include reported BMW generated and treated (kg/day), calculated treatment gap and ratio, and government-hospital counts and beds.

The workbook also includes national trends, management indicators, a dashboard matrix, a data dictionary, source notes, and data-quality notes. State-level extraction is not fully audited in this build; the panel is not fully complete. Blank values are missing, not zero. Historical combined territories are retained where the source reports them. Government-hospital beds cover government hospitals only and are not a measure of all hospital beds.

The workbook is an input file and is excluded from Git by `.gitignore`; obtain and place it locally before running the analysis.

## Technologies Used

- Python 3
- Jupyter Notebook and IPython
- NumPy
- scikit-learn
- openpyxl for Excel workbook reading
- joblib for model persistence
- Python standard library modules including `csv`, `json`, and `statistics`

## Project Methodology

1. Read the supplied workbook and inspect its sheets and data quality.
2. Use reported BMW generation (kg/day) as the prediction target, with reporting year and state/UT as features.
3. Exclude rows with missing target values from model fitting; do not impute them as zero.
4. Compare candidate models on chronological splits to reduce temporal leakage.
5. Select the candidate with the lowest RMSE on the notebook's 2021–2023 holdout, refit it using observed data through 2023, and generate 2024–2027 estimates.

Treatment and treatment-gap fields are not used as predictors for generation, avoiding target leakage. Hospital-bed counts are also excluded because future values are unavailable and the available counts cover government hospitals only.

## Exploratory Data Analysis

The workbook inspection module summarizes sheet dimensions, columns, non-empty records, duplicate records, missing values by column, value types, and numeric summaries. The notebook examines annual reporting coverage and observed generation, then compares reported generated and treated amounts and derived treatment gaps/ratios where available.

The source workbook flags incomplete state-level extraction and an inconsistency in the 2020 national report figures. Interpret aggregates and state comparisons with those limitations in mind.

## Machine Learning Model

The notebook compares several regression approaches, including linear and regularized models, generalized linear models, support-vector and nearest-neighbor regressors, decision trees, and tree ensembles. A last-observation baseline is also available for comparison. The selected estimator depends on the chronological evaluation; the notebook does not assume one model is best for every dataset or future period.

The selected model is refit on available observations through 2023 to produce exploratory state/UT estimates for 2024, 2025, 2026, and 2027. Forecasts are not measured values. Tree models generally do not extrapolate trends naturally, and uncertainty increases farther from the observed period.

## Model Evaluation

The notebook uses 2018–2020 for training and 2021–2023 as a fixed chronological test period. Candidate models are compared using mean absolute error (MAE), root mean squared error (RMSE), and R-squared; the lowest holdout RMSE is used for model selection. Generated reports and saved comparison files may also include rolling year-based validation.

Validation on a short, incomplete historical panel does not guarantee future accuracy. Abrupt source changes, reporting inconsistencies, and limited features can materially affect results. Review the notebook and its evaluation outputs before interpreting a forecast.

## Dashboard and Visualizations

The workbook includes a `Dashboard Matrix` sheet, and the notebook presents analysis and model results in tabular notebook output. This repository does not currently contain a standalone interactive dashboard application.

## Installation and Execution

Use Python 3 and run the commands from the project directory. Install the input workbook at `datasets/biomedical dataset.xlsx` first; the dataset is not included in this repository.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install jupyter ipython numpy scikit-learn openpyxl joblib
```

Run the workbook inspection and generate JSON/text reports under `outputs/`:

```powershell
python src/data_inspection.py
```

Open and run the model-comparison notebook:

```powershell
jupyter notebook notebooks/model_comparison_and_prediction.ipynb
```

The notebook can read the workbook from either a `datasets/` or `dataset/` directory. Generated model files and outputs are local artifacts and are excluded from Git.

## Project Structure

```text
MLmodel/
├── .gitignore
├── README.md
├── datasets/                         # Local input workbook (not tracked)
├── model/                            # Local model artifacts and comparisons
├── notebooks/
│   └── model_comparison_and_prediction.ipynb
├── outputs/                          # Local reports, forecasts, and results
└── src/
    └── data_inspection.py
```

## Future Enhancements

- Audit and verify state-level values against the original annual reports.
- Improve data provenance and preserve source page/table references for each observation.
- Evaluate additional temporal baselines and uncertainty intervals.
- Add automated tests for data validation and forecasting.
- Build a standalone dashboard with filters, historical comparisons, treatment-gap views, and clearly labeled forecast ranges.
- Add a dependency file and a reproducible data-preparation workflow.

## References and Data Sources

The supplied workbook cites the Central Pollution Control Board (CPCB) annual reports on biomedical waste management. The state-level extraction and derived fields should be checked against the original reports before reuse.

- [CPCB Annual Report on Biomedical Waste Management 2018](https://cpcb.nic.in/uploads/Projects/Bio-Medical-Waste/AR_BMWM_2018.pdf)
- [CPCB Annual Report on Biomedical Waste Management 2019](https://cpcb.nic.in/uploads/Projects/Bio-Medical-Waste/AR_BMWM_2019.pdf)
- [CPCB Annual Report on Biomedical Waste Management 2020](https://cpcb.nic.in/uploads/Projects/Bio-Medical-Waste/AR_BMWM_2020.pdf)
- [CPCB Annual Report on Biomedical Waste Management 2021](https://cpcb.nic.in/uploads/Projects/Bio-Medical-Waste/AR_BMWM_2021.pdf)
- [CPCB Annual Report on Biomedical Waste Management 2022](https://cpcb.nic.in/uploads/Projects/Bio-Medical-Waste/AR_BMWM_2022.pdf)
- [CPCB Annual Report on Biomedical Waste Management 2023](https://cpcb.nic.in/uploads/Projects/Bio-Medical-Waste/AR_BMWM_2023.pdf)
- The supplied Excel workbook's `Sources and Methodology`, `Data Dictionary`, and `Data Quality and Missing Values` sheets.
