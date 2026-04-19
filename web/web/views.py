import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from django.shortcuts import render
from pipeline import run_pipeline


def index(request):
    if request.method == 'POST':
        client_id = request.POST.get('client_id', 'client').strip().replace(' ', '_')
        goal = request.POST.get('goal', '').strip()
        client_content = request.POST.get('client_content', '').strip()
        competitor_content = request.POST.get('competitor_content', '').strip()

        client_docs = [client_content] if client_content else []
        competitor_docs = [competitor_content] if competitor_content else []

        try:
            output = run_pipeline(
                client_id=client_id,
                client_documents=client_docs,
                competitor_documents=competitor_docs,
                goal=goal,
                target_languages=["English", "Finnish"],
            )

            def content_to_html(content):
                sections_html = ""
                for s in content.sections:
                    sections_html += f"<h3>{s.get('heading','')}</h3><p>{s.get('body','')}</p>"
                return {
                    "title": content.title,
                    "headline": content.headline,
                    "sections_html": sections_html,
                    "cta": content.cta,
                    "language": content.language,
                }

            ev = output.evaluation
            geo_checks = ev.geo.details.get("checks", {})
            geo_missing = ev.geo.details.get("missing", [])

            return render(request, 'result.html', {
                "content_en": content_to_html(output.content_en),
                "content_fi": content_to_html(output.content_fi),
                "overall_score": ev.overall_score,
                "passed": ev.passed,
                # Judge scores
                "customer_score": ev.customer.score,
                "geo_score": ev.geo.score,
                "competitor_score": ev.competitor.score,
                "naturalness_score": ev.naturalness.score,
                # Judge feedback
                "customer_feedback": ev.customer.feedback,
                "geo_feedback": ev.geo.feedback,
                "competitor_feedback": ev.competitor.feedback,
                "naturalness_feedback": ev.naturalness.feedback,
                # Judge details
                "customer_details": ev.customer.details,
                "geo_checks": geo_checks,
                "geo_missing": geo_missing,
                "competitor_details": ev.competitor.details,
                "naturalness_details": ev.naturalness.details,
                "ai_cliches": ev.naturalness.details.get("ai_cliches_found", []),
                "content_type": output.content_type,
            })

        except Exception as e:
            import traceback
            return render(request, 'index.html', {"error": traceback.format_exc()})

    return render(request, 'index.html')
