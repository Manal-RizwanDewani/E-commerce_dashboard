# E-commerce Store Insights Dashboard Implementation Plan

> **For agentic workers:** Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Build an interactive Streamlit dashboard for the supplied e-commerce analysis and create a project virtual environment with its dependencies.

**Architecture:** Keep the app in `streamlit/app.py`; load a project-local CSV when present and otherwise accept an in-memory upload. Validate/normalize the notebook's original columns, derive dates and measures, then calculate all KPIs, charts, filters, insights, and IQR outliers from active data at runtime.

**Tech Stack:** Python 3, Streamlit, pandas, Plotly.

**Spec:** `docs/superpowers/specs/2026-10-28-ecommerce-dashboard-design.md`

## Global Constraints

- Create `.venv` in the project root and install dependencies there.
- Required input fields are `Year`, `Month`, `Category`, `Region`, `Units_Sold`, `Revenue`, `Profit`, `Customer_Rating`, and `Ad_Spend` (case-insensitive after whitespace normalization).
- Uploaded data remains in memory; do not persist it to disk.
- Use `$` formatting as the notebook does.
- Describe correlations as associations, not causal effects.
- Compute insights from active filtered records; do not repeat the notebook's contradictory narrative as fact.

## Review Focus

- Missing/malformed CSV columns: report actionable validation errors rather than crashing (manual check in Task 2).
- Missing or unrecognized month values: handle date parsing safely and show a clear error (manual check in Task 2).
- Empty filter results: show an informative empty state without invalid aggregations (manual check in Task 2).
- Zero revenue or zero units: avoid division errors in derived profit margin and unit price (manual check in Task 2).
- No default CSV present: show the uploader prompt; uploaded files should not be written to disk (manual check in Task 2).

## File Structure

- Create `.gitignore` entries for `.venv/` and Python cache files.
- Create `requirements.txt` with pinned compatible versions of Streamlit, pandas, and Plotly.
- Create `streamlit/app.py` containing the data loading/validation functions and all dashboard views.
- Create `README.md` with Windows PowerShell environment setup and launch instructions, supported CSV schema, and dashboard feature summary.

## Tasks

### Task 1: Create project environment and dependency setup

**Files:** Create `.venv/`, `requirements.txt`, and `.gitignore`.

- [ ] Create the virtual environment using `python -m venv .venv` from the project root.
- [ ] Pin Streamlit, pandas, and Plotly in `requirements.txt`.
- [ ] Add `.venv/`, `__pycache__/`, and `*.py[cod]` to `.gitignore`.
- [ ] Install packages with `.venv\Scripts\python.exe -m pip install -r requirements.txt` and confirm the package versions using that interpreter.

### Task 2: Implement the interactive dashboard

**Files:** Create `streamlit/app.py`.

- [ ] Add `normalize_columns(df)`, `validate_and_prepare(df)`, and `load_default_data()` with exact responsibilities: normalize names to lower snake case; validate the nine required fields; parse `date` from year/month; derive `total_cost`, `unit_price`, `profit_margin`, `month_name`, and quarter safely; search project-root CSV candidates and return a useful missing-data state.
- [ ] Build sidebar upload and multiselect filters for year, category, and region; show an actionable error for absent required fields or invalid months.
- [ ] Render KPI cards for revenue, profit, weighted margin, units, and average rating. Use zero-safe calculations.
- [ ] Render Plotly charts for time trends, category and region performance, monthly seasonality, profit/revenue relationship, rating, ad spend correlation, and IQR outlier counts.
- [ ] Calculate brief filtered-data insights (top category/region/month and correlations) without causal claims; handle empty filter results.
- [ ] Add filtered sortable data table, data-quality summary, IQR outlier details, and filtered CSV download.
- [ ] Use a polished responsive layout and clear dataset-missing/invalid-file states.
- [ ] Launch the app using `.venv\Scripts\python.exe -m streamlit run streamlit/app.py`; manually check launch, missing-CSV prompt, uploaded valid CSV, each filter, empty filter result, invalid CSV, zero-valued denominators, and chart interactions.

### Task 3: Document local usage

**Files:** Create `README.md`.

- [ ] Document PowerShell commands to activate `.venv`, install `requirements.txt`, and run the dashboard.
- [ ] Document the expected CSV fields and upload fallback behavior.
- [ ] Summarize dashboard pages/features and the notebook findings included.
- [ ] Confirm paths and commands match the actual workspace and environment.
