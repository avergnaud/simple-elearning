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
    context = {
        "student_name": enrolment.student.display_name,
        "quiz_title": enrolment.quiz.title,
        "score_percent": enrolment.passing_attempt.score_percent,
        "passed_date": enrolment.passing_attempt.submitted_at.date(),
        "certificate_code": str(enrolment.certificate_code).upper(),
        "platform_name": settings.PLATFORM_NAME,
        "generated_at": timezone.now(),
    }

    html_string = render_to_string("certificates/certificate.html", context)
    pdf_bytes = weasyprint.HTML(string=html_string).write_pdf()

    quiz_slug = slugify(enrolment.quiz.title)
    student_slug = slugify(enrolment.student.display_name)
    filename = f"certificate_{quiz_slug}_{student_slug}.pdf"

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
