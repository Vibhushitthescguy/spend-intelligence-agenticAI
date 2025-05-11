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
