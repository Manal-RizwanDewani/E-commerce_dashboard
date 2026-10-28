# E-commerce Store Insights Dashboard Design

**Date:** 2026-10-28

## Intent

Turn the existing e-commerce sales analysis notebook into a clear, interactive Streamlit dashboard for exploring revenue, profit, units, customer ratings, advertising spend, time patterns, and potential outliers. The audience is a store owner or analyst reviewing the 2020–2024 data and comparing performance across years, categories, regions, and months.

## Goals

- Create a project virtual environment and install Streamlit plus the dashboard's data and chart libraries into it.
- Use the notebook's `Year`, `Month`, `Category`, `Region`, `Units_Sold`, `Revenue`, `Profit`, `Customer_Rating`, and `Ad_Spend` fields.
- Provide interactive filters and linked visual summaries with Plotly.
- Include additional derived measures supported by notebook logic: total cost (`Revenue - Profit`), unit price (`total cost / units sold`), and profit margin (`Profit / Revenue`).
- Surface the notebook's key findings while recalculating KPIs and charts from the currently filtered data.
- Allow CSV upload, show data quality and row-level exploration, and let users download filtered rows.
- Give clear setup and launch instructions.

## Non-goals

- Changing or rewriting the original analysis notebook.
- Treating correlation as proof of causation or making unsupported claims about advertising ROI.
- Forecasting, customer-level segmentation, or product-level analysis; the dataset has no customer or product identifiers.
- Hard-coding notebook summary numbers as if they remain true after filters or data uploads.

## Constraints and findings

- The workspace contains `Copy_of_EDA_E_commerce_sales_data_Project.ipynb`, but no `ecommerce_sales_data.csv`. The notebook refers to `/content/ecommerce_sales_data.csv`, a Colab path. Dashboard startup therefore needs a clear upload prompt if no local CSV is present.
- The notebook has 1,000 rows and 9 original columns, no null values, and reports $27,123,544.52 revenue, $5,494,732.66 profit, 20.26% weighted profit margin, and 2,649,554.61 ad spend.
- The notebook's narrative has contradictions. Its actual `Units_Sold` to `Revenue` correlation output is about 0.67, not the 0.90 claimed in the summary. Its weekday summary calls Thursday both the highest and lowest. Dashboard insights must be calculated from data at runtime; no conflicting narrative statements should be repeated as facts.
- Currency is shown with `$` in the notebook's business summary; retain that convention.

## Approaches considered

1. **Require a local CSV.** Simple for a fixed deployment but the supplied workspace has no CSV, so the app would not be usable immediately.
2. **CSV upload only.** Works for arbitrary datasets but requires a repeated manual step even when a standard project CSV is later added.
3. **Auto-load a project CSV with upload fallback (recommended).** Try common project-local CSV names first, then let the user upload a file. This supports both a ready-to-run project and flexible data replacement. This is the proposed approach, pending user review.

## Proposed experience

- A clean, polished dashboard with a sidebar containing dataset input and multiselect filters for year, category, and region.
- An overview with filtered revenue, profit, weighted margin, units, and average rating KPIs, plus revenue/profit trends and category/region comparisons.
- A performance section for month/quarter seasonality, category and region rankings, and revenue versus profit.
- A marketing and customer section for ad spend versus revenue and ratings by category. Correlation is presented as association only.
- A data explorer with a sortable table, outlier summary using the notebook's IQR method, data-quality checks, and filtered CSV download.
- A concise insights panel generated from the selected data (top category, leading region, peak month, and correlations), with empty-data and invalid-file states handled clearly.

## Implementation calls left to the builder

- Use Streamlit, pandas, and Plotly with a small set of pinned dependencies in `requirements.txt`.
- Create `.venv` in the project folder and document Windows PowerShell activation and launch commands.
- Keep the app in the existing `streamlit` folder and use one main `app.py` unless project inspection reveals a natural existing structure.
- Load uploaded CSVs in memory; do not write uploaded files to disk.
- Derive time fields from `Year` and `Month`, validate required columns, and explain missing or malformed fields in the UI.
- Recompute all charts and summary values from the active filtered DataFrame.
