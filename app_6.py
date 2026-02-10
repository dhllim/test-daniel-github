import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="SG Job Market Dashboard", layout="wide")

# 2. Password Protection Logic
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        return True

# 3. Main App Content
if check_password():
    st.title("🇸🇬 Singapore Job Market Dashboard")
    st.caption("Advanced filtering for targeted job market analysis.")

    # --- DATA LOADING ---
    POSSIBLE_PATHS = ["data/sgjobdata_small.csv", "sgjobdata_small.csv"]
    DATA_PATH = next((p for p in POSSIBLE_PATHS if os.path.exists(p)), None)

    @st.cache_data
    def load_data(path):
        df = pd.read_csv(path)
        df["metadata_originalPostingDate"] = pd.to_datetime(df["metadata_originalPostingDate"])
        df["average_salary"] = pd.to_numeric(df["average_salary"], errors='coerce')
        df["minimumYearsExperience"] = pd.to_numeric(df["minimumYearsExperience"], errors='coerce')
        # Fill missing values for filtering
        df["employmentTypes"] = df["employmentTypes"].fillna("Unspecified")
        return df.dropna(subset=["average_salary", "positionLevels", "metadata_originalPostingDate"])

    if DATA_PATH:
        df = load_data(DATA_PATH)

        # --- SIDEBAR FILTERS ---
        st.sidebar.header("Filter Controls")
        
        # New Filter: Job Title Search
        search_query = st.sidebar.text_input("🔍 Search Job Titles", "")

        # New Filter: Date Range
        min_date = df["metadata_originalPostingDate"].min().date()
        max_date = df["metadata_originalPostingDate"].max().date()
        date_range = st.sidebar.date_input("📅 Posting Date Range", [min_date, max_date])

        # Existing: Position Level
        unique_levels = sorted(df["positionLevels"].unique())
        selected_levels = st.sidebar.multiselect("Position Level", unique_levels, default=unique_levels)

        # New Filter: Employment Type
        unique_types = sorted(df["employmentTypes"].unique())
        selected_types = st.sidebar.multiselect("Employment Type", unique_types, default=unique_types)

        # Salary & Experience Sliders
        min_sal_data = int(df["average_salary"].min())
        salary_range = st.sidebar.slider("Monthly Salary Range ($)", min_sal_data, 25000, (min_sal_data, 15000))
        exp_val = st.sidebar.slider("Maximum Years Experience", 0, 20, 10)

        # --- APPLY FILTERS ---
        mask = (
            (df["title"].str.contains(search_query, case=False, na=False)) &
            (df["positionLevels"].isin(selected_levels)) &
            (df["employmentTypes"].isin(selected_types)) &
            (df["average_salary"].between(salary_range[0], salary_range[1])) &
            (df["minimumYearsExperience"] <= exp_val)
        )
        
        # Date range filtering (handles single date selection during range picking)
        if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
            mask &= (df["metadata_originalPostingDate"].dt.date.between(date_range[0], date_range[1]))
            
        filtered_df = df[mask]

        # --- DASHBOARD LAYOUT ---
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Job Count", f"{len(filtered_df):,}")
        m2.metric("Avg Salary", f"${filtered_df['average_salary'].mean():,.0f}")
        m3.metric("Median Salary", f"${filtered_df['average_salary'].median():,.0f}")
        m4.metric("Avg Experience", f"{filtered_df['minimumYearsExperience'].mean():.1f} yrs")

        st.divider()

        # Trend & Visuals
        st.subheader("📈 Posting Trends & Market Composition")
        trend_data = filtered_df.groupby(filtered_df["metadata_originalPostingDate"].dt.date).size().reset_index(name='count')
        fig_trend = px.line(trend_data, x="metadata_originalPostingDate", y="count", title="Postings Over Time")
        st.plotly_chart(fig_trend, width="stretch")

        col_l, col_r = st.columns(2)
        with col_l:
            fig_level = px.bar(filtered_df.groupby("positionLevels")["average_salary"].mean().sort_values(), orientation='h')
            st.plotly_chart(fig_level, width="stretch")
        with col_r:
            fig_pie = px.pie(filtered_df, names='employmentTypes', hole=0.4)
            st.plotly_chart(fig_pie, width="stretch")

        # Data Table
        st.subheader(f"Top {min(50, len(filtered_df))} Relevant Job Postings")
        st.dataframe(
            filtered_df[['title', 'postedCompany_name', 'average_salary', 'employmentTypes']].head(50),
            width="stretch", 
            hide_index=True
        )
    else:
        st.error("❌ Data file not found.")