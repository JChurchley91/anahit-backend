from django.contrib import admin
from .models import NewsSearchConfig, NewsArticle


@admin.register(NewsSearchConfig)
class NewsSearchConfigAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "user",
        "country",
        "category",
        "frequency",
        "is_active",
        "last_executed",
        "created_at",
    )
    list_filter = ("is_active", "frequency", "country", "category", "created_at")
    search_fields = ("name", "keywords", "user__username")
    readonly_fields = ("created_at", "updated_at", "last_executed")
    fieldsets = (
        ("Basic Information", {"fields": ("user", "name", "is_active")}),
        (
            "Search Parameters",
            {"fields": ("keywords", "country", "category", "sources", "sort_by")},
        ),
        ("Scheduling", {"fields": ("frequency",)}),
        (
            "Metadata",
            {
                "fields": ("created_at", "updated_at", "last_executed"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "source_name",
        "author",
        "search_config",
        "published_at",
        "is_read",
        "created_at",
    )
    list_filter = (
        "is_read",
        "source_name",
        "search_config",
        "published_at",
        "created_at",
    )
    search_fields = ("title", "description", "source_name", "author", "source_id")
    readonly_fields = ("created_at",)
    date_hierarchy = "published_at"
    fieldsets = (
        (
            "Article Information",
            {
                "fields": (
                    "search_config",
                    "title",
                    "description",
                    "url",
                    "url_to_image",
                )
            },
        ),
        (
            "Source & Publication",
            {"fields": ("source_id", "source_name", "author", "published_at")},
        ),
        ("Content", {"fields": ("content",), "classes": ("collapse",)}),
        ("Status", {"fields": ("is_read", "created_at")}),
    )
