"""Student-facing URL configuration for the quizzes app."""
from django.urls import path

from apps.enrolments import views as enrolment_views
from apps.quizzes import views as quiz_views

app_name = "quizzes"

urlpatterns = [
    # Quiz catalogue (student home)
    path("", quiz_views.QuizListView.as_view(), name="quiz-list"),
    # Quiz detail
    path("<uuid:quiz_id>/", quiz_views.QuizDetailView.as_view(), name="quiz-detail"),
    # Enrolment (POST only)
    path("<uuid:quiz_id>/enrol/", enrolment_views.EnrolView.as_view(), name="enrol"),
    # Attempt: GET creates/resumes attempt and renders form; POST submits answers
    path("<uuid:quiz_id>/attempt/", enrolment_views.AttemptView.as_view(), name="attempt"),
    # Results page
    path(
        "<uuid:quiz_id>/results/<uuid:attempt_id>/",
        enrolment_views.AttemptResultsView.as_view(),
        name="results",
    ),
    # Certificate PDF download (student, own passed enrolment only)
    path(
        "<uuid:quiz_id>/certificate/",
        enrolment_views.CertificateDownloadView.as_view(),
        name="certificate",
    ),
]
