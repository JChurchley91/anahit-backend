from django.db import models
from django.contrib.auth.models import User


class NewsSearchConfig(models.Model):
    """Configuration for news searches that will be used by the scraper app"""

    FREQUENCY_CHOICES = [
        ("hourly", "Hourly"),
        ("daily", "Daily"),
        ("weekly", "Weekly"),
    ]

    COUNTRY_CHOICES = [
        ("us", "United States"),
        ("uk", "United Kingdom"),
        ("ca", "Canada"),
    ]

    CATEGORY_CHOICES = [
        ("general", "General"),
        ("business", "Business"),
        ("technology", "Technology"),
    ]

    SORT_BY_CHOICES = [
        ("publishedAt", "Published Date"),
        ("relevancy", "Relevancy"),
        ("popularity", "Popularity"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="news_configs"
    )
    name = models.CharField(
        max_length=200, help_text="Friendly name for this search configuration"
    )

    # Search parameters aligned with NewsAPI top-headlines endpoint
    keywords = models.TextField(
        blank=True, help_text="Keywords or phrases to search for"
    )
    country = models.CharField(
        max_length=2,
        choices=COUNTRY_CHOICES,
        default="us",
        help_text="Country to get headlines for",
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="general",
        help_text="Category to get headlines for",
    )
    sources = models.TextField(
        blank=True,
        help_text="Specific news sources (comma-separated, e.g. bbc-news,cnn)",
    )
    sort_by = models.CharField(
        max_length=20, choices=SORT_BY_CHOICES, default="publishedAt"
    )

    # Scheduling
    frequency = models.CharField(
        max_length=10, choices=FREQUENCY_CHOICES, default="daily"
    )
    is_active = models.BooleanField(
        default=True, help_text="Whether this search should be executed"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_executed = models.DateTimeField(
        null=True, blank=True, help_text="Last time this search was executed"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "News Search Configuration"
        verbose_name_plural = "News Search Configurations"

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    def get_sources_list(self):
        """Return sources as a list"""
        return (
            [s.strip() for s in self.sources.split(",") if s.strip()]
            if self.sources
            else []
        )

    def get_newsapi_params(self):
        """Return parameters formatted for NewsAPI top-headlines endpoint"""
        params = {
            "country": self.country,
            "category": self.category,
            "sortBy": self.sort_by,
        }

        if self.keywords:
            params["q"] = self.keywords

        if self.sources:
            params["sources"] = ",".join(self.get_sources_list())
            # Note: sources parameter cannot be mixed with country/category in NewsAPI
            params.pop("country", None)
            params.pop("category", None)

        return params


class NewsArticle(models.Model):
    """Stores news articles retrieved by the scraper from NewsAPI"""

    search_config = models.ForeignKey(
        NewsSearchConfig, on_delete=models.CASCADE, related_name="articles"
    )

    # Article data from NewsAPI response
    title = models.TextField(help_text="Article headline")
    description = models.TextField(
        blank=True, null=True, help_text="Article snippet or description"
    )
    url = models.URLField(unique=True, help_text="Direct URL to the article")
    url_to_image = models.URLField(
        blank=True, null=True, help_text="URL to article image"
    )
    published_at = models.DateTimeField(help_text="Publication date and time")
    content = models.TextField(
        blank=True, null=True, help_text="Truncated article content (max 200 chars)"
    )

    # Source information
    source_id = models.CharField(
        max_length=100, blank=True, null=True, help_text="NewsAPI source identifier"
    )
    source_name = models.CharField(max_length=200, help_text="Source name")
    author = models.CharField(
        max_length=200, blank=True, null=True, help_text="Article author"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False, help_text="User read status")

    class Meta:
        ordering = ["-published_at"]
        verbose_name = "News Article"
        verbose_name_plural = "News Articles"
        indexes = [
            models.Index(fields=["published_at"]),
            models.Index(fields=["source_name"]),
            models.Index(fields=["is_read"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.source_name})"

    @classmethod
    def create_from_newsapi(cls, article_data, search_config):
        """Create a NewsArticle from NewsAPI response data"""
        return cls.objects.get_or_create(
            url=article_data["url"],
            defaults={
                "search_config": search_config,
                "title": article_data["title"],
                "description": article_data.get("description"),
                "url_to_image": article_data.get("urlToImage"),
                "published_at": article_data["publishedAt"],
                "content": article_data.get("content"),
                "source_id": article_data["source"].get("id")
                if article_data.get("source")
                else None,
                "source_name": article_data["source"]["name"]
                if article_data.get("source")
                else "Unknown",
                "author": article_data.get("author"),
            },
        )
