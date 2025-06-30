from ninja import NinjaAPI, Schema
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from typing import List, Optional
from datetime import datetime
from .models import NewsSearchConfig, NewsArticle


api = NinjaAPI(
    title="Anahit News API", description="API for managing news search configurations"
)


class NewsSearchConfigSchema(Schema):
    id: int
    user_id: int
    name: str
    keywords: Optional[str] = None
    country: str
    category: str
    sources: Optional[str] = None
    sort_by: str
    frequency: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_executed: Optional[datetime] = None


class NewsSearchConfigCreateSchema(Schema):
    name: str
    keywords: Optional[str] = None
    country: str = "us"
    category: str = "general"
    sources: Optional[str] = None
    sort_by: str = "publishedAt"
    frequency: str = "daily"
    is_active: bool = True


class NewsArticleSchema(Schema):
    id: int
    search_config_id: int
    title: str
    description: Optional[str] = None
    url: str
    url_to_image: Optional[str] = None
    published_at: datetime
    content: Optional[str] = None
    source_id: Optional[str] = None
    source_name: str
    author: Optional[str] = None
    created_at: datetime
    is_read: bool


@api.get(
    "/configs", response=List[NewsSearchConfigSchema], tags=["Search Configurations"]
)
def list_configs(request):
    """Get all active news search configurations"""
    return NewsSearchConfig.objects.filter(is_active=True)


@api.get(
    "/configs/{config_id}",
    response=NewsSearchConfigSchema,
    tags=["Search Configurations"],
)
def get_config(request, config_id: int):
    """Get a specific news search configuration"""
    return get_object_or_404(NewsSearchConfig, id=config_id)


@api.post("/configs", response=NewsSearchConfigSchema, tags=["Search Configurations"])
def create_config(request, payload: NewsSearchConfigCreateSchema):
    """Create a new news search configuration"""
    # For now, we'll use the first user or create a default user
    # In a real app, you'd get this from authentication
    user, created = User.objects.get_or_create(
        username="default_user", defaults={"email": "default@example.com"}
    )

    config = NewsSearchConfig.objects.create(user=user, **payload.dict())
    return config


@api.put(
    "/configs/{config_id}",
    response=NewsSearchConfigSchema,
    tags=["Search Configurations"],
)
def update_config(request, config_id: int, payload: NewsSearchConfigCreateSchema):
    """Update a news search configuration"""
    config = get_object_or_404(NewsSearchConfig, id=config_id)

    for attr, value in payload.dict().items():
        setattr(config, attr, value)

    config.save()
    return config


@api.delete("/configs/{config_id}", tags=["Search Configurations"])
def delete_config(request, config_id: int):
    """Delete a news search configuration"""
    config = get_object_or_404(NewsSearchConfig, id=config_id)
    config.delete()
    return {"success": True}


@api.patch(
    "/configs/{config_id}/last-executed",
    response=NewsSearchConfigSchema,
    tags=["Search Configurations"],
)
def update_last_executed(request, config_id: int):
    """Update the last_executed timestamp for a configuration (used by scraper)"""
    config = get_object_or_404(NewsSearchConfig, id=config_id)
    config.last_executed = datetime.now()
    config.save()
    return config


@api.get(
    "/configs/{config_id}/articles", response=List[NewsArticleSchema], tags=["Articles"]
)
def get_config_articles(request, config_id: int):
    """Get all articles for a specific configuration"""
    config = get_object_or_404(NewsSearchConfig, id=config_id)
    return config.articles.all()


class NewsArticleCreateSchema(Schema):
    search_config_id: int
    title: str
    description: Optional[str] = None
    url: str
    url_to_image: Optional[str] = None
    published_at: str  # ISO datetime string
    content: Optional[str] = None
    source_id: Optional[str] = None
    source_name: str
    author: Optional[str] = None


@api.post("/articles", response=NewsArticleSchema, tags=["Articles"])
def create_article(request, payload: NewsArticleCreateSchema):
    """Create a new news article (used by scraper)"""
    search_config = get_object_or_404(NewsSearchConfig, id=payload.search_config_id)

    article, created = NewsArticle.objects.get_or_create(
        url=payload.url,
        defaults={
            "search_config": search_config,
            "title": payload.title,
            "description": payload.description,
            "url_to_image": payload.url_to_image,
            "published_at": payload.published_at,
            "content": payload.content,
            "source_id": payload.source_id,
            "source_name": payload.source_name,
            "author": payload.author,
        },
    )

    return article


@api.post("/articles/from-newsapi", response=List[NewsArticleSchema], tags=["Articles"])
def create_articles_from_newsapi(
    request, search_config_id: int, articles_data: List[dict]
):
    """Create multiple articles from NewsAPI response (used by scraper)"""
    search_config = get_object_or_404(NewsSearchConfig, id=search_config_id)
    created_articles = []

    for article_data in articles_data:
        article, created = NewsArticle.create_from_newsapi(article_data, search_config)
        created_articles.append(article)

    return created_articles


@api.get("/articles", response=List[NewsArticleSchema], tags=["Articles"])
def list_articles(request, limit: int = 50):
    """Get recent articles across all configurations"""
    return NewsArticle.objects.all()[:limit]
