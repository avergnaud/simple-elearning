"""Enrolment, Attempt, results, and certificate views (student-facing)."""
import random
import uuid

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView

from apps.enrolments.models import Attempt, AttemptAnswer, AttemptQuestion, Enrolment
from apps.enrolments.utils import render_certificate_pdf
from apps.quizzes.models import Quiz


class EnrolView(LoginRequiredMixin, View):
    """Enrol the current student in a quiz (POST only).

    Creates an Enrolment record if one does not already exist for this
    student/quiz pair. Immediately locks the quiz if this is the first enrolment.
    """

    def post(self, request, quiz_id, *args, **kwargs):
        """Create enrolment and redirect to quiz detail."""
        if request.user.is_admin:
            raise PermissionDenied

        quiz = get_object_or_404(Quiz, pk=quiz_id)
        _, created = Enrolment.objects.get_or_create(student=request.user, quiz=quiz)

        if created and not quiz.is_locked:
            quiz.is_locked = True
            quiz.save(update_fields=["is_locked"])

        return redirect("quizzes:quiz-detail", quiz_id=quiz_id)


class AttemptView(LoginRequiredMixin, View):
    """Display and submit a quiz attempt.

    GET: Find or create an unsubmitted attempt for this enrolment and render
         the quiz form with all questions.
    POST: Score the submitted attempt and redirect to the results page.
    """

    def dispatch(self, request, *args, **kwargs):
        """Reject admin users."""
        if request.user.is_authenticated and request.user.is_admin:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def _get_enrolment(self, request, quiz_id):
        """Return the enrolment or raise 404."""
        return get_object_or_404(Enrolment, student=request.user, quiz_id=quiz_id)

    def _get_or_create_attempt(self, enrolment):
        """Return an existing unsubmitted attempt or create a new one.

        A new attempt randomly selects N questions from the quiz pool and
        pre-populates all four answer options in shuffled order.
        """
        existing = enrolment.attempts.filter(submitted_at__isnull=True).first()
        if existing:
            return existing

        quiz = enrolment.quiz
        question_pool = list(quiz.questions.prefetch_related("answers").all())
        if len(question_pool) < quiz.questions_shown:
            # Fallback: show all questions if pool is smaller than requested
            selected_questions = question_pool
        else:
            selected_questions = random.sample(question_pool, quiz.questions_shown)

        attempt = Attempt.objects.create(enrolment=enrolment)

        for display_order, question in enumerate(selected_questions, start=1):
            aq = AttemptQuestion.objects.create(
                attempt=attempt,
                question=question,
                display_order=display_order,
            )
            answers = list(question.answers.all())
            random.shuffle(answers)
            for answer_order, answer in enumerate(answers, start=1):
                AttemptAnswer.objects.create(
                    attempt_question=aq,
                    answer=answer,
                    is_selected=False,
                    display_order=answer_order,
                )

        return attempt

    def get(self, request, quiz_id, *args, **kwargs):
        """Show the quiz attempt form."""
        from django.shortcuts import render
        enrolment = self._get_enrolment(request, quiz_id)
        attempt = self._get_or_create_attempt(enrolment)

        attempt_questions = (
            attempt.attempt_questions
            .select_related("question")
            .prefetch_related("attempt_answers__answer")
            .order_by("display_order")
        )

        return render(request, "enrolments/attempt-form.html", {
            "quiz": enrolment.quiz,
            "attempt": attempt,
            "attempt_questions": attempt_questions,
        })

    def post(self, request, quiz_id, *args, **kwargs):
        """Score the submitted attempt and redirect to the results page."""
        enrolment = self._get_enrolment(request, quiz_id)
        attempt_id = request.POST.get("attempt_id")
        attempt = get_object_or_404(
            Attempt, pk=attempt_id, enrolment=enrolment, submitted_at__isnull=True
        )

        # Build a map of attempt_question_id → list of selected answer_ids from POST
        submitted: dict[str, list[str]] = {}
        for key, values in request.POST.lists():
            if key.startswith("aq_"):
                aq_id = key[3:]  # strip "aq_" prefix
                submitted[aq_id] = values

        # Score each question
        correct_count = 0
        for aq in attempt.attempt_questions.prefetch_related(
            "attempt_answers__answer", "question__answers"
        ):
            selected_ids = set(submitted.get(str(aq.pk), []))
            correct_ids = set(
                str(a.pk) for a in aq.question.answers.filter(is_correct=True)
            )
            for aa in aq.attempt_answers.all():
                aa.is_selected = str(aa.answer_id) in selected_ids
                aa.save(update_fields=["is_selected"])
            if selected_ids == correct_ids:
                correct_count += 1

        total = attempt.attempt_questions.count()
        score = round((correct_count / total) * 100, 1) if total else 0.0

        attempt.score_percent = score
        attempt.passed = score >= float(enrolment.quiz.passing_score)
        attempt.submitted_at = timezone.now()
        attempt.save()

        # Update enrolment if this is the first pass
        if attempt.passed and not enrolment.has_passed:
            enrolment.has_passed = True
            enrolment.passing_attempt = attempt
            enrolment.certificate_code = uuid.uuid4()
            enrolment.save(update_fields=["has_passed", "passing_attempt", "certificate_code"])

        return redirect("quizzes:results", quiz_id=quiz_id, attempt_id=attempt.pk)


class AttemptResultsView(LoginRequiredMixin, DetailView):
    """Show the results of a completed attempt: pass/fail, score, and question review."""

    template_name = "enrolments/attempt-results.html"
    context_object_name = "attempt"

    def dispatch(self, request, *args, **kwargs):
        """Reject admin users."""
        if request.user.is_authenticated and request.user.is_admin:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        """Return the attempt, enforcing ownership."""
        return get_object_or_404(
            Attempt,
            pk=self.kwargs["attempt_id"],
            enrolment__student=self.request.user,
            enrolment__quiz_id=self.kwargs["quiz_id"],
            submitted_at__isnull=False,
        )

    def get_context_data(self, **kwargs):
        """Add quiz, enrolment, and annotated question/answer data to context."""
        context = super().get_context_data(**kwargs)
        attempt = self.object
        enrolment = attempt.enrolment

        attempt_questions = list(
            attempt.attempt_questions
            .select_related("question")
            .prefetch_related("attempt_answers__answer", "question__answers")
            .order_by("display_order")
        )

        correct_count = 0
        for aq in attempt_questions:
            selected_ids = {str(aa.answer_id) for aa in aq.attempt_answers.all() if aa.is_selected}
            correct_ids = {str(a.pk) for a in aq.question.answers.all() if a.is_correct}
            if selected_ids == correct_ids:
                correct_count += 1

        context["quiz"] = enrolment.quiz
        context["enrolment"] = enrolment
        context["attempt_questions"] = attempt_questions
        context["correct_count"] = correct_count
        context["total_questions"] = attempt_questions.count()
        return context


class CertificateDownloadView(LoginRequiredMixin, View):
    """Stream a PDF certificate for the student's own passed enrolment."""

    def dispatch(self, request, *args, **kwargs):
        """Reject admin users."""
        if request.user.is_authenticated and request.user.is_admin:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, quiz_id, *args, **kwargs):
        """Return the certificate PDF or 403 if not yet passed."""
        enrolment = get_object_or_404(Enrolment, student=request.user, quiz_id=quiz_id)
        if not enrolment.has_passed:
            raise PermissionDenied
        return render_certificate_pdf(enrolment)
