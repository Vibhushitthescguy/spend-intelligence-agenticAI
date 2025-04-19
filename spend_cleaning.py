import pandas as pd

def clean_data(df):
    # Standardize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # Rename supplier column for ease
    if 'supplier/supplying_plant' in df.columns:
        df.rename(columns={'supplier/supplying_plant': 'supplier'}, inplace=True)

    # Basic cleaning
    df.dropna(subset=['material', 'net_price'], inplace=True)
    df = df[df['net_price'] > 0]

    # Total spend calculation
    if 'order_quantity' in df.columns:
        df['total_spend'] = df['order_quantity'] * df['net_price']
    else:
        df['total_spend'] = df['net_price']

    return df

def analyze_fragmentation(df):
    frag_df = (
        df.groupby(['material', 'short_text'])['supplier']
        .nunique()
        .reset_index()
        .rename(columns={'supplier': 'unique_suppliers'})
    )
    frag_df = frag_df[frag_df['unique_suppliers'] > 2]
    return frag_df

def analyze_price_variance(df):
    price_var_df = (
        df.groupby(['material', 'short_text'])['net_price']
        .agg(['count', 'nunique', 'min', 'max', 'mean'])
        .reset_index()
        .rename(columns={
            'count': 'purchase_count',
            'nunique': 'price_points',
            'min': 'min_price',
            'max': 'max_price',
            'mean': 'avg_price'
        })
    )
    price_var_df['variance_pct'] = (
        (price_var_df['max_price'] - price_var_df['min_price']) / price_var_df['min_price']
    ) * 100
    price_var_df = price_var_df[price_var_df['price_points'] > 1]
    return price_var_df

def summarize_categories(df):
    category_spend = (
        df.groupby('material_group')['total_spend']
        .sum()
        .reset_index()
        .sort_values(by='total_spend', ascending=False)
    )
    category_spend['spend_share_pct'] = (
        category_spend['total_spend'] / category_spend['total_spend'].sum()
    ) * 100
    category_spend['cumulative_share'] = category_spend['spend_share_pct'].cumsum()
    return category_spend

def generate_insights(frag_df, price_var_df, category_spend):
    insights = []

    frag_count = frag_df.shape[0]
    high_var_count = price_var_df[price_var_df['variance_pct'] > 10].shape[0]
    top_cat = category_spend.iloc[0]
    top_20_cats = category_spend[category_spend['cumulative_share'] <= 80].shape[0]

    insights.append(f"{frag_count} materials are purchased from >2 suppliers — consider consolidation.")
    insights.append(f"{high_var_count} materials show >10% price variance — review pricing consistency.")
    insights.append(f"Top category: {top_cat['material_group']} with AED {top_cat['total_spend']:,.2f} spend.")
    insights.append(f"{top_20_cats} categories account for 80% of spend — focus sourcing strategy.")

    return insights

