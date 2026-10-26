import pandas as pd
import streamlit as st
import requests
from io import BytesIO

st.set_page_config(
    page_title="Google Sheet Viewer",
    layout="wide"
)

st.title("📄 Google Sheet Viewer")

SHEET_URL = "https://docs.google.com/spreadsheets/d/1ab1ZDtxUXgMbDjmHCFZhTIRDV1a3yzi7lDA7-PC40MU/gviz/tq?tqx=out:csv&gid=1397139536"

st.markdown(
    "[🔗 Open Original Google Sheet](https://docs.google.com/spreadsheets/d/1ab1ZDtxUXgMbDjmHCFZhTIRDV1a3yzi7lDA7-PC40MU/edit#gid=1397139536)"
)

@st.cache_data(ttl=60)
def load_sheet():
    response = requests.get(
        SHEET_URL,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    response.raise_for_status()

    # Parse downloaded CSV content directly
    content = response.content
    df = pd.read_csv(BytesIO(content), encoding="utf-8-sig")

    # Remove completely empty rows and columns
    df = df.dropna(how="all").dropna(axis=1, how="all")

    return df

if st.button("🔄 Refresh Data"):
    st.cache_data.clear()

try:
    with st.spinner("Loading spreadsheet..."):
        df = load_sheet()

    st.success("Google Sheet loaded successfully!")

    st.write(f"**Rows:** {len(df)} | **Columns:** {len(df.columns)}")

    if df.empty:
        st.warning(
            "The CSV was downloaded, but no data rows were found. "
            "Check the selected worksheet tab."
        )
    else:
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        if st.checkbox("Show summary statistics"):
            st.write(df.describe(include="all"))

except Exception as e:
    st.error("Could not display the Google Sheet.")
    st.exception(e)
