# Generated manually for RAGDocument model

import apps.agents.models
import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("agents", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="RAGDocument",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                (
                    "file",
                    models.FileField(
                        upload_to=apps.agents.models.rag_document_upload_path,
                        validators=[
                            django.core.validators.FileExtensionValidator(
                                allowed_extensions=["pdf", "txt", "md", "docx", "csv"]
                            )
                        ],
                    ),
                ),
                ("file_type", models.CharField(blank=True, max_length=10)),
                (
                    "file_size",
                    models.PositiveIntegerField(
                        default=0, help_text="File size in bytes"
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending Processing"),
                            ("processing", "Processing"),
                            ("indexed", "Indexed"),
                            ("failed", "Failed"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("error_message", models.TextField(blank=True)),
                ("chunk_count", models.PositiveIntegerField(default=0)),
                (
                    "scope",
                    models.CharField(
                        choices=[
                            ("global", "Global (all users)"),
                            ("user", "User-specific"),
                        ],
                        default="global",
                        max_length=10,
                    ),
                ),
                ("tags", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "uploaded_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rag_documents",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "RAG Document",
                "verbose_name_plural": "RAG Documents",
                "db_table": "rag_documents",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(
                        fields=["uploaded_by", "-created_at"],
                        name="rag_documents_uploade_c1a2b3_idx",
                    ),
                    models.Index(
                        fields=["status"],
                        name="rag_documents_status_d4e5f6_idx",
                    ),
                    models.Index(
                        fields=["scope"],
                        name="rag_documents_scope_a7b8c9_idx",
                    ),
                ],
            },
        ),
    ]
