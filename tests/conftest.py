import pytest
from django.contrib.auth.models import User
from django.test import Client
from datetime import datetime, timezone
import factory
from factory.django import DjangoModelFactory
from news_config.models import NewsSearchConfig, NewsArticle


@pytest.fixture
def client():
    """Django test client"""
    return Client()


@pytest.fixture
def user():
    """Create a test user"""
    return User.objects.create_user(
        username="testuser", email="test@example.com", password="testpass123"
    )


@pytest.fixture
def admin_user():
    """Create an admin user"""
    return User.objects.create_superuser(
        username="admin", email="admin@example.com", password="adminpass123"
    )


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")


class NewsSearchConfigFactory(DjangoModelFactory):
    class Meta:
        model = NewsSearchConfig

    user = factory.SubFactory(UserFactory)
    name = factory.Faker("sentence", nb_words=3)
    keywords = factory.Faker("words", nb=3)
    country = "us"
    category = "general"
    sources = ""
    sort_by = "publishedAt"
    frequency = "daily"
    is_active = True


class NewsArticleFactory(DjangoModelFactory):
    class Meta:
        model = NewsArticle

    search_config = factory.SubFactory(NewsSearchConfigFactory)
    title = factory.Faker("sentence")
    description = factory.Faker("text", max_nb_chars=200)
    url = factory.Faker("url")
    url_to_image = factory.Faker("image_url")
    published_at = factory.Faker("date_time", tzinfo=timezone.utc)
    content = factory.Faker("text", max_nb_chars=200)
    source_id = factory.Faker("slug")
    source_name = factory.Faker("company")
    author = factory.Faker("name")
    is_read = False


@pytest.fixture
def news_config(user):
    """Create a test news search configuration"""
    return NewsSearchConfigFactory(user=user)


@pytest.fixture
def news_article(news_config):
    """Create a test news article"""
    return NewsArticleFactory(search_config=news_config)


@pytest.fixture
def sample_newsapi_article():
    """Sample article data in NewsAPI format"""
    return {
        "source": {"id": "bbc-news", "name": "BBC News"},
        "author": "John Doe",
        "title": "Test Article Title",
        "description": "This is a test article description",
        "url": "https://example.com/article",
        "urlToImage": "https://example.com/image.jpg",
        "publishedAt": "2023-12-01T10:00:00Z",
        "content": "This is the article content...",
    }
