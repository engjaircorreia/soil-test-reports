from django.urls import path

from . import views

app_name = "ensaios"

urlpatterns = [
    path("", views.upload_view, name="upload"),
    path("upload/", views.upload_view, name="upload_post"),
    path("jobs/<int:job_id>/review/", views.review_view, name="review"),
    path("jobs/<int:job_id>/generate/", views.generate_view, name="generate"),
    path("jobs/<int:job_id>/result/", views.result_view, name="result"),
    path("jobs/<int:job_id>/download/<int:file_index>/", views.download_view, name="download"),
]
