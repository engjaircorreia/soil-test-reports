from django.db import models


class Job(models.Model):
    STATUS_UPLOADED = "uploaded"
    STATUS_EXTRACTING = "extracting"
    STATUS_REVIEW_PENDING = "review_pending"
    STATUS_GENERATING = "generating"
    STATUS_DONE = "done"
    STATUS_ERROR = "error"

    STATUS_CHOICES = [
        (STATUS_UPLOADED, "Uploaded"),
        (STATUS_EXTRACTING, "Extracting"),
        (STATUS_REVIEW_PENDING, "Review pending"),
        (STATUS_GENERATING, "Generating"),
        (STATUS_DONE, "Done"),
        (STATUS_ERROR, "Error"),
    ]

    LANGUAGE_CHOICES = [
        ("pt", "Português"),
        ("en", "English"),
    ]

    TEST_TYPE_CHOICES = [
        ("compactacao_cbr", "Proctor / CBR"),
        ("granulometria", "Granulometria"),
        ("ambos", "Ambos"),
    ]

    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_UPLOADED)
    language = models.CharField(max_length=8, choices=LANGUAGE_CHOICES, default="pt")
    test_type = models.CharField(max_length=32, choices=TEST_TYPE_CHOICES, default="ambos")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    original_files = models.JSONField(default=list, blank=True)
    openai_raw_response = models.JSONField(null=True, blank=True)
    extracted_data = models.JSONField(default=dict, blank=True)
    reviewed_data = models.JSONField(default=dict, blank=True)
    output_files = models.JSONField(default=list, blank=True)
    error_message = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"Job #{self.pk} - {self.get_status_display()}"

# Create your models here.
