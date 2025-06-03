import streamlit as st
import pdfplumber
import pandas as pd
import matplotlib.pyplot as plt
import re
from io import BytesIO

# Streamlit UI
st.title("📉 Weekly Waste Report Analyzer")
uploaded_file = st.file_uploader("Upload your PDF report", type="pdf")

# Pastry keywords
pastry_keywords = [
    "Almond Croissant", "Apricot Croissant", "Vegan Raspberry Croissant",
    "Pain Au Chocolat", "Pain Au Raisin", "Cinnamon Swirl", "Butter Croissant"
]

# Helper functions
def is_all_caps(text):
    return text.isupper()

def is_numeric_row(row):
    return all(re.fullmatch(r'[\d,.]*', str(cell).strip()) for cell in row if cell)

def is_valid_text(text):
    return bool(re.search(r'[a-zA-Z]', text)) and not is_all_caps(text)

if uploaded_file:
    try:
        clean_rows = []
        store_name = None

        with pdfplumber.open(uploaded_file) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if page_num == 0 and text:
                    match = re.search(r"Store Name:\s*(.*)", text)
                    if match:
                        store_name = match.group(1).strip()

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
            st.error("No valid rows found in the uploaded PDF.")
        else:
            df_cleaned = pd.DataFrame(clean_rows)
            df_cleaned.columns = [f"col{i+1}" for i in range(len(df_cleaned.columns))]

            df_cleaned["Item_clean"] = df_cleaned["col1"].str.replace(r"\s+", " ", regex=True).str.strip()
            pastry_pattern = "|".join([re.escape(name.lower()) for name in pastry_keywords])
            df_cleaned["is_pastry"] = df_cleaned["Item_clean"].str.lower().str.contains(pastry_pattern)

            df_cleaned[["col10", "col11"]] = df_cleaned[["col10", "col11"]].apply(pd.to_numeric, errors="coerce")
            df_cleaned = df_cleaned[["Item_clean", "is_pastry", "col10", "col11"]]
            df_cleaned.rename(columns={"Item_clean": "Item", "col10": "Sold", "col11": "Waste"}, inplace=True)
            df_cleaned["Waste_pct"] = (df_cleaned["Waste"] / (df_cleaned["Sold"] + df_cleaned["Waste"]) * 100).round(2)

            df_pastries = df_cleaned[df_cleaned["is_pastry"]].copy()
            df_non_pastries = df_cleaned[~df_cleaned["is_pastry"]].copy()

            top10_non_pastries = df_non_pastries.sort_values(by="Waste_pct", ascending=False).head(10)
            top10_pastries = df_pastries.sort_values(by="Waste_pct", ascending=False).head(10)

            # Main report header
            st.subheader(f"Top 10 Most Wasted Products{' – ' + store_name if store_name else ''}")
            st.dataframe(top10_non_pastries[["Item", "Sold", "Waste", "Waste_pct"]])

            # Chart for non-pastries
            fig, ax = plt.subplots()
            bars = ax.barh(top10_non_pastries["Item"], top10_non_pastries["Waste_pct"], color="orange")
            for bar in bars:
                width = bar.get_width()
                ax.text(width - 2, bar.get_y() + bar.get_height() / 2, f"{width:.1f}%", va='center', ha='right', color='white', fontsize=9)
            ax.set_xlabel("Waste %")
            ax.set_ylabel("Product")
            ax.invert_yaxis()
            st.pyplot(fig)

            # Download button
            buf1 = BytesIO()
            fig.savefig(buf1, format="png", bbox_inches="tight")
            buf1.seek(0)
            st.download_button("📥 Download Non-Pastry Chart", data=buf1, file_name="non_pastry_chart.png", mime="image/png")

            # Pastry report
            if not df_pastries.empty:
                st.subheader("🥐 Pastry Waste Overview")
                st.dataframe(top10_pastries[["Item", "Sold", "Waste", "Waste_pct"]])

                fig2, ax2 = plt.subplots()
                bars2 = ax2.barh(top10_pastries["Item"], top10_pastries["Waste_pct"], color="steelblue")
                for bar in bars2:
                    width = bar.get_width()
                    ax2.text(width - 2, bar.get_y() + bar.get_height() / 2, f"{width:.1f}%", va='center', ha='right', color='white', fontsize=9)
                ax2.set_xlabel("Waste %")
                ax2.set_ylabel("Pastry Item")
                ax2.invert_yaxis()
                st.pyplot(fig2)

                # Download button for pastry chart
                buf2 = BytesIO()
                fig2.savefig(buf2, format="png", bbox_inches="tight")
                buf2.seek(0)
                st.download_button("📥 Download Pastry Chart", data=buf2, file_name="pastry_chart.png", mime="image/png")
            else:
                st.info("No pastries found matching expected names.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
