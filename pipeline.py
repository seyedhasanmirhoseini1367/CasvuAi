import json
from models import EvaluationResult, JudgeResult, PipelineOutput
from agents.ingestion import ingest_client_data
from agents.brand_analyzer import analyze_brand
from agents.competitor_analyzer import analyze_competitors
from agents.content_writer import build_content_brief, write_content
from agents.content_classifier import classify_content
from agents.geo_optimizer import optimize_for_geo
from agents.localizer import localize_content
from agents.evaluator import evaluate_loop, evaluate_competitor_edge
from config import MAX_RETRIES


def to_str(v) -> str:
    if isinstance(v, list):
        return " ".join(str(i) for i in v)
    return str(v) if v else ""


def content_to_text(content) -> str:
    parts = [to_str(content.title), to_str(content.headline)]
    for section in content.sections:
        parts.append(to_str(section.get("heading", "")))
        parts.append(to_str(section.get("body", "")))
    parts.append(to_str(content.cta))
    return "\n\n".join(parts)


def run_pipeline(
    client_id: str,
    client_documents: list[str],
    competitor_documents: list[str],
    goal: str,
    target_languages: list[str] = ["English", "Finnish"],
) -> PipelineOutput:

    print(f"\n{'='*60}")
    print(f"CASEVUAI CONTENT PIPELINE - Client: {client_id}")
    print(f"Goal: {goal}")
    print(f"{'='*60}\n")

    # ── PHASE 1: DATA INGESTION ──────────────────────────────────
    print("[Phase 1] Ingesting client data...")
    ingest_client_data(client_id, client_documents)

    # ── PHASE 2: PRE-FILTERS ─────────────────────────────────────
    print("[Phase 2] Running pre-filters...")

    # Query intent first — informs both brand focus and competitor analysis
    content_type = classify_content(goal)
    print(f"  Query intent: {content_type['primary_intent'].upper()} — {' -> '.join(content_type['structure'])}")

    # Brand analysis (RAG from client VectorDB)
    brand = analyze_brand(client_id)
    print(f"  Brand tone: {brand.tone}")

    # Competitor analysis — uses query intent + brand context for targeted inference
    brand_context = f"{brand.tone} {brand.audience} — {', '.join(brand.differentiators[:2])}"
    gap_map = analyze_competitors(goal, competitor_documents, brand_context, content_type['primary_intent'])
    print(f"  Competitors identified: {', '.join(gap_map.competitors[:3])}")
    print(f"  Gaps found: {len(gap_map.gaps)}")

    # Content brief — synthesizes intent + brand + gaps into one writing instruction
    brief = build_content_brief(goal, brand, gap_map)
    print(f"  Content angle: {brief.angle}")

    # ── PHASE 3-5: WRITE → GEO OPTIMIZE → EVALUATE (loop) ───────
    print("[Phase 3-5] Write -> GEO optimize -> evaluate (loop)...")
    feedback = None
    content_en = None
    loop_result = None

    for attempt in range(1, MAX_RETRIES + 1):
        print(f"  Attempt {attempt}/{MAX_RETRIES}")

        content_en = write_content(client_id, brief, brand, content_type, language="English", feedback=feedback)
        content_en, _ = optimize_for_geo(content_en)
        content_text = content_to_text(content_en)

        loop_result = evaluate_loop(
            content_text=content_text,
            audience=brand.audience,
            goal=goal,
        )

        print(f"  Customer: {loop_result['customer']['score']} | GEO: {loop_result['geo']['score']} | Naturalness: {loop_result['naturalness']['score']} | Overall: {loop_result['overall_score']} | Passed: {loop_result['passed']}")

        if loop_result["passed"]:
            break

        feedback = (
            f"Customer feedback: {loop_result['customer']['feedback']}\n"
            f"GEO missing: {', '.join(loop_result['geo']['missing'])}\n"
            f"Naturalness feedback: {loop_result['naturalness']['feedback']}"
        )

    # ── POST-LOOP: COMPETITOR EDGE (once, on final content) ───────
    print("  [Judge 3] Competitor edge (post-loop)...")
    competitor_result = evaluate_competitor_edge(
        content_text=content_to_text(content_en),
        competitor_data=competitor_documents,
        gap_map_gaps=gap_map.gaps,
    )

    overall_score = round((
        loop_result["customer"]["score"] +
        loop_result["geo"]["score"] +
        competitor_result["score"] +
        loop_result["naturalness"]["score"]
    ) / 4)

    evaluation = EvaluationResult(
        customer=JudgeResult(
            score=loop_result["customer"]["score"],
            feedback=loop_result["customer"]["feedback"],
            details={
                "pain_points_addressed": loop_result["customer"]["pain_points_addressed"],
                "clarity": loop_result["customer"]["clarity"],
                "value_proposition": loop_result["customer"]["value_proposition"],
            }
        ),
        geo=JudgeResult(
            score=loop_result["geo"]["score"],
            feedback=loop_result["geo"]["feedback"],
            details={
                "checks": loop_result["geo"]["checks"],
                "missing": loop_result["geo"]["missing"],
            }
        ),
        competitor=JudgeResult(
            score=competitor_result["score"],
            feedback=competitor_result["feedback"],
            details={
                "beats_on_specificity": competitor_result["beats_on_specificity"],
                "covers_gaps": competitor_result["covers_gaps"],
                "unique_angle": competitor_result["unique_angle"],
            }
        ),
        naturalness=JudgeResult(
            score=loop_result["naturalness"]["score"],
            feedback=loop_result["naturalness"]["feedback"],
            details={
                "sounds_human": loop_result["naturalness"]["sounds_human"],
                "ai_cliches_found": loop_result["naturalness"]["ai_cliches_found"],
                "ai_patterns": loop_result["naturalness"]["ai_patterns"],
            }
        ),
        overall_score=overall_score,
        passed=overall_score >= 70,
    )

    print(f"  Final — Customer: {evaluation.customer.score} | GEO: {evaluation.geo.score} | Competitor: {evaluation.competitor.score} | Naturalness: {evaluation.naturalness.score} | Overall: {evaluation.overall_score}")

    # ── PHASE 6: LOCALIZE ─────────────────────────────────────────
    print("[Phase 6] Localizing content...")
    localized = {"English": content_en}
    for lang in target_languages:
        if lang == "English":
            continue
        print(f"  Localizing to {lang}...")
        localized[lang] = localize_content(client_id, content_en, lang, brand)

    content_fi = localized.get("Finnish", content_en)

    print(f"\n{'='*60}")
    print(f"PIPELINE COMPLETE - Overall: {evaluation.overall_score}/100 | Passed: {evaluation.passed}")
    print(f"{'='*60}\n")

    return PipelineOutput(
        content_en=content_en,
        content_fi=content_fi,
        evaluation=evaluation,
        content_type=content_type,
    )


def save_output(output: PipelineOutput, client_id: str):
    import os
    os.makedirs("output", exist_ok=True)

    for content in [output.content_en, output.content_fi]:
        lang = content.language.lower()[:2]
        path = f"output/{client_id}_{lang}.md"
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# {content.title}\n\n## {content.headline}\n\n")
            for section in content.sections:
                f.write(f"### {section.get('heading', '')}\n\n{section.get('body', '')}\n\n")
            f.write(f"**{content.cta}**\n")
        print(f"Saved: {path}")

    with open(f"output/{client_id}_scores.json", "w") as f:
        json.dump(output.evaluation.model_dump(), f, indent=2)
