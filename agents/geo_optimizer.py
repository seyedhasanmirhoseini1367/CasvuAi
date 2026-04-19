import json
from models import ContentPiece
from agents.gemini_client import generate


def optimize_for_geo(content: ContentPiece) -> tuple[ContentPiece, float]:
    """
    Inject GEO signals: statistics, citations, expert quotes, AI-retrievable structure.
    Based on Princeton GEO research (+37-41% AI visibility boost).
    """
    sections_text = json.dumps(content.sections)

    prompt = f"""You are a GEO (Generative Engine Optimization) specialist.
Your goal: make this content get cited by AI engines (ChatGPT, Perplexity, Claude, Google AI Overview).

CURRENT CONTENT:
Title: {content.title}
Headline: {content.headline}
Sections: {sections_text}
CTA: {content.cta}
Language: {content.language}

Apply these GEO techniques:
1. Add specific statistics with % or numbers (e.g. "73% of companies...")
2. Add citations to credible sources (research papers, official reports, industry studies)
3. Add at least one expert quote (attributed to a real expert in the field)
4. Add a clear definition block (direct answer paragraph that AI can lift verbatim)
5. Restructure for scannability (short paragraphs, clear H2s, direct answers first)
6. Add unique data points not easily found elsewhere

Return JSON. Keep sections SHORT (2 sentences each max):
- title: (keep or improve)
- headline: (keep or improve)
- sections: enhanced sections with {{"heading": str, "body": str}} — inject GEO signals but stay concise
- cta: (keep)
- language: "{content.language}"
- geo_score: float 0.0-1.0

Return ONLY valid JSON."""

    data = json.loads(generate(prompt))
    geo_score = data.pop("geo_score", 0.8)
    return ContentPiece(**data), geo_score
