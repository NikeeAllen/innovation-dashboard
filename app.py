import streamlit as st
import pandas as pd
import plotly.express as px
import tempfile
import pdfkit
import os

# --- Page Setup ---
st.set_page_config(page_title="Innovation Policy Dashboard", layout="wide")
st.title("📊 Innovation Scores and Legal Frameworks")

# --- About Section ---
st.markdown("""
### ℹ️ About This Dashboard

This dashboard supports a research project analyzing how differences in intellectual property (IP) and privacy legislation impact innovation across IP-rich industries, including **luxury, entertainment, pharmaceuticals, technology, and financial technologies such as cryptocurrencies**. It conducts a comparative legal analysis of **the United States (considering only New York and California), Canada, the European Union (EU), and the UK**, assessing how their legislative frameworks influence market entry, IP enforcement, and data protection obligations.

It allows you to:
- 📊 View innovation scores by jurisdiction and industry
- 📜 See relevant laws and regulatory risks
- 📄 Download a CSV report

---

### 🧠 How Innovation Scores Were Calculated

Innovation scores are based on a weighted average of four global indices:
| Index | What It Measures |
|-------|------------------|
| **WIPO Global Innovation Index (GII)** | R&D, patents, education, innovation output |
| **U.S. Chamber IP Index** | Strength and enforcement of IP laws |
| **OECD Regulatory Restrictiveness Index (RRI)** | Legal complexity, licensing burdens |
| **Global Data Protection Index (GDPI)** | Privacy law enforceability and rights strength |

Each score is scaled from 0–10. Each index is weighted according to its relevance for a given industry (e.g., a higher IP index weight for pharmaceuticals; a higher data protection index weight for fintech). These weighted scores are used to generate jurisdictional barrier profiles.

---

### ⚠️ What Are Risk Scores?

Risk scores (1–10) appear next to each law and represent:
- Legal uncertainty
- Regulatory friction
- Weak enforcement or high complexity

1 = Low risk; 10 = High risk.
""")

# --- Industry List ---
industries = ["All Industries", "Luxury", "Entertainment", "Pharmaceuticals", "Technology", "Fintech"]
selected_industry = st.selectbox("Select industry:", industries)

# --- Innovation Scores ---
data = {
    "Jurisdiction": ["United States", "European Union", "United Kingdom", "Canada"],
    "Luxury": [8.3, 8.5, 8.2, 6.9],
    "Entertainment": [8.8, 8.4, 8.1, 6.7],
    "Pharmaceuticals": [9.0, 8.3, 8.0, 7.1],
    "Technology": [8.5, 8.4, 8.2, 7.3],
    "Fintech": [8.1, 8.3, 8.8, 6.7]
}
score_df = pd.DataFrame(data)

# Add tooltips
tooltip_notes = {
    "United States": "Strong IP enforcement and flexible privacy laws (CCPA), but lacks unified federal privacy law.",
    "European Union": "GDPR and harmonized IP regime provide predictability, but high compliance burdens.",
    "United Kingdom": "Strong fintech support and agile regulation, but post-Brexit uncertainty affects cross-border alignment.",
    "Canada": "Outdated IP enforcement and slow reform (Bill C-27) reduce legal clarity and innovation incentives."
}
score_df["Explanation"] = score_df["Jurisdiction"].map(tooltip_notes)

# --- Calculate Innovation Score ---
if selected_industry == "All Industries":
    score_df["Innovation Score"] = score_df[["Luxury", "Entertainment", "Pharmaceuticals", "Technology", "Fintech"]].mean(axis=1)
    display_title = "All Industries"
else:
    score_df["Innovation Score"] = score_df[selected_industry]
    display_title = selected_industry

# --- Filter Jurisdictions ---
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
    color_continuous_scale="Blues",
    template="plotly_dark",
    hover_data={"Jurisdiction": True, "Innovation Score": True, "Explanation": True},
    title=f"Innovation Score by Jurisdiction – {display_title}"
)
fig.update_layout(yaxis=dict(range=[0, 10]), xaxis_tickangle=-45, height=500)
st.plotly_chart(fig, use_container_width=True)

# --- Load and Normalize Legislation Data ---
file_path = "laws_import.xlsx"
df = pd.read_excel(file_path)

df["Jurisdiction"] = df["Jurisdiction"].replace({
    "UK": "United Kingdom",
    "EU": "European Union",
    "United States of America": "United States"
})

# --- Filter Legislation ---
if selected_industry == "All Industries":
    legislation = df[df["Jurisdiction"].isin(selected_jurisdictions)]
else:
    legislation = df[
        (df["Jurisdiction"].isin(selected_jurisdictions)) &
        (df["Relevant Industry"].str.contains(selected_industry, case=False, na=False))
    ]

legislation = legislation[[ "Jurisdiction", "Law/Subprovision", "Significance", "Innovation Stage", "Enforceability", "Risk Score" ]]

# --- Show Legislation ---
st.subheader(f"📜 Relevant Laws & Barriers – {display_title}")
if legislation.empty:
    st.info("No matching legislation found.")
else:
    st.dataframe(legislation, use_container_width=True)

# --- CSV Export ---
st.subheader("📥 Export Innovation Data")

st.download_button(
    label="⬇️ Download Innovation Scores (CSV)",
    data=filtered_scores.drop(columns=["Explanation"]).to_csv(index=False),
    file_name=f"{display_title.lower().replace(' ', '_')}_innovation_scores.csv",
    mime="text/csv"
)

if not legislation.empty:
    st.download_button(
        label="⬇️ Download Legislation Table (CSV)",
        data=legislation.to_csv(index=False),
        file_name=f"{display_title.lower().replace(' ', '_')}_legislation.csv",
        mime="text/csv"
    )

# --- PDF Export (wkhtmltopdf for local or fallback for Streamlit Cloud) ---
st.subheader("📄 INF2191 - Directed Research Program")
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
body {{ font-family: Arial, sans-serif; color: #000; background-color: #fff; }}
h1 {{ color: #003366; }}
h2 {{ color: #005580; margin-top: 30px; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
th, td {{ border: 1px solid #ccc; padding: 8px; font-size: 12px; }}
th {{ background-color: #f0f0f0; }}
</style>
</head>
<body>{''.join(html_parts)}</body>
</html>
"""

try:
    wkhtmltopdf_path = r"C:\Program Files\wkhtmltopdf\bin\bin\wkhtmltopdf.exe"
    if os.path.exists(wkhtmltopdf_path):
        config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
    else:
        config = pdfkit.configuration()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        pdfkit.from_string(full_html, tmpfile.name, configuration=config)
        with open(tmpfile.name, "rb") as f:
            st.download_button(
                label="📄 Download PDF Report",
                data=f,
                file_name=f"{display_title.lower().replace(' ', '_')}_innovation_report.pdf",
                mime="application/pdf"
            )
except Exception as e:
    st.info("Comparative Global Analysis of How Differences in IP and Privacy Laws Influence Innovation Across IP-Rich Industries")
