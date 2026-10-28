from __future__ import annotations

import math
import re
from io import BytesIO
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_COLUMNS = {
    "year", "month", "category", "region", "units_sold", "revenue", "profit",
    "customer_rating", "ad_spend",
}
MONTH_ORDER = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


@st.cache_data(show_spinner=False)
def load_csv(file_bytes: bytes) -> pd.DataFrame:
    """Read uploaded CSV data in memory."""
    return pd.read_csv(BytesIO(file_bytes))


def normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Convert source headings to lowercase snake_case."""
    clean = frame.copy()
    clean.columns = [
        re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", str(col).strip().lower())).strip("_")
        for col in clean.columns
    ]
    return clean


def validate_and_prepare(frame: pd.DataFrame) -> pd.DataFrame:
    """Check the notebook schema and add derived measures."""
    data = normalize_columns(frame)
    missing = sorted(REQUIRED_COLUMNS - set(data.columns))
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))
    if data.columns.duplicated().any():
        duplicates = sorted(set(data.columns[data.columns.duplicated()].tolist()))
        raise ValueError("Duplicate column headings after normalization: " + ", ".join(duplicates))

    numeric_columns = ["year", "units_sold", "revenue", "profit", "customer_rating", "ad_spend"]
    for column in numeric_columns:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    finite = data[numeric_columns].map(lambda value: pd.notna(value) and math.isfinite(value))
    invalid_numeric = ~finite.all(axis=1)
    if invalid_numeric.any():
        rows = ", ".join(str(index + 2) for index in data.index[invalid_numeric][:5])
        raise ValueError(f"Required number fields contain blank, invalid, or non-finite values (CSV row {rows}).")

    fractional_year = data["year"].mod(1).ne(0)
    if fractional_year.any():
        rows = ", ".join(str(index + 2) for index in data.index[fractional_year][:5])
        raise ValueError(f"Year values must be whole numbers (CSV row {rows}).")

    data["year"] = data["year"].astype(int)
    data["month"] = data["month"].astype(str).str.strip()
    data["date"] = pd.to_datetime(
        data["year"].astype(str) + "-" + data["month"], format="%Y-%B", errors="coerce"
    )
    invalid_dates = data["date"].isna()
    if invalid_dates.any():
        rows = ", ".join(str(index + 2) for index in data.index[invalid_dates][:5])
        raise ValueError(f"Use full month names such as January (invalid value on CSV row {rows}).")

    for column in ("category", "region"):
        blank = data[column].isna() | data[column].astype("string").str.strip().eq("").fillna(False)
        if blank.any():
            rows = ", ".join(str(index + 2) for index in data.index[blank][:5])
            raise ValueError(f"{column.title()} has blank values (CSV row {rows}).")
        data[column] = data[column].astype(str).str.strip()

    data["month_name"] = data["date"].dt.month_name()
    data["quarter"] = data["date"].dt.quarter
    data["total_cost"] = data["revenue"] - data["profit"]
    data["unit_price"] = data["total_cost"].div(data["units_sold"].where(data["units_sold"].ne(0)))
    data["profit_margin"] = data["profit"].mul(100).div(data["revenue"].where(data["revenue"].ne(0)))
    return data


def load_default_data() -> tuple[pd.DataFrame | None, str | None]:
    """Load the first valid project CSV using the existing search paths."""
    candidates = [
        ROOT / "ecommerce_sales_data.csv",
        ROOT / "E-commerce_sales_data.csv",
        ROOT / "ecommerce_sales.csv",
        ROOT / "sales_data.csv",
    ]
    candidates.extend(sorted(ROOT.glob("*.csv")))
    candidates.extend(sorted((ROOT / "streamlit" / "data").glob("*.csv")))

    failures: list[str] = []
    for path in dict.fromkeys(candidates):
        if not path.is_file():
            continue
        try:
            return validate_and_prepare(pd.read_csv(path)), path.name
        except Exception as exc:
            failures.append(f"{path.name}: {exc}")

    if failures:
        return None, "Project CSV files could not be loaded: " + " | ".join(failures)
    return None, None


def format_money(value: float, compact: bool = False) -> str:
    if pd.isna(value):
        return "—"
    magnitude = abs(value)
    if compact and magnitude >= 1_000_000:
        return f"${value / 1_000_000:,.1f}M"
    if compact and magnitude >= 10_000:
        return f"${value / 1_000:,.0f}K"
    return f"${value:,.2f}"


def show_chart(fig) -> None:
    """Use a consistent chart height and fill the available Streamlit column."""
    fig.update_layout(height=350, template="plotly_white", margin=dict(l=16, r=16, t=55, b=20))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def iqr_summary(frame: pd.DataFrame) -> pd.DataFrame:
    measures = ["revenue", "profit", "units_sold", "unit_price", "ad_spend", "profit_margin"]
    rows = []
    for column in measures:
        values = frame[column].dropna()
        if values.empty:
            rows.append({"Measure": column.replace("_", " ").title(), "Outliers": 0, "Lower fence": None, "Upper fence": None})
            continue
        q1, q3 = values.quantile([0.25, 0.75])
        spread = q3 - q1
        low, high = q1 - 1.5 * spread, q3 + 1.5 * spread
        rows.append({
            "Measure": column.replace("_", " ").title(),
            "Outliers": int(((values < low) | (values > high)).sum()),
            "Lower fence": low,
            "Upper fence": high,
        })
    return pd.DataFrame(rows)


def show_dashboard(data: pd.DataFrame, source_name: str) -> None:
    st.sidebar.header("Filters")
    years = sorted(data["year"].unique().tolist())
    categories = sorted(data["category"].unique().tolist())
    regions = sorted(data["region"].unique().tolist())
    selected_years = st.sidebar.multiselect("Year", years, default=years)
    selected_categories = st.sidebar.multiselect("Category", categories, default=categories)
    selected_regions = st.sidebar.multiselect("Region", regions, default=regions)
    st.sidebar.caption(f"Data source: {source_name}")

    filtered = data[
        data["year"].isin(selected_years)
        & data["category"].isin(selected_categories)
        & data["region"].isin(selected_regions)
    ].copy()

    st.title("E-commerce Store Insights")
    st.caption("Explore sales, profitability, customer ratings, and advertising across time and store segments.")
    if filtered.empty:
        st.info("No records match these filters. Select at least one year, category, and region.")
        return

    revenue = float(filtered["revenue"].sum())
    profit = float(filtered["profit"].sum())
    margin = profit / revenue * 100 if revenue else float("nan")
    total_units = int(filtered["units_sold"].sum())
    average_rating = float(filtered["customer_rating"].mean())
    kpis = st.columns(5)
    kpis[0].metric("Revenue", format_money(revenue, compact=True), f"{len(filtered):,} records")
    kpis[1].metric("Profit", format_money(profit, compact=True))
    kpis[2].metric("Profit margin", f"{margin:.1f}%" if pd.notna(margin) else "—")
    kpis[3].metric("Units sold", f"{total_units:,}")
    kpis[4].metric("Average rating", f"{average_rating:.2f} / 5")

    st.caption(f"Showing {len(filtered):,} of {len(data):,} records")
    overview_tab, segment_tab, marketing_tab, data_tab = st.tabs(
        ["Overview", "Category & region", "Marketing & customers", "Data explorer"]
    )

    with overview_tab:
        left, right = st.columns(2)
        with left:
            measure_label = st.selectbox("Trend measure", ["Revenue", "Profit", "Units sold"])
            measure_column = {"Revenue": "revenue", "Profit": "profit", "Units sold": "units_sold"}[measure_label]
            trend = filtered.groupby("date", as_index=False)[measure_column].sum().sort_values("date")
            trend_fig = px.line(
                trend, x="date", y=measure_column, markers=True, title=f"{measure_label} over time",
                labels={"date": "Month", measure_column: measure_label},
            )
            trend_fig.update_traces(line_color="#16845b", line_width=3, marker_size=6)
            if measure_column != "units_sold":
                trend_fig.update_yaxes(tickprefix="$", tickformat="~s")
            show_chart(trend_fig)

        with right:
            monthly = filtered.groupby("month_name", as_index=False)["revenue"].sum()
            monthly["month_name"] = pd.Categorical(monthly["month_name"], categories=MONTH_ORDER, ordered=True)
            monthly = monthly.sort_values("month_name")
            month_fig = px.bar(
                monthly, x="month_name", y="revenue", title="Revenue by month",
                labels={"month_name": "Month", "revenue": "Revenue"}, color_discrete_sequence=["#16845b"],
            )
            month_fig.update_xaxes(tickangle=-30)
            month_fig.update_yaxes(tickprefix="$", tickformat="~s")
            show_chart(month_fig)

        category_revenue = filtered.groupby("category")["revenue"].sum().sort_values(ascending=False)
        region_revenue = filtered.groupby("region")["revenue"].sum().sort_values(ascending=False)
        best_month = monthly.sort_values("revenue", ascending=False).iloc[0]["month_name"]
        st.info(
            f"**Highlights:** {category_revenue.index[0]} leads category revenue "
            f"({format_money(category_revenue.iloc[0], compact=True)}); {region_revenue.index[0]} "
            f"leads by region; {best_month} is the strongest month in this selection."
        )

    with segment_tab:
        left, right = st.columns(2)
        with left:
            category = filtered.groupby("category", as_index=False).agg(
                revenue=("revenue", "sum"), profit=("profit", "sum"), units=("units_sold", "sum")
            ).sort_values("revenue")
            category_fig = px.bar(
                category, x="revenue", y="category", orientation="h", title="Revenue by category",
                labels={"revenue": "Revenue", "category": "Category"},
                color_discrete_sequence=["#16845b"], hover_data={"profit": ":$,.0f", "units": ":,"},
            )
            category_fig.update_xaxes(tickprefix="$", tickformat="~s")
            show_chart(category_fig)

        with right:
            matrix = filtered.pivot_table(
                index="region", columns="category", values="revenue", aggfunc="sum", fill_value=0
            )
            matrix_fig = px.imshow(
                matrix, text_auto=".2s", aspect="auto", color_continuous_scale="Greens",
                title="Revenue by region and category",
                labels={"x": "Category", "y": "Region", "color": "Revenue"},
            )
            show_chart(matrix_fig)

        left, right = st.columns(2)
        with left:
            relationship_fig = px.scatter(
                filtered, x="revenue", y="profit", color="category",
                hover_data=["region", "month_name", "units_sold"], title="Revenue and profit",
                labels={"revenue": "Revenue", "profit": "Profit"},
            )
            relationship_fig.update_xaxes(tickprefix="$", tickformat="~s")
            relationship_fig.update_yaxes(tickprefix="$", tickformat="~s")
            show_chart(relationship_fig)

        with right:
            ratings = filtered.groupby("category", as_index=False)["customer_rating"].mean()
            rating_fig = px.bar(
                ratings.sort_values("customer_rating"), x="customer_rating", y="category", orientation="h",
                title="Average customer rating by category",
                labels={"customer_rating": "Rating", "category": "Category"},
                color_discrete_sequence=["#65a875"],
            )
            rating_fig.update_xaxes(range=[0, 5])
            show_chart(rating_fig)

    with marketing_tab:
        st.info("Correlation shows association between measures in these records; it does not establish cause and effect.")
        left, right = st.columns(2)
        with left:
            ad_fig = px.scatter(
                filtered, x="ad_spend", y="revenue", color="region",
                hover_data=["category", "profit", "units_sold"], title="Advertising spend and revenue",
                labels={"ad_spend": "Ad spend", "revenue": "Revenue"},
            )
            ad_fig.update_xaxes(tickprefix="$", tickformat="~s")
            ad_fig.update_yaxes(tickprefix="$", tickformat="~s")
            show_chart(ad_fig)

        with right:
            ad_corr = filtered["ad_spend"].corr(filtered["revenue"]) if len(filtered) > 1 else float("nan")
            units_corr = filtered["units_sold"].corr(filtered["revenue"]) if len(filtered) > 1 else float("nan")
            correlation_metrics = st.columns(2)
            correlation_metrics[0].metric("Ad spend / revenue", f"{ad_corr:.2f}" if pd.notna(ad_corr) else "—", help="Pearson correlation")
            correlation_metrics[1].metric("Units / revenue", f"{units_corr:.2f}" if pd.notna(units_corr) else "—", help="Pearson correlation")

            ad_region = filtered.groupby("region", as_index=False)["ad_spend"].sum().sort_values("ad_spend")
            ad_region_fig = px.bar(
                ad_region, x="ad_spend", y="region", orientation="h", title="Advertising spend by region",
                labels={"ad_spend": "Ad spend", "region": "Region"}, color_discrete_sequence=["#d27d5d"],
            )
            ad_region_fig.update_xaxes(tickprefix="$", tickformat="~s")
            show_chart(ad_region_fig)

        ratings = filtered.groupby("category", as_index=False)["customer_rating"].mean()
        rating_fig = px.bar(
            ratings.sort_values("customer_rating"), x="category", y="customer_rating",
            title="Customer rating by category",
            labels={"category": "Category", "customer_rating": "Average rating"},
            color_discrete_sequence=["#65a875"],
        )
        rating_fig.update_yaxes(range=[0, 5])
        show_chart(rating_fig)

    with data_tab:
        st.caption("Potential outliers use the 1.5 × IQR rule on filtered data. Review them before treating them as errors.")
        quality = st.columns(3)
        quality[0].metric("Rows in view", f"{len(filtered):,}")
        quality[1].metric("Missing source cells", f"{int(filtered[list(REQUIRED_COLUMNS)].isna().sum().sum()):,}")
        quality[2].metric("Duplicate records", f"{int(filtered.duplicated().sum()):,}")

        st.subheader("Outlier summary")
        st.dataframe(iqr_summary(filtered), hide_index=True, use_container_width=True)
        with st.expander("Inspect possible outliers"):
            measure = st.selectbox(
                "Measure", ["revenue", "profit", "units_sold", "unit_price", "ad_spend", "profit_margin"],
                format_func=lambda value: value.replace("_", " ").title(),
            )
            values = filtered[measure].dropna()
            if len(values) < 2:
                st.caption("At least two valid values are needed to calculate outliers.")
            else:
                q1, q3 = values.quantile([0.25, 0.75])
                spread = q3 - q1
                outliers = filtered[
                    (filtered[measure] < q1 - 1.5 * spread)
                    | (filtered[measure] > q3 + 1.5 * spread)
                ].sort_values(measure, ascending=False)
                st.caption(f"{len(outliers)} possible {measure.replace('_', ' ')} outlier(s).")
                st.dataframe(outliers, hide_index=True, use_container_width=True)

        display_columns = [
            "date", "year", "month", "category", "region", "units_sold", "revenue", "profit",
            "total_cost", "unit_price", "profit_margin", "customer_rating", "ad_spend",
        ]
        st.subheader("Filtered records")
        st.dataframe(
            filtered[display_columns].sort_values("date", ascending=False),
            hide_index=True,
            use_container_width=True,
            height=420,
            column_config={
                "date": st.column_config.DateColumn("Month", format="MMM YYYY"),
                "revenue": st.column_config.NumberColumn(format="$%.2f"),
                "profit": st.column_config.NumberColumn(format="$%.2f"),
                "total_cost": st.column_config.NumberColumn(format="$%.2f"),
                "unit_price": st.column_config.NumberColumn(format="$%.2f"),
                "profit_margin": st.column_config.NumberColumn(format="%.1f%%"),
                "ad_spend": st.column_config.NumberColumn(format="$%.2f"),
            },
        )
        st.download_button(
            "Download filtered CSV",
            filtered[display_columns].to_csv(index=False).encode("utf-8"),
            file_name="store_insights_filtered.csv",
            mime="text/csv",
        )


def main() -> None:
    st.set_page_config(page_title="E-commerce Store Insights", layout="wide")

    default_data, default_message = load_default_data()
    st.sidebar.header("Data")
    uploaded_file = st.sidebar.file_uploader("Upload sales CSV", type=["csv"])
    data = default_data
    source_name = default_message or "No CSV found"

    if uploaded_file is not None:
        try:
            data = validate_and_prepare(load_csv(uploaded_file.getvalue()))
            source_name = uploaded_file.name
        except Exception as exc:
            st.title("E-commerce Store Insights")
            st.error(f"Could not read this CSV: {exc}")
            st.stop()

    if data is None:
        st.title("E-commerce Store Insights")
        st.info("No project CSV was found. Upload `ecommerce_sales_data.csv` using the left sidebar to view the dashboard.")
        st.caption("Required columns: Year, Month, Category, Region, Units_Sold, Revenue, Profit, Customer_Rating, Ad_Spend.")
        if default_message:
            st.sidebar.warning(default_message)
        return

    show_dashboard(data, source_name)


if __name__ == "__main__":
    main()
