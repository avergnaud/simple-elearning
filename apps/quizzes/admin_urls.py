"""Admin-panel URL configuration (quiz management + reporting)."""
from django.urls import include, path

from apps.quizzes import views

app_name = "admin-panel"

urlpatterns = [
    # Dashboard
    path("", views.AdminDashboardView.as_view(), name="dashboard"),
    # Quiz management
    path("quizzes/", views.AdminQuizListView.as_view(), name="quiz-list"),
    path("quizzes/create/", views.AdminQuizCreateView.as_view(), name="quiz-create"),
    path("quizzes/<uuid:quiz_id>/", views.AdminQuizDetailView.as_view(), name="quiz-detail"),
    path("quizzes/<uuid:quiz_id>/duplicate/", views.AdminQuizDuplicateView.as_view(), name="quiz-duplicate"),
    path("quizzes/<uuid:quiz_id>/delete/", views.AdminQuizDeleteView.as_view(), name="quiz-delete"),
    path(
        "quizzes/<uuid:quiz_id>/questions/add/",
        views.AdminQuestionAddView.as_view(),
        name="question-add",
    ),
    path(
        "quizzes/<uuid:quiz_id>/questions/<uuid:question_id>/edit/",
        views.AdminQuestionEditView.as_view(),
        name="question-edit",
    ),
    # Image upload
    path("media/upload/", views.AdminImageUploadView.as_view(), name="image-upload"),
    # Reporting (nested namespace)
    path("reports/", include("apps.reporting.urls", namespace="reporting")),
]
