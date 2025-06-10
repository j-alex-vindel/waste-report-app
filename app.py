import streamlit as st
import base64


def add_bg_from_local(image_file):
    with open(image_file, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()

    css = f"""
    <style>
    .stApp {{
        background: url("data:image/jpg;base64,{encoded}") no-repeat center center fixed;
        background-size: cover;
        position: relative;
    }}

    .stApp::before {{
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        height: 100%;
        width: 100%;
        background: rgba(255, 255, 255, 0.75); /* White overlay with 75% opacity */
        z-index: 0;
    }}

    .stApp > * {{
        position: relative;
        z-index: 1;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# 🔁 Add background image
add_bg_from_local("assests/beans.jpg")

st.title("📊 Welcome to the Weekly Waste Reporting Tool")
st.markdown(
    """
    Use the sidebar to navigate between the available visualization tools.
    
    - _**Use this tool to help you visualize/ analyze your weekly food waste reports and SO sales.**_


    - :chart: **Waste Report**: Analyze weekly food waste from your PDF reports. Download a PDF with the Top 10 waste items charts.
    - :coffee: **Single Origin**: Analyze weekly Single Origin  sales from your PDF report. Download a PDF with the staff performance chart.
    - **More to come...**
    """
)
st.caption(""":male-technologist: **Developed by** [Alexander Vindel](https://github.com/j-alex-vindel)""")

