# spend_cleaning.py (Hard-coded Currency Rates, Syntax Corrected)
import pandas as pd

# === Hard-coded FX rates into AED ===
# Update these values as needed
RATES = {
    "AED": 1.0,
    "USD": 3.67,
    "EUR": 4.00,
    "GBP": 4.89,
    # add other currencies here as required
}

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    1. Normalize column names
    2. Fill missing core fields
    3. Convert `net_order_value` from any currency into AED using hard-coded rates
    4. Tag each row with its calendar year
    5. Return the full DataFrame with `total_spend` in AED
    """
    # 1) Copy & normalize headers
    df = df.copy()
    df.columns = (
        df.columns
          .str.strip()
          .str.lower()
          .str.replace(" ", "_", regex=False)
    )
    if "supplier/supplying_plant" in df.columns:
        df = df.rename(columns={"supplier/supplying_plant": "supplier"})

    # 2) Fill missing core fields
    df.loc[:, "currency"] = (
        df.get("currency", pd.Series("AED", index=df.index))
          .fillna("AED")
    )
    df.loc[:, "net_order_value"] = (
        df.get("net_order_value", pd.Series(0.0, index=df.index))
          .fillna(0.0)
    )
    df.loc[:, "material_group"] = (
        df.get("material_group", pd.Series("Unknown", index=df.index))
          .fillna("Unknown")
    )
    df.loc[:, "material"] = (
        df.get("material", pd.Series("", index=df.index))
          .fillna("")
    )
    df.loc[:, "short_text"] = (
        df.get("short_text", pd.Series("", index=df.index))
          .fillna("")
    )

    # 3) Apply hard-coded FX conversion
    df.loc[:, "rate_to_aed"] = df["currency"].map(RATES).fillna(1.0)
    df.loc[:, "total_spend"] = df["net_order_value"] * df["rate_to_aed"]

    # 4) Extract calendar year
    if "posting_date" in df.columns:
        df.loc[:, "posting_date"] = pd.to_datetime(
            df["posting_date"], errors="coerce"
        )
        today_year = pd.to_datetime("today").year
        df.loc[:, "year"] = (
            df["posting_date"].dt.year.fillna(today_year).astype(int)
        )
    else:
        df.loc[:, "year"] = pd.to_datetime("today").year

    return df


def analyze_fragmentation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identify materials sourced from >2 unique suppliers.
    """
    frag = (
        df.groupby(["material", "short_text"]) ["supplier"]
          .nunique()
          .reset_index()
          .rename(columns={"supplier": "unique_suppliers"})
    )
    return frag[frag["unique_suppliers"] > 2]


def analyze_price_variance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute min/max/avg and variance % on AED-normalized `total_spend`.
    """
    var = (
        df.groupby(["material", "short_text"]) ["total_spend"]
          .agg([
            ("purchase_count", "count"),
            ("min_price", "min"),
            ("max_price", "max"),
            ("avg_price", "mean"),
          ])
          .reset_index()
    )
    var.loc[:, "variance_pct"] = (
        (var["max_price"] - var["min_price"]) / var["min_price"]
    ) * 100
    return var[var["purchase_count"] > 1]


def summarize_categories(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pareto-style summary of spend by `material_group`.
    """
    cat = (
        df.groupby("material_group")["total_spend"]
          .sum()
          .reset_index()
          .sort_values("total_spend", ascending=False)
    )
    total = cat["total_spend"].sum()
    cat.loc[:, "spend_share_pct"] = (cat["total_spend"] / total) * 100
    cat.loc[:, "cumulative_share"] = cat["spend_share_pct"].cumsum()
    return cat


def generate_insights(
    frag_df: pd.DataFrame,
    price_var_df: pd.DataFrame,
    category_spend: pd.DataFrame
) -> list[str]:
    """
    Turn key metrics into human-friendly bullet points.
    """
    insights = []
    frag_count = frag_df.shape[0]
    high_var_count = (price_var_df["variance_pct"] > 10).sum()
    top_cat = category_spend.iloc[0]
    top_20_cats = (category_spend["cumulative_share"] <= 80).sum()

    insights.append(
        f"{frag_count} materials are purchased from >2 suppliers — consider consolidation."
    )
    insights.append(
        f"{high_var_count} materials show >10% price variance — review pricing consistency."
    )
    insights.append(
        f"Top category: {top_cat['material_group']} with AED {top_cat['total_spend']:,.2f} spend."
    )
    insights.append(
        f"{top_20_cats} categories account for 80% of spend — focus sourcing strategy."
    )
    return insights
