import streamlit as st
import pandas as pd
import plotly.express as px
import tempfile
import pdfkit
import os

# --- Force Dark Theme ---
st.set_page_config(page_title="Innovation Policy Dashboard", layout="wide", initial_sidebar_state="auto")

# Inject custom CSS for dark theme
st.markdown("""
    <style>
    html, body, [class*="css"]  {
        background-color: #0e1117;
        color: #ffffff;
    }
    table {
        color: white !important;
    }
    .stDataFrame div[data-testid="stDataFrame"] {
        background-color: #1e222a;
    }
    h1, h2, h3, h4, h5 {
        color: #ffffff;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Innovation Scores and Legal Frameworks")

st.markdown("""
### 🔎 What This Dashboard Shows

- 📊 **Jurisdiction-specific innovation scores** from Final Draft (Section 4)
- 📜 **Relevant laws & barriers** by jurisdiction and industry
- 📄 Export results as a PDF report (works locally)
""")

# --- Industry List ---
industries = ["All Industries", "Luxury", "Entertainment", "Pharmaceuticals", "Technology", "Fintech"]
selected_industry = st.selectbox("Select industry:", industries)

# --- Official Innovation Scores ---
data = {
    "Jurisdiction": ["United States", "European Union", "United Kingdom", "Canada"],
    "Luxury": [8.3, 8.5, 8.2, 6.9],
    "Entertainment": [8.8, 8.4, 8.1, 6.7],
    "Pharmaceuticals": [9.0, 8.3, 8.0, 7.1],
    "Technology": [8.5, 8.4, 8.2, 7.3],
    "Fintech": [8.1, 8.3, 8.8, 6.7]
}
score_df = pd.DataFrame(data)

tooltip_notes = {
    "United States": "Strong IP enforcement and flexible privacy laws (CCPA), but lacks unified federal privacy law.",
    "European Union": "GDPR and harmonized IP regime provide predictability, but high compliance burdens.",
    "United Kingdom": "Strong fintech support and agile regulation, but post-Brexit uncertainty affects cross-border alignment.",
    "Canada": "Outdated IP enforcement and slow reform (Bill C-27) reduce legal clarity and innovation incentives."
}
score_df["Explanation"] = score_df["Jurisdiction"].map(tooltip_notes)

if selected_industry == "All Industries":
    score_df["Innovation Score"] = score_df[["Luxury", "Entertainment", "Pharmaceuticals", "Technology", "Fintech"]].mean(axis=1)
    display_title = "All Industries"
else:
    score_df["Innovation Score"] = score_df[selected_industry]
    display_title = selected_industry

selected_jurisdictions = st.multiselect(
    "Filter jurisdictions:",
    score_df["Jurisdiction"].tolist(),
    default=score_df["Jurisdiction"].tolist()
)
filtered_scores = score_df[score_df["Jurisdiction"].isin(selected_jurisdictions)][["Jurisdiction", "Innovation Score", "Explanation"]]

# --- Bar Chart ---
st.subheader(f"📊 Innovation Scores – {display_title}")
fig = px.bar(
    filtered_scores.sort_values("Innovation Score", ascending=False),
    x="Jurisdiction",
    y="Innovation Score",
    color="Innovation Score",
    color_continuous_scale="blues",
    template="plotly_dark",
    hover_data={"Jurisdiction": True, "Innovation Score": True, "Explanation": True},
    title=f"Innovation Score by Jurisdiction – {display_title}"
)
fig.update_layout(yaxis=dict(range=[0, 10]), xaxis_tickangle=-45, height=500)
st.plotly_chart(fig, use_container_width=True)

# --- Load Legislation Data ---
file_path = "laws_import.xlsx"
df = pd.read_excel(file_path)

df["Jurisdiction"] = df["Jurisdiction"].replace({
    "UK": "United Kingdom",
    "EU": "European Union",
    "United States": "United States of America"
})

if selected_industry == "All Industries":
    legislation = df[df["Jurisdiction"].isin(selected_jurisdictions)]
else:
    legislation = df[
        (df["Jurisdiction"].isin(selected_jurisdictions)) &
        (df["Relevant Industry"].str.contains(selected_industry, case=False, na=False))
    ]

legislation = legislation[[
    "Jurisdiction", "Law/Subprovision", "Significance",
    "Innovation Stage", "Enforceability", "Risk Score"
]]

# --- Show Legislation Table ---
st.subheader(f"📜 Relevant Laws & Barriers – {display_title}")
if legislation.empty:
    st.info("No matching legislation found.")
else:
    st.dataframe(legislation, use_container_width=True)

# --- Export to PDF ---
st.subheader("📄 Export Innovation Report to PDF")
if st.button("Download PDF Report"):
    html_parts = []
    html_parts.append(f"<h1>Innovation Score Summary – {display_title}</h1>")
    html_parts.append(filtered_scores.drop(columns=["Explanation"]).to_html(index=False))

    if not legislation.empty:
        html_parts.append(f"<h2>Relevant Laws & Barriers – {display_title}</h2>")
        html_parts.append(legislation.to_html(index=False))
    else:
        html_parts.append("<p><i>No legislation found for this combination.</i></p>")

    full_html = f"""
    <html>
    <head>
    <style>
    body {{ font-family: Arial, sans-serif; color: #ffffff; background-color: #0e1117; }}
    h1 {{ color: #00ccff; }}
    h2 {{ color: #66d9ef; margin-top: 30px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
    th, td {{ border: 1px solid #444; padding: 8px; font-size: 12px; color: #ffffff; }}
    th {{ background-color: #333; }}
    </style>
    </head>
    <body>{''.join(html_parts)}</body>
    </html>
    """

    wkhtmltopdf_path = r"C:\Program Files\wkhtmltopdf\bin\bin\wkhtmltopdf.exe"
    if not os.path.exists(wkhtmltopdf_path):
        st.warning("⚠️ PDF export only works locally. Please install wkhtmltopdf and run Streamlit locally.")
    else:
        config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            pdfkit.from_string(full_html, tmpfile.name, configuration=config)
            with open(tmpfile.name, "rb") as f:
                st.download_button(
                    label="📄 Download PDF Report",
                    data=f,
                    file_name=f"{display_title.lower().replace(' ', '_')}_innovation_report.pdf",
                    mime="application/pdf"
                )
