"""
Demo: run the full pipeline with sample client data.
Replace client_documents and competitor_documents with real data from your system.
"""
from pipeline import run_pipeline, save_output

# Simulated client data (replace with real data from your system)
client_documents = [
    """
    Acme HR Solutions helps small businesses hire smarter.
    We believe every company deserves great talent, regardless of size or budget.
    Our approach is personal, practical, and always people-first.
    We don't use jargon — we speak plainly because our clients are busy founders, not HR experts.
    """,
    """
    Our services include recruitment process outsourcing, onboarding automation,
    and HR compliance support. We work with Finnish SMEs across retail, tech, and healthcare.
    Our clients typically have 10-100 employees and no dedicated HR manager.
    """,
]

# Simulated competitor data (replace with real competitor content from your system)
competitor_documents = [
    "Competitor A offers end-to-end HR software with AI-powered matching and enterprise integrations.",
    "Competitor B provides recruitment services focused on large corporations with dedicated account managers.",
]

output = run_pipeline(
    client_id="acme_hr",
    client_documents=client_documents,
    competitor_documents=competitor_documents,
    goal="Launch a new AI-assisted onboarding service for Finnish SMEs",
    target_languages=["English", "Finnish"],
)

save_output(output, "acme_hr")
