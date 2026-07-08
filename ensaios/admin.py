from django.contrib import admin

from .models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "language", "test_type", "created_at", "updated_at")
    list_filter = ("status", "language", "test_type")
    search_fields = ("id",)

# Register your models here.
