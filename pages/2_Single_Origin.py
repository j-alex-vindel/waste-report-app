import streamlit as st
import pdfplumber
import pandas as pd
import matplotlib.pyplot as plt
import re
from io import BytesIO
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import base64
from email_utils import send_email_with_reports, validate_email,get_email_config
import os

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
add_bg_from_local("assests/coffebean_so.jpg")

tab1, tab2 = st.tabs(["⬇️ Download Report", "📧 Email Report"])

st.title("📁 Single Origin")
st.info("This feature will allow you to plot and track single origin sales.")

uploaded_file = st.file_uploader("Upload your PDF report - Single Origin Espresso Sales Report - (Colin)", type="pdf")

if uploaded_file:
    try:
        rows_cleaned = []
        store_name = None
        date = None
        with pdfplumber.open(uploaded_file) as pdf:
            title = pdf.metadata.get("Title", "Unknown Title").strip()
            first_page = pdf.pages[0]   
            if not title or "Single Origin" not in title:
                first_page_text = first_page.extract_text()
                if "Single Origin" not in first_page_text:
                    st.error("This PDF does not appear to be a Single Origin report.")
                    st.stop()
            else:
                st.success(f"Processing PDF: {title}")
                table = first_page.extract_table()
                text = first_page.extract_text()
                date = text.split("\n")[0]
                date = '-'.join(date.split()[-4:-1])
                if not date:
                    date = "Unknown Date"

                for i,row in enumerate(table):
                    if not row or (len(row) < 2) or (row[0] is None and row[1] is None):
                        continue

                    if i == 2 and len(row) > 1 and row[1]:
                        store_name = row[1].strip()

                    if i >= 3 and len(row) > 5:
                        name = row[1].strip() if row[1] else None
                        p_week = row[-3].strip() if row[-3] else None
                        mix_pct = row[-1].strip() if row[-1] else None
                        if name and mix_pct:
                            rows_cleaned.append((name, p_week, mix_pct))    
                # Create DataFrame
                df = pd.DataFrame(rows_cleaned, columns=["Name", "Previous Week", "Mix % Last"])
                df = df[~df["Name"].str.contains(r"Cashier|Barista|Shift", case=False, na=False)]
                df["Name"] = df["Name"].str.strip()
                # Convert and replace NaN with 0
                df["Mix % Last"] = pd.to_numeric(df["Mix % Last"].str.replace('%', ''), errors="coerce").fillna(0)
                df["Previous Week"] = pd.to_numeric(df["Previous Week"].str.replace('%',''), errors="coerce").fillna(0)
                df["Improvement"] = df["Mix % Last"] - df["Previous Week"]     
                df_sorted = df.sort_values(by="Mix % Last", ascending=False)


                # Show results
                st.subheader(f"🏪 {store_name} - {title} - {date}")
                st.dataframe(df,use_container_width=True)

                pdf_buffer = BytesIO()
                with PdfPages(pdf_buffer) as pdf_pages:
                    fig, ax = plt.subplots(figsize=(12, 6))
                    names = df_sorted["Name"]
                    x = np.arange(len(names))
                    wraped_names = [name.replace(" ", "\n") if len(name) > 12 else name for name in names]
                    gap = 0.6
                    # Plotting
                    names = df_sorted["Name"]
                    x = np.arange(len(names))
                
                    gap = 0.6  # space between groups
                    x = np.arange(len(names)) * (1 + gap)
                    
                    width = 0.2

                    fig, ax = plt.subplots(figsize=(9, 5))
                    # Bars
                    bar1 = ax.bar(x - width, df_sorted["Previous Week"], width, label="Previous Week", color="lightgray", edgecolor="black")
                    bar2 = ax.bar(x, df_sorted["Mix % Last"], width, label="Last Week", color="darkgray", edgecolor="black")
                    bar3 = ax.bar(x + width, df_sorted["Improvement"], width, label="Improvement", color="green", edgecolor="black")

                    # Labels and styling
                    ax.set_ylabel("Mix %")
                    ax.set_title(f"Mix % Comparison by Team Member - {store_name} - {date}")
                    ax.set_xticks(x)
                    ax.set_xticklabels(wraped_names, fontsize=9, fontfamily='monospace')
                    plt.subplots_adjust(bottom=0.25)
                    ax.legend()
                    ax.grid(True, linestyle="--", axis="y", alpha=0.5)

                    # Display in Streamlit
                    pdf_pages.savefig(fig)
                    fig.tight_layout()
                    st.pyplot(fig)
                    plt.close(fig)

                with tab1:
                    st.download_button(
                    label="📄 Download report as PDF",
                    data=pdf_buffer.getvalue(),
                    file_name="SO_report.pdf",
                    mime="application/pdf"
                )
                with tab2:
                    st.markdown("Enter your email below to receive the report directly in your inbox.")
                    recipient_email = st.text_input("Recipient Email Address")
                    st.caption("Please ensure you enter a valid email address. Your email will not be stored or used for any other purpose.")
                    if st.button("Send Report"):
                        if not recipient_email:
                            st.warning("Please enter an email address.")
                        elif not validate_email(recipient_email):
                            st.error("❌ Please enter a valid email address.")
                        else:
                            try:
                                report_filename = f"{store_name}_SingleOrigin.pdf"
                                with open(report_filename, "wb") as f:
                                    f.write(pdf_buffer.getvalue())
                                config = get_email_config()
                                success = send_email_with_reports(
                                sender_email=config["sender_email"],
                                sender_password=config["sender_password"],
                                smtp_server=config["smtp_server"],
                                smtp_port=config["smtp_port"],
                                recipient_email=recipient_email,
                                subject="📊 Your Report from the Waste & Sales Tool",
                                body=f'''Hi there! Attached is your report for {store_name} ({date})\n.
                                \nBest Regards,\nThe Waste & Sales Tool Bot\n\n\nPlease do not reply to this email, it is sent from an unmonitored address.''',
                                pdf_paths=[report_filename]
                            )
                                if success:
                                    st.success("📬 Report sent successfully!")
                                    os.remove(report_filename)
    
                            except Exception as e:
                                st.error(f"Failed to send email: {e}")


    except Exception as e:
        st.error(f"Error processing the file: {e}")
        st.stop()

st.caption(""":male-technologist: **Developed by** [Alexander Vindel](https://github.com/j-alex-vindel)""")