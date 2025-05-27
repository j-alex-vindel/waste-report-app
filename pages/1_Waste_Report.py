import streamlit as st
import pdfplumber
import pandas as pd
import matplotlib.pyplot as plt
import re
from io import BytesIO

# Helper to deduplicate column names
def deduplicate_columns(columns):
    seen = {}
    new_cols = []
    for col in columns:
        col = str(col).strip()
        if col in seen:
            seen[col] += 1
            new_cols.append(f"{col}.{seen[col]}")
        else:
            seen[col] = 0
            new_cols.append(col)
    return new_cols

# Excluded subtotal/category names
excluded_items = {
    "BREAKFAST SAVOURY", "BREAKFAST ROLLS/SANDWICHES", "FILLED CROISSANTS", "COLD SAVOURY", "SALAD",
    "DOG TREATS", "FRUIT", "FRUIT POTS", "HOT SAVOURY", "SOUP", "TARTS, ROLLS & QUICHE",
    "LARGE CAKES", "BUNS & CHOUXNUTS", "CHEESECAKES", "SLICED CAKES", "MUFFINS",
    "PORRIDGE", "SANDWICHES", "DELI SANDWICH", "FOCACCIA",
    "PANINI", "TOSTATI", "WEDGE", "SAVOURY SNACKING", "CRISPS", "FRUIT AND NUT",
    "POPCORN", "SMALL CAKES", "SCONES", "TRAYBAKES/SLICES", "SWEET SNACKING",
    "CONFECTIONERY", "WRAPPED BISCUITS", "WRAPPED CAKES"
}

# Streamlit UI
st.title("📉 Weekly Waste Report Analyzer")
uploaded_file = st.file_uploader("Upload your PDF report", type="pdf")

if uploaded_file:
    try:
         # --- Validate that it's the correct sales report ---
        with pdfplumber.open(uploaded_file) as pdf:
            first_page_text = pdf.pages[0].extract_text()

        expected_title = "4 Weekly Food Sales by Store"
        if expected_title not in first_page_text:
            st.error("❌ This does not appear to be a valid '4 Weekly Food Sales by Store' report.")
            st.stop()
        # Extract store name from line starting with "Store Name:"
        store_name = "Unknown Store"
        for line in first_page_text.splitlines():
            if line.startswith("Store Name:"):
                store_name = line.split("Store Name:")[1].strip()
                break

        # --- Extract tables ---
        tables = []
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                for table in page.extract_tables():
                    if table and len(table) > 2:
                        header = table[1]
                        df = pd.DataFrame(table[2:], columns=header)
                        df.columns = deduplicate_columns(df.columns)
                        tables.append(df)

        if not tables:
            st.error("No tables found in the uploaded PDF.")
        else:
            raw_table = pd.concat(tables, ignore_index=True)
            raw_table.dropna(how='all', inplace=True)

            # Select last week's Sold and Wasted columns
            sold_cols = [col for col in raw_table.columns if "Sold" in col]
            wasted_cols = [col for col in raw_table.columns if "Wasted" in col]
            last_sold = sold_cols[-1]
            last_wasted = wasted_cols[-1]

            df = raw_table[[raw_table.columns[0], last_sold, last_wasted]].copy()
            df.columns = ["Item", "Sold", "Wasted"]
            df.reset_index(drop=True, inplace=True)

            # Normalize item names early
            df["Item"] = df["Item"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
          

            # Filter subtotal/group/header rows
            df = df[df["Item"].notna()]
            df = df[~df["Item"].isin(["None", "", None])]
            df = df[df["Item"].str.lower() != "item"]
            df = df[df["Item"].str.lower() != "header"]
            df = df[~df["Item"].str.upper().isin(excluded_items)]
            df = df[~df["Item"].str.match(r'^[A-Z0-9\s&/,\-]+$', na=False)]

            # Convert numeric columns
            df[["Sold", "Wasted"]] = df[["Sold", "Wasted"]].apply(pd.to_numeric, errors='coerce')
            df = df[(df["Sold"] + df["Wasted"]) > 0]

            # Calculate Waste %
            df["Waste %"] = (df["Wasted"] / (df["Sold"] + df["Wasted"]) * 100).round(2)

            # --- Filter (C) and non-(C) using regex ---
            df["Item_clean"] = df["Item"].str.replace(r"\s+", " ", regex=True).str.strip()
            non_c_items = df[~df["Item"].str.replace(r"\s+", " ", regex=True)
                              .str.strip()
                              .str.match(r".*\(C\)$", flags=re.IGNORECASE)]
            # --- Top 10 Non-(C) Waste Products ---
            top10 = non_c_items.sort_values(by="Waste %", ascending=False).head(10)
            st.markdown(f"### 🏬 Store: **{store_name}**")
            st.subheader("Top 10 Most Wasted Products by Waste % (excluding Pastries)")
            st.dataframe(top10[["Item", "Sold", "Wasted", "Waste %"]])

            fig, ax = plt.subplots()
            bars = ax.barh(top10["Item"], top10["Waste %"], color="orange")
            ax.set_xlabel("Waste %")
            ax.set_ylabel("Product")
            ax.invert_yaxis()
            ax.set_title(f"Top 10 Waste % (Non Pastries) - {store_name}")

            # Add value labels to the right of each bar
            for bar in bars:
                width = bar.get_width()
                ax.text(width / 2,
                        bar.get_y() + bar.get_height() / 2,
                        f"{width:.1f}%",
                        ha='center', va='center', fontsize=10, color='black')

            # Render chart in Streamlit
            st.pyplot(fig)

            # Save chart to BytesIO
            img_buffer = BytesIO()
            fig.savefig(img_buffer, format='png', bbox_inches='tight')
            img_buffer.seek(0)

            # Download button
            st.download_button(
                label="📸 Download Chart as PNG",
                data=img_buffer,
                file_name="top10_waste_chart.png",
                mime="image/png"
            )

    except Exception as e:
        st.error(f"Something went wrong:\n\n{e}")