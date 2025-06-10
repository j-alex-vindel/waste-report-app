import streamlit as st

st.set_page_config(page_title="Weekly Analysis Hub", layout="wide")

st.title("📊 Welcome to the Weekly Waste Reporting Tool")
st.markdown(
    """
    Use the sidebar to navigate between the available analysis tools.
    
    - _**Use this tool to help you visualize your weekly food waste reports and SO sales.**_


    - :chart: **Waste Report**: Analyze weekly food waste from your PDF reports. Download a PDF with the Top 10 waste items charts.
    - :coffee: **Single Origin**: Analyze weekly Single Origin  sales from your PDF report. Download a PDF with the staff performance chart.
    - **More to come**: (coming soon)
    """
)
st.caption(""":male-technologist: **Developed by** [Alexander Vindel](https://github.com/j-alex-vindel)""")

