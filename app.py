import streamlit as st
import pandas as pd

# Sets the page configuration
# You can set the page title and layout here
st.set_page_config(page_title="HDB Resale Dashboard", layout="wide")

st.title("Singapore HDB Resale Dashboard")
st.caption("Code-along: building a usable dashboard from real resale transactions.")


##upload the file
DATA_PATH = "./data/sgjobdata_small.csv"

df = pd.read_csv(DATA_PATH)
# Lesson assumption:
# this dataset has already gone through EDA and basic cleaning.
# Here we focus on dashboard building, not data cleaning.
# We still set the datetime dtype explicitly for reliable filtering and charting.
##df["month"] = pd.to_datetime(df["month"])


##display now 
st.write(f"Rows loaded: {len(df):,} | Columns: {len(df.columns)}")
st.dataframe(df.head(100), width="stretch")

