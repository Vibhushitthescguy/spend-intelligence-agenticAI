import pandas as pd

# Step 1: Load Excel
file_path = "Procurement spend data for FY 24.xlsx"
df = pd.read_excel(file_path, sheet_name="Sheet1")

# Step 2: Clean column names (remove spaces, lowercase)
df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

# Step 3: Create total_spend column
df['total_spend'] = df['order_quantity'] * df['net_price']

# Step 4: Show result
print(df[['material', 'short_text', 'supplier/supplying_plant', 'order_quantity', 'net_price', 'total_spend']].head())
# Step 5: Fragmentation Analysis
fragmented_df = (
    df.groupby(['material', 'short_text'])['supplier/supplying_plant']
    .nunique()
    .reset_index()
    .rename(columns={'supplier/supplying_plant': 'unique_suppliers'})
)

# Filter: Materials with more than 2 suppliers
fragmented_df = fragmented_df[fragmented_df['unique_suppliers'] > 2]

# Show top fragmented items
print("\n🔍 Fragmented Spend Items:")
print(fragmented_df.sort_values(by='unique_suppliers', ascending=False).head(10))
# Step 6: Price Variance Analysis
price_var_df = (
    df.groupby(['material', 'short_text'])['net_price']
    .agg(['count', 'nunique', 'min', 'max', 'mean'])
    .reset_index()
)

price_var_df = price_var_df.rename(columns={
    'count': 'purchase_count',
    'nunique': 'price_points',
    'min': 'min_price',
    'max': 'max_price',
    'mean': 'avg_price'
})

# Add variance % column
price_var_df['variance_pct'] = (
    (price_var_df['max_price'] - price_var_df['min_price']) / price_var_df['min_price']
) * 100

# Filter: Only items with multiple price points
price_var_df = price_var_df[price_var_df['price_points'] > 1]

# Show top price variance cases
print("\n📈 Price Variance Detected:")
print(price_var_df.sort_values(by='variance_pct', ascending=False).head(10))
# Step 7: Category-wise Spend Summary
category_spend = (
    df.groupby('material_group')['total_spend']
    .sum()
    .reset_index()
    .sort_values(by='total_spend', ascending=False)
)

# Optional: Add % share and cumulative share for Pareto
category_spend['spend_share_pct'] = (category_spend['total_spend'] / category_spend['total_spend'].sum()) * 100
category_spend['cumulative_share'] = category_spend['spend_share_pct'].cumsum()

# Show top categories
print("\n🏷️ Category-wise Spend Summary:")
print(category_spend.head(10))
# Step 8: Generate Smart Recommendations

print("\n🧠 SMART RECOMMENDATIONS:")

# Fragmented Materials
frag_count = fragmented_df.shape[0]
if frag_count > 0:
    print(f"- Detected {frag_count} materials purchased from more than 2 suppliers. Consider consolidating vendors to improve negotiation and reduce processing effort.")

# Price Variance
high_var_count = price_var_df[price_var_df['variance_pct'] > 10].shape[0]
if high_var_count > 0:
    print(f"- {high_var_count} materials show >10% price variance across purchases. Recommend standardizing procurement rates or contract pricing.")

# Category Spend
top_cat = category_spend.iloc[0]
print(f"- Highest spend category is Material Group {top_cat['material_group']} with total spend of AED {top_cat['total_spend']:,.2f}.")

# 80/20 rule check
top_20_cats = category_spend[category_spend['cumulative_share'] <= 80].shape[0]
print(f"- {top_20_cats} categories contribute to 80% of overall spend. Recommend strategic sourcing focus on these.")

print("\n✅ Summary complete. Ready to export as report or visualize in dashboard.")
# Step 9: Export results to Excel
with pd.ExcelWriter("SpendAnalysis_Output.xlsx") as writer:
    df.to_excel(writer, sheet_name="Raw_Data", index=False)
    fragmented_df.to_excel(writer, sheet_name="Fragmentation", index=False)
    price_var_df.to_excel(writer, sheet_name="Price_Variance", index=False)
    category_spend.to_excel(writer, sheet_name="Category_Spend", index=False)

    # Exporting recommendations as a one-column summary sheet
    summary_text = [
        f"SMART RECOMMENDATIONS:",
        f"- {frag_count} items purchased from >2 suppliers → consider consolidation.",
        f"- {high_var_count} items have >10% price variance → price standardization needed.",
        f"- Top category: {top_cat['material_group']} with AED {top_cat['total_spend']:,.2f} spend.",
        f"- {top_20_cats} categories make up 80% of spend → strategic sourcing focus."
    ]
    summary_df = pd.DataFrame({"Insights": summary_text})
    summary_df.to_excel(writer, sheet_name="Summary", index=False)
# Step 10: Export Power BI-ready CSVs
df[['material', 'short_text', 'supplier/supplying_plant', 'order_quantity', 'net_price', 'total_spend', 'material_group', 'plant']].to_csv("ItemSpendDetails.csv", index=False)
fragmented_df.to_csv("Fragmentation.csv", index=False)
price_var_df.to_csv("PriceVariance.csv", index=False)
category_spend.to_csv("Spend_Summary.csv", index=False)

