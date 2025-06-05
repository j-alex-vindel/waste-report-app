import streamlit as st

st.set_page_config(page_title="Weekly Analysis Hub", layout="wide")

st.title("📊 Welcome to the Weekly Waste Reporting Tool")
st.markdown(
    """
    Use the sidebar to navigate between the available analysis tools.
    
    - **Waste Report**: Analyze weekly food waste from your PDF reports.
    - **Single Origin**: (coming soon).
    - **More to come**: (coming soon)
    """
)
st.caption(""":male-technologist: **Developed by** [Alexander Vindel](https://github.com/j-alex-vindel)""")

