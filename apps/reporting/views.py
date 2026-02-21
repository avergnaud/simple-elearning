"""Admin reporting views: quiz summaries, per-student drill-downs, and certificate download."""
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, TemplateView

from apps.accounts.mixins import AdminRequiredMixin
from apps.enrolments.models import Attempt, Enrolment
from apps.enrolments.utils import render_certificate_pdf
from apps.quizzes.models import Quiz
from django.views import View


class ReportHomeView(AdminRequiredMixin, ListView):
    """Reporting home — quiz summary report listing all quizzes with aggregate stats."""

    template_name = "reporting/report-home.html"
    context_object_name = "quiz_stats"

    def get_queryset(self):
        """Return all quizzes annotated with enrolment and attempt statistics."""
        return (
            Quiz.objects.annotate(
                enrolled_count=Count("enrolments", distinct=True),
                attempt_count=Count("enrolments__attempts"),
                pass_count=Count(
                    "enrolments__attempts",
                    filter=Q(enrolments__attempts__passed=True),
                ),
                avg_score=Avg("enrolments__attempts__score_percent"),
            )
            .order_by("title")
        )

    def get_context_data(self, **kwargs):
        """Compute pass rate percentage for each quiz."""
        context = super().get_context_data(**kwargs)
        for quiz in context["quiz_stats"]:
            if quiz.attempt_count:
                quiz.pass_rate = round(quiz.pass_count / quiz.attempt_count * 100, 1)
            else:
                quiz.pass_rate = None
        return context


class QuizReportView(AdminRequiredMixin, TemplateView):
    """Per-quiz summary report with key statistics."""

    template_name = "reporting/quiz-report.html"

    def get_context_data(self, **kwargs):
        """Load quiz aggregate stats."""
        context = super().get_context_data(**kwargs)
        quiz = get_object_or_404(Quiz, pk=self.kwargs["quiz_id"])
        attempts = Attempt.objects.filter(
            enrolment__quiz=quiz, submitted_at__isnull=False
        )
        total_attempts = attempts.count()
        pass_count = attempts.filter(passed=True).count()
        avg_score = attempts.aggregate(avg=Avg("score_percent"))["avg"]

        context["quiz"] = quiz
        context["enrolled_count"] = quiz.enrolments.count()
        context["total_attempts"] = total_attempts
        context["pass_rate"] = round(pass_count / total_attempts * 100, 1) if total_attempts else None
        context["avg_score"] = round(float(avg_score), 1) if avg_score is not None else None
        return context


class QuizStudentsReportView(AdminRequiredMixin, TemplateView):
    """Per-student drill-down for a specific quiz.

    Shows each enrolled student with attempt counts, best score, pass/fail status,
    and first/most-recent attempt dates.
    """

    template_name = "reporting/quiz-students.html"

    def get_context_data(self, **kwargs):
        """Build a per-student statistics table for the selected quiz."""
        context = super().get_context_data(**kwargs)
        quiz = get_object_or_404(Quiz, pk=self.kwargs["quiz_id"])

        enrolments = (
            Enrolment.objects
            .filter(quiz=quiz)
            .select_related("student")
            .prefetch_related("attempts")
        )

        student_rows = []
        for enrolment in enrolments:
            submitted = enrolment.attempts.filter(submitted_at__isnull=False)
            attempt_count = submitted.count()
            best_score = None
            first_attempt = None
            last_attempt = None

            if attempt_count:
                scores = [a.score_percent for a in submitted if a.score_percent is not None]
                best_score = round(float(max(scores)), 1) if scores else None
                ordered = submitted.order_by("submitted_at")
                first_attempt = ordered.first().submitted_at
                last_attempt = ordered.last().submitted_at

            student_rows.append({
                "student": enrolment.student,
                "enrolment": enrolment,
                "attempt_count": attempt_count,
                "best_score": best_score,
                "has_passed": enrolment.has_passed,
                "first_attempt": first_attempt,
                "last_attempt": last_attempt,
            })

        context["quiz"] = quiz
        context["student_rows"] = student_rows
        return context


class StudentOverviewReportView(AdminRequiredMixin, TemplateView):
    """Cross-quiz student overview: shows every student's enrolments and statuses."""

    template_name = "reporting/students-overview.html"

    def get_context_data(self, **kwargs):
        """Build a per-student cross-quiz summary."""
        context = super().get_context_data(**kwargs)
        from apps.accounts.models import User
        students = (
            User.objects
            .filter(role="student")
            .prefetch_related("enrolments__quiz", "enrolments__attempts")
            .order_by("display_name")
        )

        student_rows = []
        for student in students:
            enrolments = student.enrolments.select_related("quiz").all()
            total_attempts = sum(e.attempts.count() for e in enrolments)
            student_rows.append({
                "student": student,
                "enrolments": enrolments,
                "total_attempts": total_attempts,
            })

        context["student_rows"] = student_rows
        return context


class AdminCertificateDownloadView(AdminRequiredMixin, View):
    """Allow an admin to download a certificate PDF for any passed enrolment."""

    def get(self, request, enrolment_id, *args, **kwargs):
        """Return the certificate PDF or 403 if not yet passed."""
        enrolment = get_object_or_404(Enrolment, pk=enrolment_id)
        if not enrolment.has_passed:
            raise PermissionDenied
        return render_certificate_pdf(enrolment)
