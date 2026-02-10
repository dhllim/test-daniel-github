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
    st.caption("Visualizing job trends, salaries, and requirements.")

    # --- DATA LOADING ---
    POSSIBLE_PATHS = ["data/sgjobdata_small.csv", "sgjobdata_small.csv"]
    DATA_PATH = None

    for path in POSSIBLE_PATHS:
        if os.path.exists(path):
            DATA_PATH = path
            break

    @st.cache_data
    def load_data(path):
        df = pd.read_csv(path)
        # Ensure date is in datetime format for trending
        df["metadata_originalPostingDate"] = pd.to_datetime(df["metadata_originalPostingDate"])
        df["average_salary"] = pd.to_numeric(df["average_salary"], errors='coerce')
        df["minimumYearsExperience"] = pd.to_numeric(df["minimumYearsExperience"], errors='coerce')
        return df.dropna(subset=["average_salary", "positionLevels", "metadata_originalPostingDate"])

    if DATA_PATH:
        df = load_data(DATA_PATH)

        # --- SIDEBAR FILTERS ---
        st.sidebar.header("Filter Controls")
        unique_levels = sorted(df["positionLevels"].dropna().unique())
        selected_levels = st.sidebar.multiselect("Position Level", unique_levels)

        min_sal = int(df["average_salary"].min())
        salary_range = st.sidebar.slider("Monthly Salary Range ($)", min_sal, 20000, (min_sal, 12000))
        exp_val = st.sidebar.slider("Maximum Years Experience Required", 0, 15, 5)

        # --- APPLY FILTERS ---
        filtered_df = df.copy()
        if selected_levels:
            filtered_df = filtered_df[filtered_df["positionLevels"].isin(selected_levels)]
        
        filtered_df = filtered_df[
            (filtered_df["average_salary"].between(salary_range[0], salary_range[1])) &
            (filtered_df["minimumYearsExperience"] <= exp_val)
        ]

        # --- DASHBOARD LAYOUT ---
        
        # Row 1: Key Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Job Count", f"{len(filtered_df):,}")
        m2.metric("Avg Salary", f"${filtered_df['average_salary'].mean():,.0f}")
        m3.metric("Median Salary", f"${filtered_df['average_salary'].median():,.0f}")
        m4.metric("Avg Experience", f"{filtered_df['minimumYearsExperience'].mean():.1f} yrs")

        st.divider()

        # NEW ROW: Trending Graph
        st.subheader("📈 Job Posting Trends (Daily)")
        # Grouping data by date to count postings per day
        trend_data = filtered_df.groupby(filtered_df["metadata_originalPostingDate"].dt.date).size().reset_index(name='count')
        fig_trend = px.line(trend_data, x="metadata_originalPostingDate", y="count", 
                            title="Volume of New Job Postings Over Time",
                            labels={'metadata_originalPostingDate': 'Date', 'count': 'New Postings'})
        st.plotly_chart(fig_trend, width="stretch")

        st.divider()

        # Row 2: Category Charts
        col_left, col_right = st.columns(2)
        with col_left:
            st.subheader("Salary by Position Level")
            level_chart_data = filtered_df.groupby("positionLevels")["average_salary"].mean().sort_values()
            fig_level = px.bar(level_chart_data, orientation='h', color_continuous_scale='Blues')
            st.plotly_chart(fig_level, width="stretch")

        with col_right:
            st.subheader("Distribution of Employment Types")
            fig_pie = px.pie(filtered_df, names='employmentTypes', hole=0.4)
            st.plotly_chart(fig_pie, width="stretch")

        # Row 3: Data Table
        st.subheader("Detailed Job Postings (Top 50)")
        st.dataframe(
            filtered_df[['title', 'postedCompany_name', 'average_salary', 'minimumYearsExperience']].head(50),
            width="stretch", 
            hide_index=True
        )

    else:
        st.error(f"❌ File Not Found!")
