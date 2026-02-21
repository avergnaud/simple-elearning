"""Student-facing quiz views and admin quiz-management views."""
import uuid
import os

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, FormView, ListView, TemplateView, View

from apps.accounts.mixins import AdminRequiredMixin
from apps.quizzes.forms import ImageUploadForm, QuestionAddForm, QuizCreateForm
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
            raise PermissionDenied
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
            raise PermissionDenied
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
