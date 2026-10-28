# E-commerce Store Insights

An interactive Streamlit dashboard for exploring the e-commerce sales analysis in `E-commerce_sales.ipynb`.

## Start the dashboard (Windows PowerShell)

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run streamlit\app.py
```

If PowerShell blocks virtual-environment activation, call the environment's executable directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run streamlit\app.py
```

## Data

The dashboard looks for a project-local CSV named `ecommerce_sales_data.csv`, `E-commerce_sales_data.csv`, `ecommerce_sales.csv`, or `sales_data.csv`. It also accepts another CSV placed in the project root. If no file is present, use **Add your sales CSV** in the left sidebar. Uploaded data is processed in memory and is not saved to disk.

The CSV must include these columns (capitalization and spaces are flexible):

- `Year`
- `Month` (full month names such as `January`)
- `Category`
- `Region`
- `Units_Sold`
- `Revenue`
- `Profit`
- `Customer_Rating`
- `Ad_Spend`

## Dashboard features

- Interactive year, category, and region filters
- Revenue, profit, weighted profit-margin, unit, and rating KPIs
- Revenue/profit/unit trends and monthly seasonality
- Category and regional comparisons, including a region/category revenue matrix
- Customer ratings and advertising-spend analysis
- Filtered Pearson correlations, presented as associations rather than causal effects
- IQR outlier review, data-quality summary, sortable row explorer, and filtered CSV download
- Derived total cost, unit price, and profit margin in the filtered row explorer and download

The notebook reports 1,000 records, $27.1M revenue, $5.49M profit, and a 20.26% overall profit margin. The dashboard recalculates all visible KPIs and insights from the loaded and filtered data rather than using those notebook totals as fixed values.
