import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Spend Intelligence Dashboard", layout="wide")

st.markdown("""
    <style>
        .block-container {padding-top: 2rem;}
        h1, h2, h3 { color: #1e3a8a; }
    </style>
""", unsafe_allow_html=True)

st.title("💼 Procurement Spend Intelligence")
st.markdown("This dashboard presents actionable insights based on FY24 procurement spend data.")

uploaded_file = st.file_uploader("📥 Upload `SpendAnalysis_Output.xlsx`", type=["xlsx"])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)

    df_raw = pd.read_excel(xls, sheet_name="Raw_Data")
    df_frag = pd.read_excel(xls, sheet_name="Fragmentation")
    df_var = pd.read_excel(xls, sheet_name="Price_Variance")
    df_cat = pd.read_excel(xls, sheet_name="Category_Spend")
    df_sum = pd.read_excel(xls, sheet_name="Summary")

    st.subheader("🧠 Key Insights")
    for line in df_sum['Insights']:
        st.success(f"✅ {line}")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📦 Top Categories by Spend")
        fig1 = px.bar(df_cat.head(10), x="material_group", y="total_spend", title="Top Spend by Category")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("📈 High Price Variance Items")
        var_thresh = st.slider("Min % variance to highlight", 0, 100, 20)
        df_var_filtered = df_var[df_var['variance_pct'] >= var_thresh]
        fig2 = px.bar(df_var_filtered.sort_values('variance_pct', ascending=False).head(10),
                      x='short_text', y='variance_pct', title="Price Variance %")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("🧩 Fragmented Materials")
    supplier_min = st.slider("Filter: Min # of suppliers", 2, 10, 3)
    frag_filtered = df_frag[df_frag['unique_suppliers'] >= supplier_min]
    st.dataframe(frag_filtered)

    st.subheader("📋 PO Line Items")
    col1, col2, col3 = st.columns(3)
    supplier = col1.selectbox("Filter by Supplier", ["All"] + sorted(df_raw['supplier/supplying_plant'].dropna().unique()))
    plant = col2.selectbox("Filter by Plant", ["All"] + sorted(df_raw['plant'].dropna().unique()))
    mat_grp = col3.selectbox("Filter by Material Group", ["All"] + sorted(df_raw['material_group'].dropna().astype(str).unique()))

    df_filtered = df_raw.copy()
    if supplier != "All":
        df_filtered = df_filtered[df_filtered['supplier/supplying_plant'] == supplier]
    if plant != "All":
        df_filtered = df_filtered[df_filtered['plant'] == plant]
    if mat_grp != "All":
        df_filtered = df_filtered[df_filtered['material_group'].astype(str) == mat_grp]

    st.dataframe(df_filtered)

    # Export button
    st.markdown("### 📤 Export Filtered PO Data")
    def to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Filtered_PO_Data')
        return output.getvalue()

    st.download_button(
        label="Download Excel",
        data=to_excel(df_filtered),
        file_name="Filtered_PO_Data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.warning("Please upload the Excel file to proceed.")
