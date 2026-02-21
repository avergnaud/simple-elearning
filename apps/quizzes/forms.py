"""Forms for creating quizzes and questions (admin-facing)."""
from django import forms
from django.utils.translation import gettext_lazy as _

from apps.quizzes.models import Answer, Question, Quiz


class QuizCreateForm(forms.ModelForm):
    """Form for creating a new quiz.

    The passing score is fixed at 70% in the MVP and is displayed as read-only.
    """

    class Meta:
        model = Quiz
        fields = ["title", "description", "questions_shown"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }
        help_texts = {
            "description": _("Optional. Supports Markdown formatting."),
            "questions_shown": _("How many questions will be randomly shown per attempt."),
        }

    def clean_questions_shown(self):
        """Validate that questions_shown is at least 1."""
        value = self.cleaned_data.get("questions_shown")
        if value is not None and value < 1:
            raise forms.ValidationError(_("Must show at least 1 question per attempt."))
        return value


class QuestionAddForm(forms.ModelForm):
    """Form for adding a question with its four answers to a quiz.

    All four answer fields are required. Correct-answer checkboxes enforce
    the single/multiple-choice constraint.
    """

    answer_a = forms.CharField(max_length=500, label=_("Answer A"))
    answer_b = forms.CharField(max_length=500, label=_("Answer B"))
    answer_c = forms.CharField(max_length=500, label=_("Answer C"))
    answer_d = forms.CharField(max_length=500, label=_("Answer D"))

    correct_a = forms.BooleanField(required=False, label=_("Correct"))
    correct_b = forms.BooleanField(required=False, label=_("Correct"))
    correct_c = forms.BooleanField(required=False, label=_("Correct"))
    correct_d = forms.BooleanField(required=False, label=_("Correct"))

    class Meta:
        model = Question
        fields = ["text", "question_type"]
        widgets = {
            "text": forms.Textarea(attrs={"rows": 5}),
        }
        help_texts = {
            "text": _("Supports Markdown. Use the image uploader above to embed images."),
        }

    def clean(self):
        """Validate correct-answer counts against the selected question type."""
        cleaned_data = super().clean()
        question_type = cleaned_data.get("question_type")
        correct_flags = [
            cleaned_data.get("correct_a"),
            cleaned_data.get("correct_b"),
            cleaned_data.get("correct_c"),
            cleaned_data.get("correct_d"),
        ]
        correct_count = sum(bool(f) for f in correct_flags)

        if correct_count == 0:
            raise forms.ValidationError(_("At least one answer must be marked as correct."))

        if question_type == Question.TYPE_SINGLE and correct_count != 1:
            raise forms.ValidationError(
                _("Single-choice questions must have exactly one correct answer.")
            )

        if question_type == Question.TYPE_MULTIPLE and correct_count < 2:
            raise forms.ValidationError(
                _("Multiple-choice questions must have at least two correct answers.")
            )

        return cleaned_data


class ImageUploadForm(forms.Form):
    """Simple form for uploading an image to embed in a question."""

    image = forms.ImageField(
        label=_("Image file"),
        help_text=_("Accepted: PNG, JPG, GIF, WebP. Maximum size: 5 MB."),
    )

    def clean_image(self):
        """Validate file extension and size."""
        image = self.cleaned_data.get("image")
        if image is None:
            return image

        allowed_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
        import os
        ext = os.path.splitext(image.name)[1].lower()
        if ext not in allowed_extensions:
            raise forms.ValidationError(
                _("Unsupported file type. Allowed: PNG, JPG, GIF, WebP.")
            )

        max_size = 5 * 1024 * 1024  # 5 MB
        if image.size > max_size:
            raise forms.ValidationError(_("File size must not exceed 5 MB."))

        return image
