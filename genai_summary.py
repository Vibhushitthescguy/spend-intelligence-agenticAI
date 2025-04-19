# genai_summary.py
import openai
openai.api_key = "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"

def generate_procurement_summary(insights, top_variance_df, top_fragment_df):
    top_var_items = top_variance_df[['short_text', 'variance_pct']].head(5).to_dict(orient='records')
    top_frag_items = top_fragment_df[['short_text', 'unique_suppliers']].head(5).to_dict(orient='records')

    prompt = f"""
    You are a senior procurement consultant. Based on the data below, generate a 5-bullet strategic summary:
    - Core insights: {insights}
    - Top price variance items: {top_var_items}
    - Top fragmented items: {top_frag_items}

    Use business-friendly language. Suggest opportunities or risks. Avoid technical jargon.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful procurement assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response['choices'][0]['message']['content']
