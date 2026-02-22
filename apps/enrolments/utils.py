"""Shared utility functions for the enrolments app."""
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.text import slugify

import weasyprint


def render_certificate_pdf(enrolment) -> HttpResponse:
    """Render a certificate PDF for a passed enrolment and return it as an HTTP response.

    Args:
        enrolment: An ``Enrolment`` instance where ``has_passed`` is True and
                   ``passing_attempt`` is set.

    Returns:
        An ``HttpResponse`` with Content-Type ``application/pdf`` and an
        appropriate ``Content-Disposition`` attachment header.
    """
    attempt = enrolment.passing_attempt
    attempt_questions = (
        attempt.attempt_questions
        .select_related("question")
        .prefetch_related("attempt_answers__answer")
        .order_by("display_order")
    )

    questions_detail = []
    for aq in attempt_questions:
        all_answers = list(aq.attempt_answers.all())
        correct_ids = {str(aa.answer_id) for aa in all_answers if aa.answer.is_correct}
        selected = [aa for aa in all_answers if aa.is_selected]
        selected_ids = {str(aa.answer_id) for aa in selected}
        questions_detail.append({
            "number": aq.display_order,
            "text": aq.question.text,
            "selected_answers": [aa.answer.text for aa in selected],
            "is_correct": selected_ids == correct_ids,
        })

    context = {
        "student_name": enrolment.student.display_name,
        "quiz_title": enrolment.quiz.title,
        "score_percent": enrolment.passing_attempt.score_percent,
        "passed_date": enrolment.passing_attempt.submitted_at.date(),
        "certificate_code": str(enrolment.certificate_code).upper(),
        "platform_name": settings.PLATFORM_NAME,
        "generated_at": timezone.now(),
        "questions_detail": questions_detail,
    }

    html_string = render_to_string("certificates/certificate.html", context)
    pdf_bytes = weasyprint.HTML(string=html_string).write_pdf()

    quiz_slug = slugify(enrolment.quiz.title)
    student_slug = slugify(enrolment.student.display_name)
    filename = f"certificate_{quiz_slug}_{student_slug}.pdf"

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
