import json
from models import BrandProfile, ContentBrief, CompetitorGapMap, ContentPiece
from agents.ingestion import query_collection
from agents.gemini_client import generate


def build_content_brief(goal: str, brand: BrandProfile, gap_map: CompetitorGapMap) -> ContentBrief:
    prompt = f"""You are a content strategist.

GOAL: {goal}
BRAND AUDIENCE: {brand.audience}
BRAND VALUES: {', '.join(brand.values)}
UNIQUE ANGLES AVAILABLE: {', '.join(gap_map.unique_angles)}
GAPS TO FILL: {', '.join(gap_map.gaps)}

Build a content brief as JSON:
- goal: restate the goal clearly
- angle: the single best angle to take (from unique angles)
- target_audience: specific description (one sentence)
- key_messages: list of 3 short messages
- gap_opportunities: list of 2-3 gaps this content will fill

Return ONLY valid JSON."""

    data = json.loads(generate(prompt))
    if "content_brief" in data:
        data = data["content_brief"]
    return ContentBrief(**data)


def write_content(
    client_id: str,
    brief: ContentBrief,
    brand: BrandProfile,
    content_type: dict,
    language: str = "English",
    feedback: str = None,
) -> ContentPiece:
    """Generate website page content grounded in client's real data via RAG."""
    rag_chunks = query_collection(client_id, brief.goal, n_results=4)
    rag_context = "\n\n".join(rag_chunks)
    feedback_block = f"\nPREVIOUS FEEDBACK:\n{feedback}" if feedback else ""

    structure = " → ".join(content_type["structure"])

    prompt = f"""You are a website copywriter. Write a concise website page.

CONTENT TYPE: Answers the question "{content_type['primary_intent'].upper()}"
REQUIRED STRUCTURE: {structure}
OPENING RULE: {content_type['opening_instruction']}
GEO PRIORITY: {content_type['geo_priority']}

BRAND VOICE: {brand.tone}
FORBIDDEN WORDS: {', '.join(brand.forbidden_words)}
TARGET AUDIENCE: {brief.target_audience}
CONTENT ANGLE: {brief.angle}
KEY MESSAGES: {', '.join(brief.key_messages)}
LANGUAGE: {language}

COMPANY CONTENT (match this voice):
{rag_context}
{feedback_block}

Return JSON — keep sections SHORT (2 sentences each):
- title: SEO title (60 chars max)
- headline: punchy H1 (one sentence)
- sections: exactly 3 items with "heading" and "body" — follow the required structure above
- cta: 5 words max
- language: "{language}"

Return ONLY valid JSON."""

    data = json.loads(generate(prompt))
    return ContentPiece(**data)
