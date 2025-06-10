import streamlit as st
import pdfplumber
import pandas as pd
import matplotlib.pyplot as plt
import re
from io import BytesIO
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime

# --- Helper functions ---
def is_all_caps(text):
    return text.isupper()

def is_numeric_row(row):
    return all(re.fullmatch(r'[\d,.]*', str(cell).strip()) for cell in row if cell)

def is_valid_text(text):
    return bool(re.search(r'[a-zA-Z]', text)) and not is_all_caps(text)

# Known pastry products
pastry_keywords = [
    "Almond Croissant", "Apricot Croissant", "Vegan Raspberry Croissant",
    "Pain Au Chocolat", "Pain Au Raisin", "Cinnamon Swirl", "Butter Croissant"
]

# --- Streamlit app ---
st.title("📉 Weekly Waste Report Analyzer Tool")
uploaded_file = st.file_uploader("Upload your PDF report - 4 Weekly Food Sales - (Colin)", type="pdf")

if uploaded_file:
    try:
        clean_rows = []
        first_date = last_date = store_name = None
        parsed_dates = []
        raw_date = None

        with pdfplumber.open(uploaded_file) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if page_num == 0 and text:
                    store_match = re.search(r"Store Name:\s*(.*)", text)
                    if store_match:
                        store_name = store_match.group(1).strip()
                      # Match flexible date formats like '5 May 2025' or '05/05/2025'
                    date_matches = re.findall(r"\b(\d{1,2}[ /.-](?:\w+|\d{1,2})[ /.-]\d{4})\b", text)
                    for raw_date in date_matches:
                        try:
                            parsed = datetime.strptime(raw_date, "%d %B %Y")
                        except:
                            try:
                                parsed = datetime.strptime(raw_date, "%d/%m/%Y")
                            except:
                                continue
                        parsed_dates.append(parsed)
                    for table in page.extract_tables():
                        for i, row in enumerate(table):
                            if i == 0 and "Last 4 Weeks" in row:
                                raw_date = [date for date in row if date != None]
                
                for table in page.extract_tables():
                    for row in table:
                        if not row or not row[0]:
                            continue
                        first_cell = str(row[0]).strip()
                        if is_all_caps(first_cell) or is_numeric_row(row):
                            continue
                        if is_valid_text(first_cell):
                            clean_rows.append(row)

        if not clean_rows:
            st.error("No valid data found in the uploaded PDF.")
        else:
            raw_date.pop()
            clean_date = [raw_date[0],raw_date[-1]]
            df = pd.DataFrame(clean_rows)
            df.columns = [f"col{i+1}" for i in range(len(df.columns))]

            df["Item"] = df["col1"].str.replace(r"\s+", " ", regex=True).str.strip()
            df["is_pastry"] = df["Item"].str.lower().str.contains(
                "|".join([re.escape(name.lower()) for name in pastry_keywords])
            )

            df[["col10", "col11"]] = df[["col10", "col11"]].apply(pd.to_numeric, errors="coerce")
            df = df.rename(columns={"col10": "Sold", "col11": "Waste"})
            df = df[["Item", "is_pastry", "Sold", "Waste"]].dropna(subset=["Sold", "Waste"])
            df["Waste_pct"] = (df["Waste"] / (df["Sold"] + df["Waste"]) * 100).round(2)

            # Extract and format date range
            if parsed_dates:
                parsed_dates.sort()
                first_date = parsed_dates[0].strftime("%d %b %Y")
                last_date = parsed_dates[-1].strftime("%d %b %Y")
                date_range_str = f"{first_date} – {last_date}"
            else:
                date_range_str = ""

            df_pastries = df[df["is_pastry"]].copy()
            df_non_pastries = df[~df["is_pastry"]].copy()

            top10_non_pastries = df_non_pastries.sort_values(by="Waste_pct", ascending=False).head(10)
            top10_pastries = df_pastries.sort_values(by="Waste_pct", ascending=False).head(10)

            subheader = f"Top 10 Most Wasted Products – {store_name}" if store_name else "Top 10 Most Wasted Products"
            st.subheader(subheader)
            if date_range_str:
                st.caption(f"Data from {clean_date[1]} to {clean_date[0]}")
            
            st.dataframe(top10_non_pastries[["Item","Sold", "Waste", "Waste_pct"]], use_container_width=True)

            # --- Create PDF for both charts ---
            pdf_buffer = BytesIO()
            with PdfPages(pdf_buffer) as pdf:
                # Non-pastry chart
                fig1, ax1 = plt.subplots(figsize=(9, 5))
                bars1 = ax1.barh(top10_non_pastries["Item"], top10_non_pastries["Waste_pct"], color="gray", edgecolor="black")
                for bar in bars1:
                    ax1.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2, f"{bar.get_width():.1f}%", va='center')
                ax1.set_title(f"Top 10 Most Wasted Products\n{store_name or ''}\n{clean_date[1] or ''} – {clean_date[0] or ''}", fontsize=14)
                ax1.set_xlabel("Waste %")
                ax1.set_ylabel("Product")
                ax1.invert_yaxis()
                ax1.grid(True, linestyle="--", alpha=0.5)
                fig1.tight_layout()
                pdf.savefig(fig1)
                st.pyplot(fig1)  # Show the figure in Streamlit
                plt.close(fig1)

                # Pastry chart
                if not top10_pastries.empty:
                    subheader_pastries = f"Top 10 Most Wasted Pastries – {store_name}" if store_name else "Top 10 Most Wasted Pastries"
                    st.subheader(subheader_pastries)
                    st.dataframe(top10_pastries[["Item", "Sold", "Waste", "Waste_pct"]], use_container_width=True)
                    fig2, ax2 = plt.subplots(figsize=(9, 5))
                    bars2 = ax2.barh(top10_pastries["Item"], top10_pastries["Waste_pct"], color="lightgray", edgecolor="black")
                    for bar in bars2:
                        ax2.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2, f"{bar.get_width():.1f}%", va='center')
                    ax2.set_title(f"Top 10 Most Wasted Pastries\n{store_name or ''}\n{clean_date[1] or ''} – {clean_date[0] or ''}", fontsize=14)
                    ax2.set_xlabel("Waste %")
                    ax2.set_ylabel("Pastry Item")
                    ax2.invert_yaxis()
                    ax2.grid(True, linestyle="--", alpha=0.5)
                    fig2.tight_layout()
                    pdf.savefig(fig2)
                    st.pyplot(fig2)
                    plt.close(fig2)

            st.download_button(
                label="📄 Download charts as PDF",
                data=pdf_buffer.getvalue(),
                file_name="waste_charts_report.pdf",
                mime="application/pdf"
            )

    except Exception as e:
        st.error(f"An error occurred: {e}")



st.caption(""":male-technologist: **Developed by** [Alexander Vindel](https://github.com/j-alex-vindel)""")