# sales_dashboard_realtime.py
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta

# Page config
st.set_page_config(page_title="Sales Data Insights (Real-time Demo)", layout="wide")

# Sample data generator
@st.cache_data
def sample_data(n=40, seed=42):
    np.random.seed(seed)
    base = datetime(2025, 1, 1)
    products = ["Product A", "Product B", "Product C"]
    regions = ["North", "South", "East", "West"]
    rows = []
    for i in range(n):
        rows.append({
            "Date": (base + timedelta(days=int(np.random.randint(0, 60)))).date(),
            "Product": np.random.choice(products),
            "Region": np.random.choice(regions),
            "Units Sold": int(np.random.randint(10, 200)),
            "Unit Price": float(np.random.choice([10, 15, 20])),
        })
    df = pd.DataFrame(rows)
    df["Total Sales"] = df["Units Sold"] * df["Unit Price"]
    return df

# Initialize session state dataset
if "df" not in st.session_state:
    st.session_state.df = sample_data(n=40)

# Header
st.title("📊 Sales Data Insights Dashboard — Real-time Demo")
st.markdown("Upload your CSV (Date, Product, Region, Units Sold, Unit Price) or use the sample dataset. Use **Add random transaction** to simulate live sales.")

# Sidebar: upload / reset / simulate
with st.sidebar:
    st.header("Data")
    uploaded_file = st.file_uploader("Upload CSV (Date,Product,Region,Units Sold,Unit Price)", type=["csv"])
    if uploaded_file:
        try:
            df_upload = pd.read_csv(uploaded_file)
            required = {"Date", "Product", "Region", "Units Sold", "Unit Price"}
            if not required.issubset(set(df_upload.columns)):
                st.error(f"CSV must contain columns: {', '.join(required)}")
            else:
                # parse and sanitize
                df_upload["Date"] = pd.to_datetime(df_upload["Date"]).dt.date
                df_upload["Units Sold"] = pd.to_numeric(df_upload["Units Sold"], errors="coerce").fillna(0).astype(int)
                df_upload["Unit Price"] = pd.to_numeric(df_upload["Unit Price"], errors="coerce").fillna(0.0)
                df_upload["Total Sales"] = df_upload["Units Sold"] * df_upload["Unit Price"]
                st.session_state.df = df_upload.copy()
                st.success("CSV loaded into session.")
        except Exception as e:
            st.error(f"Failed to read CSV: {e}")

    if st.button("Reset to Sample Data"):
        st.session_state.df = sample_data(n=40)
        st.success("Session reset to sample dataset.")

    st.markdown("---")
    st.header("Real-time Simulation")
    if st.button("Add random transaction (simulate)"):
        # create a row and append
        new_row = {
            "Date": datetime.now().date(),
            "Product": np.random.choice(["Product A", "Product B", "Product C"]),
            "Region": np.random.choice(["North", "South", "East", "West"]),
            "Units Sold": int(np.random.randint(1, 200)),
            "Unit Price": float(np.random.choice([10, 15, 20])),
        }
        new_row["Total Sales"] = new_row["Units Sold"] * new_row["Unit Price"]
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_row])], ignore_index=True)
        
        # Refresh the app (works on old and new Streamlit)
        if hasattr(st, "rerun"):
            st.rerun()
        else:
            st.experimental_rerun()

    st.markdown("---")
    st.markdown("Tip: Uploading a CSV replaces the current session dataset. Use Reset to return to the sample dataset.")

# Working DataFrame
df = st.session_state.df.copy()

# Ensure correct types
df["Date"] = pd.to_datetime(df["Date"]).dt.date
df["Units Sold"] = pd.to_numeric(df["Units Sold"], errors="coerce").fillna(0).astype(int)
df["Unit Price"] = pd.to_numeric(df["Unit Price"], errors="coerce").fillna(0.0)
df["Total Sales"] = df["Units Sold"] * df["Unit Price"]

# Filters (placed in sidebar for clarity)
st.sidebar.header("Filters")
min_date = df["Date"].min()
max_date = df["Date"].max()

date_range = st.sidebar.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = date_range
    end_date = date_range

regions = st.sidebar.multiselect("Region(s):", options=sorted(df["Region"].unique()), default=sorted(df["Region"].unique()))
products = st.sidebar.multiselect("Product(s):", options=sorted(df["Product"].unique()), default=sorted(df["Product"].unique()))

# Apply filters
filtered_df = df[
    (df["Date"] >= start_date) &
    (df["Date"] <= end_date) &
    (df["Region"].isin(regions)) &
    (df["Product"].isin(products))
].copy()

# KPIs
total_sales = filtered_df["Total Sales"].sum()
total_units = filtered_df["Units Sold"].sum()
avg_price = filtered_df["Unit Price"].mean() if len(filtered_df) > 0 else 0.0

col1, col2, col3 = st.columns(3)
col1.metric("Total Sales ($)", f"{total_sales:,.2f}")
col2.metric("Total Units Sold", f"{int(total_units):,}")
col3.metric("Avg Unit Price ($)", f"{avg_price:,.2f}")

st.markdown("---")

# Sales by Product (bar)
if not filtered_df.empty:
    prod_sales = filtered_df.groupby("Product", as_index=False)["Total Sales"].sum().sort_values("Total Sales", ascending=False)
    fig_prod = px.bar(prod_sales, x="Product", y="Total Sales", title="Total Sales by Product", text_auto=True)
    st.plotly_chart(fig_prod, use_container_width=True)
else:
    st.info("No data to display for selected filters (Product chart).")

# Sales by Region (pie)
if not filtered_df.empty:
    reg_sales = filtered_df.groupby("Region", as_index=False)["Total Sales"].sum()
    fig_reg = px.pie(reg_sales, names="Region", values="Total Sales", title="Sales Distribution by Region", hole=0.35)
    st.plotly_chart(fig_reg, use_container_width=True)
else:
    st.info("No data to display for selected filters (Region chart).")

# Time series
if not filtered_df.empty:
    ts = filtered_df.groupby("Date", as_index=False)["Total Sales"].sum().sort_values("Date")
    fig_ts = px.line(ts, x="Date", y="Total Sales", title="Daily Sales Trend", markers=True)
    st.plotly_chart(fig_ts, use_container_width=True)
else:
    st.info("No data to display for selected filters (Time series).")

st.markdown("---")

# Data Table + Download
st.subheader("Detailed Sales Data")
st.dataframe(filtered_df.reset_index(drop=True), use_container_width=True)

def convert_df_to_csv(df_):
    return df_.to_csv(index=False).encode("utf-8")

csv_bytes = convert_df_to_csv(filtered_df)
st.download_button("Download filtered data (CSV)", data=csv_bytes, file_name="filtered_sales.csv", mime="text/csv")

# Notes
st.markdown("""
**How to use**
- Upload a CSV with columns: `Date, Product, Region, Units Sold, Unit Price` (Date can be YYYY-MM-DD).  
- Or use the built-in sample dataset.  
- Use the **Add random transaction (simulate)** button to append demo sales.  
- Use filters to slice the data, and use the Download button to export the filtered view.
""")
