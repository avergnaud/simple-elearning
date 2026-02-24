"""Student-facing quiz views and admin quiz-management views."""
import uuid
import os

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, FormView, ListView, TemplateView, View

from apps.accounts.mixins import AdminRequiredMixin
from apps.quizzes.forms import ImageUploadForm, QuestionAddForm, QuizCreateForm, QuizEditTitleForm
from apps.quizzes.models import Answer, Question, Quiz

# ---------------------------------------------------------------------------
# Student-facing views
# ---------------------------------------------------------------------------


class QuizListView(ListView):
    """Display the quiz catalogue — the student's home page after login.

    Context variable ``quiz_list`` is a list of dicts with keys
    ``quiz`` and ``enrolment`` (None if the student is not enrolled).
    """

    template_name = "quizzes/quiz-list.html"

    def dispatch(self, request, *args, **kwargs):
        """Redirect unauthenticated users to login."""
        if not request.user.is_authenticated:
            from django.conf import settings
            return redirect(settings.LOGIN_URL)
        if request.user.is_admin:
            return redirect("admin-panel:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """Return all quizzes ordered by title."""
        return Quiz.objects.all()

    def get_context_data(self, **kwargs):
        """Build quiz_list pairing each quiz with the student's enrolment (or None)."""
        context = super().get_context_data(**kwargs)
        from apps.enrolments.models import Enrolment
        enrolments = Enrolment.objects.filter(student=self.request.user).select_related("quiz")
        enrolment_map = {e.quiz_id: e for e in enrolments}
        context["quiz_list"] = [
            {"quiz": quiz, "enrolment": enrolment_map.get(quiz.pk)}
            for quiz in self.get_queryset()
        ]
        return context


class QuizDetailView(DetailView):
    """Show quiz details, enrol button, and start-attempt button."""

    model = Quiz
    template_name = "quizzes/quiz-detail.html"
    context_object_name = "quiz"
    pk_url_kwarg = "quiz_id"

    def dispatch(self, request, *args, **kwargs):
        """Restrict to authenticated students."""
        if not request.user.is_authenticated:
            from django.conf import settings
            return redirect(settings.LOGIN_URL)
        if request.user.is_admin:
            return redirect("admin-panel:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add the student's enrolment (if any) to the context."""
        context = super().get_context_data(**kwargs)
        from apps.enrolments.models import Enrolment
        try:
            context["enrolment"] = Enrolment.objects.get(
                student=self.request.user, quiz=self.object
            )
        except Enrolment.DoesNotExist:
            context["enrolment"] = None
        return context


# ---------------------------------------------------------------------------
# Admin quiz-management views
# ---------------------------------------------------------------------------


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    """Admin home page / dashboard."""

    template_name = "admin_panel/dashboard.html"


class AdminQuizListView(AdminRequiredMixin, ListView):
    """List all quizzes for admin management."""

    model = Quiz
    template_name = "admin_panel/quiz-list.html"
    context_object_name = "quizzes"

    def get_queryset(self):
        """Annotate quizzes with question counts."""
        return Quiz.objects.all()


class AdminQuizCreateView(AdminRequiredMixin, FormView):
    """Form view for creating a new quiz."""

    template_name = "admin_panel/quiz-create.html"
    form_class = QuizCreateForm

    def form_valid(self, form):
        """Save the quiz and redirect to its detail page."""
        quiz = form.save(commit=False)
        quiz.created_by = self.request.user
        quiz.passing_score = 70.00
        quiz.save()
        messages.success(self.request, f"Quiz '{quiz.title}' created successfully.")
        return redirect("admin-panel:quiz-detail", quiz_id=quiz.pk)


class AdminQuizDetailView(AdminRequiredMixin, DetailView):
    """Show a quiz's questions and allow adding more (if not locked)."""

    model = Quiz
    template_name = "admin_panel/quiz-detail.html"
    context_object_name = "quiz"
    pk_url_kwarg = "quiz_id"

    def get_context_data(self, **kwargs):
        """Add questions and lock status to context."""
        context = super().get_context_data(**kwargs)
        context["questions"] = self.object.questions.prefetch_related("answers").order_by("order")
        return context


class AdminQuizEditTitleView(AdminRequiredMixin, FormView):
    """Handle POST requests to update a quiz's title."""

    form_class = QuizEditTitleForm

    def setup(self, request, *args, **kwargs):
        """Resolve the quiz from the URL parameter."""
        super().setup(request, *args, **kwargs)
        self.quiz = get_object_or_404(Quiz, pk=kwargs["quiz_id"])

    def get_form_kwargs(self):
        """Bind the form to the existing quiz instance."""
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.quiz
        return kwargs

    def form_valid(self, form):
        """Save the updated title and redirect back to the detail page."""
        form.save()
        messages.success(self.request, "Quiz title updated.")
        return redirect("admin-panel:quiz-detail", quiz_id=self.quiz.pk)

    def form_invalid(self, form):
        """Redirect back with an error message if validation fails."""
        messages.error(self.request, "Invalid title — please try again.")
        return redirect("admin-panel:quiz-detail", quiz_id=self.quiz.pk)


class AdminQuestionAddView(AdminRequiredMixin, FormView):
    """Form view for adding a question (with four answers) to a quiz."""

    template_name = "admin_panel/question-add.html"
    form_class = QuestionAddForm

    def setup(self, request, *args, **kwargs):
        """Resolve the quiz from the URL parameter."""
        super().setup(request, *args, **kwargs)
        self.quiz = get_object_or_404(Quiz, pk=kwargs["quiz_id"])

    def dispatch(self, request, *args, **kwargs):
        """Reject if quiz is locked."""
        response = super().dispatch(request, *args, **kwargs)
        if self.quiz.is_locked:
            messages.error(request, "This quiz is locked and cannot accept new questions.")
            return redirect("admin-panel:quiz-detail", quiz_id=self.quiz.pk)
        return response

    def get_context_data(self, **kwargs):
        """Inject the quiz into template context."""
        context = super().get_context_data(**kwargs)
        context["quiz"] = self.quiz
        return context

    def form_valid(self, form):
        """Persist the question and its four answers, then redirect."""
        next_order = self.quiz.questions.count() + 1
        question = Question.objects.create(
            quiz=self.quiz,
            text=form.cleaned_data["text"],
            question_type=form.cleaned_data["question_type"],
            order=next_order,
        )

        answer_data = [
            (form.cleaned_data["answer_a"], form.cleaned_data["correct_a"]),
            (form.cleaned_data["answer_b"], form.cleaned_data["correct_b"]),
            (form.cleaned_data["answer_c"], form.cleaned_data["correct_c"]),
            (form.cleaned_data["answer_d"], form.cleaned_data["correct_d"]),
        ]
        for i, (text, is_correct) in enumerate(answer_data, start=1):
            Answer.objects.create(
                question=question,
                text=text,
                is_correct=is_correct,
                order=i,
            )

        messages.success(self.request, "Question added successfully.")
        return redirect("admin-panel:quiz-detail", quiz_id=self.quiz.pk)


class AdminQuestionEditView(AdminRequiredMixin, FormView):
    """Form view for editing an existing question and its four answers.

    Only available while the quiz is not locked (no student has yet enrolled).
    """

    template_name = "admin_panel/question-edit.html"
    form_class = QuestionAddForm

    def setup(self, request, *args, **kwargs):
        """Resolve the quiz and question from URL parameters."""
        super().setup(request, *args, **kwargs)
        self.quiz = get_object_or_404(Quiz, pk=kwargs["quiz_id"])
        self.question = get_object_or_404(Question, pk=kwargs["question_id"], quiz=self.quiz)
        self.answers = list(self.question.answers.order_by("order"))

    def dispatch(self, request, *args, **kwargs):
        """Reject if quiz is locked."""
        if self.quiz.is_locked:
            messages.error(request, "This quiz is locked and cannot be modified.")
            return redirect("admin-panel:quiz-detail", quiz_id=self.quiz.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        """Pre-populate form with the existing question text, type, and answer data."""
        initial = super().get_initial()
        initial["text"] = self.question.text
        initial["question_type"] = self.question.question_type
        labels = ["a", "b", "c", "d"]
        for i, label in enumerate(labels):
            if i < len(self.answers):
                initial[f"answer_{label}"] = self.answers[i].text
                initial[f"correct_{label}"] = self.answers[i].is_correct
        return initial

    def get_context_data(self, **kwargs):
        """Inject the quiz and question into template context."""
        context = super().get_context_data(**kwargs)
        context["quiz"] = self.quiz
        context["question"] = self.question
        return context

    def form_valid(self, form):
        """Update the question and its four answers, then redirect to quiz detail."""
        self.question.text = form.cleaned_data["text"]
        self.question.question_type = form.cleaned_data["question_type"]
        self.question.save(update_fields=["text", "question_type"])

        answer_data = [
            (form.cleaned_data["answer_a"], form.cleaned_data["correct_a"]),
            (form.cleaned_data["answer_b"], form.cleaned_data["correct_b"]),
            (form.cleaned_data["answer_c"], form.cleaned_data["correct_c"]),
            (form.cleaned_data["answer_d"], form.cleaned_data["correct_d"]),
        ]
        for answer, (text, is_correct) in zip(self.answers, answer_data):
            answer.text = text
            answer.is_correct = is_correct
            answer.save(update_fields=["text", "is_correct"])

        messages.success(self.request, "Question updated successfully.")
        return redirect("admin-panel:quiz-detail", quiz_id=self.quiz.pk)


class AdminQuizDuplicateView(AdminRequiredMixin, View):
    """Create a full copy of a quiz (questions + answers) that is unlocked and editable.

    The duplicate gets the title "Copy of <original title>", is_locked=False,
    and all questions/answers are deep-copied with fresh UUIDs.
    """

    def post(self, request, quiz_id: uuid.UUID):
        """Handle POST: duplicate the quiz and redirect to the new quiz's detail page."""
        source = get_object_or_404(Quiz, pk=quiz_id)

        new_quiz = Quiz.objects.create(
            title=f"Copy of {source.title}",
            description=source.description,
            questions_shown=source.questions_shown,
            passing_score=source.passing_score,
            created_by=request.user,
            is_locked=False,
        )

        for question in source.questions.prefetch_related("answers").order_by("order"):
            new_question = Question.objects.create(
                quiz=new_quiz,
                text=question.text,
                question_type=question.question_type,
                order=question.order,
            )
            for answer in question.answers.order_by("order"):
                Answer.objects.create(
                    question=new_question,
                    text=answer.text,
                    is_correct=answer.is_correct,
                    order=answer.order,
                )

        messages.success(request, f"Quiz duplicated as '{new_quiz.title}'.")
        return redirect("admin-panel:quiz-detail", quiz_id=new_quiz.pk)


class AdminQuizDeleteView(AdminRequiredMixin, View):
    """Delete a quiz and all its associated data.

    Manually removes enrolments (cascading attempts, attempt_questions, attempt_answers)
    and questions (cascading answers) before deleting the quiz itself, to satisfy
    the PROTECT constraints on those foreign keys.
    """

    def post(self, request, quiz_id: uuid.UUID):
        """Handle POST: delete the quiz and all related data unconditionally."""
        from apps.enrolments.models import Enrolment

        quiz = get_object_or_404(Quiz, pk=quiz_id)
        title = quiz.title
        # 1. Remove enrolments → cascades attempts → attempt_questions → attempt_answers
        Enrolment.objects.filter(quiz=quiz).delete()
        # 2. Remove questions → cascades answers
        quiz.questions.all().delete()
        # 3. Remove the quiz itself
        quiz.delete()
        messages.success(request, f"Quiz '{title}' has been deleted.")
        return redirect("admin-panel:quiz-list")


class AdminImageUploadView(AdminRequiredMixin, FormView):
    """Upload an image and return a Markdown snippet for use in question text."""

    template_name = "admin_panel/image-upload.html"
    form_class = ImageUploadForm

    def form_valid(self, form):
        """Validate, rename, and save the uploaded image; display the Markdown snippet."""
        from django.conf import settings
        from PIL import Image as PilImage

        image_file = form.cleaned_data["image"]
        ext = os.path.splitext(image_file.name)[1].lower()

        # Verify the file is a real image using Pillow
        try:
            img = PilImage.open(image_file)
            img.verify()
        except Exception:
            form.add_error("image", "The uploaded file is not a valid image.")
            return self.form_invalid(form)

        # Re-open after verify() (verify() exhausts the stream)
        image_file.seek(0)

        # Generate a UUID-based filename to prevent enumeration/injection
        new_filename = f"{uuid.uuid4()}{ext}"
        upload_dir = os.path.join(settings.MEDIA_ROOT, "questions")
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, new_filename)

        with open(file_path, "wb") as f:
            for chunk in image_file.chunks():
                f.write(chunk)

        markdown_snippet = f"![image description]({settings.MEDIA_URL}questions/{new_filename})"
        return self.render_to_response(
            self.get_context_data(form=ImageUploadForm(), markdown_snippet=markdown_snippet)
        )
