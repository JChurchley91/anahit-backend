# Generated by Django 5.2.3 on 2025-06-30 16:06

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="NewsSearchConfig",
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
                (
                    "name",
                    models.CharField(
                        help_text="Friendly name for this search configuration",
                        max_length=200,
                    ),
                ),
                (
                    "keywords",
                    models.TextField(
                        help_text="Keywords to search for (comma-separated)"
                    ),
                ),
                (
                    "sources",
                    models.TextField(
                        blank=True,
                        help_text="Specific news sources (comma-separated, e.g. bbc-news,cnn)",
                    ),
                ),
                (
                    "domains",
                    models.TextField(
                        blank=True,
                        help_text="Specific domains (comma-separated, e.g. bbc.co.uk,techcrunch.com)",
                    ),
                ),
                (
                    "exclude_domains",
                    models.TextField(
                        blank=True, help_text="Domains to exclude (comma-separated)"
                    ),
                ),
                (
                    "language",
                    models.CharField(
                        choices=[
                            ("en", "English"),
                            ("es", "Spanish"),
                            ("fr", "French"),
                            ("de", "German"),
                            ("it", "Italian"),
                            ("pt", "Portuguese"),
                        ],
                        default="en",
                        max_length=2,
                    ),
                ),
                (
                    "sort_by",
                    models.CharField(
                        choices=[
                            ("publishedAt", "Published Date"),
                            ("relevancy", "Relevancy"),
                            ("popularity", "Popularity"),
                        ],
                        default="publishedAt",
                        max_length=20,
                    ),
                ),
                (
                    "frequency",
                    models.CharField(
                        choices=[
                            ("hourly", "Hourly"),
                            ("daily", "Daily"),
                            ("weekly", "Weekly"),
                        ],
                        default="daily",
                        max_length=10,
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True, help_text="Whether this search should be executed"
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "last_executed",
                    models.DateTimeField(
                        blank=True,
                        help_text="Last time this search was executed",
                        null=True,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="news_configs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "News Search Configuration",
                "verbose_name_plural": "News Search Configurations",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="NewsArticle",
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
                ("title", models.TextField()),
                ("description", models.TextField(blank=True)),
                ("url", models.URLField(unique=True)),
                ("url_to_image", models.URLField(blank=True)),
                ("published_at", models.DateTimeField()),
                ("source_name", models.CharField(max_length=200)),
                ("author", models.CharField(blank=True, max_length=200)),
                ("content", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("is_read", models.BooleanField(default=False)),
                (
                    "search_config",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="articles",
                        to="news_config.newssearchconfig",
                    ),
                ),
            ],
            options={
                "verbose_name": "News Article",
                "verbose_name_plural": "News Articles",
                "ordering": ["-published_at"],
            },
        ),
    ]
