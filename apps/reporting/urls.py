"""URL configuration for the reporting app (under /admin-panel/reports/)."""
from django.urls import path

from apps.reporting import views

app_name = "reporting"

urlpatterns = [
    path("", views.ReportHomeView.as_view(), name="report-home"),
    path("quiz/<uuid:quiz_id>/", views.QuizReportView.as_view(), name="quiz-report"),
    path("quiz/<uuid:quiz_id>/students/", views.QuizStudentsReportView.as_view(), name="quiz-students"),
    path("students/", views.StudentOverviewReportView.as_view(), name="students-overview"),
    path(
        "certificate/<uuid:enrolment_id>/",
        views.AdminCertificateDownloadView.as_view(),
        name="certificate",
    ),
]
