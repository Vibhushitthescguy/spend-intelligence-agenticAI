# streamlit_dashboard.py (Polished UI + Branded Feel by Vibhushit)
import streamlit as st
import pandas as pd
import plotly.express as px
from spend_cleaning import clean_data, analyze_fragmentation, analyze_price_variance, summarize_categories, generate_insights
from genai_summary import generate_procurement_summary
import openai
import os

# Page config + styling
st.set_page_config(page_title="GenAI-Powered Spend Intelligence", layout="wide")

st.markdown("""
    <style>
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Segoe UI', sans-serif;
    }
    body {
        background-color: #f9f9f9;
        color: #1a1a1a;
        font-family: 'Segoe UI', sans-serif;
    }
    .block-container {
        padding-top: 2rem;
    }
    hr {
        margin-top: 2rem;
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar Branding
st.markdown("# 🤖 GenAI-Powered Spend Intelligence Dashboard")
st.markdown("Delivering smart procurement insights — powered by GPT-4, Streamlit, and automation.")
st.markdown("---")

uploaded_file = st.file_uploader("📥 Upload your PO Data (Excel)", type=["xlsx"])

if uploaded_file:
    if "Output" in uploaded_file.name:
        st.error("🚫 Please upload a raw PO file — not an output file like 'SpendAnalysis_Output.xlsx'")
        st.stop()

    df = pd.read_excel(uploaded_file)
    df = clean_data(df)

    frag_df = analyze_fragmentation(df)
    var_df = analyze_price_variance(df)
    cat_df = summarize_categories(df)
    insights = generate_insights(frag_df, var_df, cat_df)

    st.markdown("## 🧠 Strategic GPT Insights")
    if st.button("🧠 Generate Summary with GPT"):
        ai_summary = generate_procurement_summary(insights, var_df, frag_df)
        st.markdown(ai_summary)
        st.download_button("⬇️ Download GPT Summary", ai_summary.encode('utf-8'), file_name="SpendGPT_Summary.txt")

    st.markdown("---")
    st.markdown("## 📊 Spend Overview")
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Spend (AED)", f"{df['total_spend'].sum():,.0f}")
    kpi2.metric("Unique Materials", df['material'].nunique())
    kpi3.metric("Total Suppliers", df['supplier'].nunique())

    st.markdown("---")
    st.markdown("## 📦 Top Categories by Spend")
    fig_cat = px.bar(cat_df.sort_values(by='total_spend', ascending=False).head(10),
                     x='material_group', y='total_spend',
                     color_discrete_sequence=["#0D6EFD"],
                     title='Top 10 Spend Categories', labels={'total_spend': 'Spend (AED)'})
    st.plotly_chart(fig_cat, use_container_width=True)

    st.markdown("## 🏢 Top Suppliers by Spend")
    top_suppliers = df.groupby('supplier')['total_spend'].sum().reset_index().sort_values(by='total_spend', ascending=False).head(10)
    fig_sup = px.bar(top_suppliers, x='supplier', y='total_spend', title='Top 10 Suppliers by Spend', color_discrete_sequence=["#6610f2"])
    st.plotly_chart(fig_sup, use_container_width=True)

    st.markdown("## 📈 Price Variance Filter")
    min_var, max_var = st.slider("Select Price Variance % Range", 0, 100, (10, 100))
    filtered_var = var_df[(var_df['variance_pct'] >= min_var) & (var_df['variance_pct'] <= max_var)]
    fig_var_simple = px.bar(filtered_var.sort_values(by='variance_pct', ascending=False),
                            x='short_text', y='variance_pct',
                            title=f'Materials with {min_var}%–{max_var}% Price Variance',
                            labels={'short_text': 'Material', 'variance_pct': 'Variance %'},
                            color_discrete_sequence=["#fd7e14"])
    st.plotly_chart(fig_var_simple, use_container_width=True)

    st.markdown("## 🧩 Supplier Concentration by Material Group")
    supplier_concentration = df.groupby(['material_group'])['supplier'].nunique().reset_index()
    supplier_concentration.columns = ['material_group', 'unique_suppliers']

    def risk_level(suppliers):
        if suppliers > 5:
            return 'High'
        elif suppliers > 2:
            return 'Medium'
        else:
            return 'Low'

    supplier_concentration['risk_level'] = supplier_concentration['unique_suppliers'].apply(risk_level)
    color_map = {'High': 'red', 'Medium': 'orange', 'Low': 'green'}
    supplier_concentration['color'] = supplier_concentration['risk_level'].map(color_map)

    fig_concentration = px.bar(supplier_concentration.sort_values(by='unique_suppliers', ascending=False),
                               x='material_group', y='unique_suppliers', color='risk_level',
                               color_discrete_map=color_map,
                               title='Unique Suppliers per Material Group')
    st.plotly_chart(fig_concentration, use_container_width=True)

    st.markdown("## 🚨 High Risk Category Alerts")
    risky_cats = supplier_concentration[supplier_concentration['risk_level'] == 'High']
    if not risky_cats.empty:
        st.dataframe(risky_cats[['material_group', 'unique_suppliers', 'risk_level']])
        st.download_button("⬇️ Download Risk Categories", risky_cats.to_csv(index=False), file_name="high_risk_categories.csv")
        risk_text = risky_cats[['material_group', 'unique_suppliers']].to_dict(orient='records')
        prompt = f"You are a senior procurement strategist. Review these high-risk material groups and write a 5-bullet strategic recommendation:\n{risk_text}"
        gpt_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a senior procurement advisor."},
                {"role": "user", "content": prompt}
            ]
        )
        st.markdown("### 🧠 GPT Recommendations for High-Risk Groups")
        st.markdown(gpt_response['choices'][0]['message']['content'])
    else:
        st.success("✅ No high-risk fragmentation found across categories.")

    st.markdown("## 🗓️ Monthly PO Volume")
    if 'posting_date' in df.columns:
        df['month'] = pd.to_datetime(df['posting_date']).dt.to_period('M')
        po_vol = df.groupby('month')['material'].count().reset_index()
        po_vol.columns = ['month', 'PO_count']
        fig_po = px.line(po_vol, x='month', y='PO_count', title='PO Volume Over Time', color_discrete_sequence=["#198754"])
        st.plotly_chart(fig_po, use_container_width=True)

    with st.expander("📋 View Raw Cleaned PO Data"):
        st.dataframe(df.head(100))

    with st.expander("🧩 Fragmentation Table"):
        st.dataframe(frag_df)

    with st.expander("💸 Price Variance Table"):
        st.dataframe(var_df)

    with st.expander("📊 Category Spend Table"):
        st.dataframe(cat_df)

    st.markdown("## 💬 Ask the Spend Agent")
    user_question = st.text_input("Ask a question about this spend data:")
    if user_question:
        chat_prompt = f"""
        You are a helpful procurement analyst. Based on these insights:
        {insights}

        And data flags:
        - Top price variance items: {var_df[['short_text', 'variance_pct']].head(5).to_dict(orient='records')}
        - Top fragmented items: {frag_df[['short_text', 'unique_suppliers']].head(5).to_dict(orient='records')}

        Answer the user's question:
        {user_question}
        """
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a procurement data assistant."},
                {"role": "user", "content": chat_prompt}
            ]
        )
        st.markdown(f"**🗨️ GPT Response:** {response['choices'][0]['message']['content']}")

    st.markdown("""
    <hr style='margin-top: 2rem;'>
    <p style='text-align:center; font-size:0.8rem;'>
        Built with ❤️ by Vibhushit • Powered by GPT-4 + Streamlit
    </p>
    """, unsafe_allow_html=True)

else:
    st.info("📁 Please upload an Excel file to begin analysis.")
