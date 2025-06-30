import pytest
from datetime import datetime, timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from news_config.models import NewsSearchConfig, NewsArticle
from tests.conftest import NewsSearchConfigFactory, NewsArticleFactory, UserFactory


@pytest.mark.django_db
class TestNewsSearchConfig:
    """Tests for NewsSearchConfig model"""

    def test_create_news_search_config(self, user):
        """Test creating a news search configuration"""
        config = NewsSearchConfig.objects.create(
            user=user,
            name="Tech News",
            keywords="artificial intelligence",
            country="us",
            category="technology",
            frequency="daily",
        )

        assert config.name == "Tech News"
        assert config.keywords == "artificial intelligence"
        assert config.country == "us"
        assert config.category == "technology"
        assert config.frequency == "daily"
        assert config.is_active is True
        assert config.user == user

    def test_str_representation(self, user):
        """Test string representation of NewsSearchConfig"""
        config = NewsSearchConfig.objects.create(
            user=user, name="Business News", country="uk", category="business"
        )

        assert str(config) == f"Business News ({user.username})"

    def test_get_sources_list(self, user):
        """Test get_sources_list method"""
        config = NewsSearchConfig.objects.create(
            user=user,
            name="Test Config",
            sources="bbc-news,cnn,techcrunch",
            country="us",
            category="general",
        )

        sources = config.get_sources_list()
        assert sources == ["bbc-news", "cnn", "techcrunch"]

    def test_get_sources_list_empty(self, user):
        """Test get_sources_list with empty sources"""
        config = NewsSearchConfig.objects.create(
            user=user, name="Test Config", sources="", country="us", category="general"
        )

        sources = config.get_sources_list()
        assert sources == []

    def test_get_newsapi_params_basic(self, user):
        """Test get_newsapi_params method with basic parameters"""
        config = NewsSearchConfig.objects.create(
            user=user,
            name="Test Config",
            keywords="python programming",
            country="us",
            category="technology",
            sort_by="popularity",
        )

        params = config.get_newsapi_params()
        expected = {
            "country": "us",
            "category": "technology",
            "sortBy": "popularity",
            "q": "python programming",
        }

        assert params == expected

    def test_get_newsapi_params_with_sources(self, user):
        """Test get_newsapi_params when sources are provided"""
        config = NewsSearchConfig.objects.create(
            user=user,
            name="Test Config",
            keywords="breaking news",
            sources="bbc-news,cnn",
            country="us",
            category="general",
        )

        params = config.get_newsapi_params()
        expected = {
            "sortBy": "publishedAt",
            "q": "breaking news",
            "sources": "bbc-news,cnn",
        }

        assert params == expected
        assert "country" not in params
        assert "category" not in params

    def test_choice_fields_validation(self, user):
        """Test that choice fields accept valid values"""
        config = NewsSearchConfig.objects.create(
            user=user,
            name="Test Config",
            country="ca",
            category="business",
            frequency="weekly",
            sort_by="relevancy",
        )

        assert config.country == "ca"
        assert config.category == "business"
        assert config.frequency == "weekly"
        assert config.sort_by == "relevancy"

    def test_user_cascade_delete(self):
        """Test that deleting user cascades to configs"""
        user = UserFactory()
        config = NewsSearchConfigFactory(user=user)
        config_id = config.id

        user.delete()

        assert not NewsSearchConfig.objects.filter(id=config_id).exists()


@pytest.mark.django_db
class TestNewsArticle:
    """Tests for NewsArticle model"""

    def test_create_news_article(self, news_config):
        """Test creating a news article"""
        article = NewsArticle.objects.create(
            search_config=news_config,
            title="Test Article",
            description="Test description",
            url="https://example.com/article",
            url_to_image="https://example.com/image.jpg",
            published_at=datetime(2023, 12, 1, 10, 0, 0, tzinfo=timezone.utc),
            content="Test content",
            source_id="test-source",
            source_name="Test Source",
            author="Test Author",
        )

        assert article.title == "Test Article"
        assert article.description == "Test description"
        assert article.url == "https://example.com/article"
        assert article.source_name == "Test Source"
        assert article.is_read is False
        assert article.search_config == news_config

    def test_str_representation(self, news_article):
        """Test string representation of NewsArticle"""
        expected = f"{news_article.title} ({news_article.source_name})"
        assert str(news_article) == expected

    def test_url_uniqueness(self, news_config):
        """Test that article URLs must be unique"""
        url = "https://example.com/unique-article"

        NewsArticle.objects.create(
            search_config=news_config,
            title="First Article",
            url=url,
            published_at=datetime.now(timezone.utc),
            source_name="Source One",
        )

        with pytest.raises(IntegrityError):
            NewsArticle.objects.create(
                search_config=news_config,
                title="Second Article",
                url=url,
                published_at=datetime.now(timezone.utc),
                source_name="Source Two",
            )

    def test_create_from_newsapi(self, news_config, sample_newsapi_article):
        """Test creating article from NewsAPI data"""
        article, created = NewsArticle.create_from_newsapi(
            sample_newsapi_article, news_config
        )

        assert created is True
        assert article.title == "Test Article Title"
        assert article.description == "This is a test article description"
        assert article.url == "https://example.com/article"
        assert article.url_to_image == "https://example.com/image.jpg"
        assert article.source_id == "bbc-news"
        assert article.source_name == "BBC News"
        assert article.author == "John Doe"
        assert article.content == "This is the article content..."
        assert article.search_config == news_config

    def test_create_from_newsapi_duplicate(self, news_config, sample_newsapi_article):
        """Test creating duplicate article from NewsAPI data"""
        # Create first article
        article1, created1 = NewsArticle.create_from_newsapi(
            sample_newsapi_article, news_config
        )

        # Try to create duplicate
        article2, created2 = NewsArticle.create_from_newsapi(
            sample_newsapi_article, news_config
        )

        assert created1 is True
        assert created2 is False
        assert article1.id == article2.id

    def test_create_from_newsapi_no_source(self, news_config):
        """Test creating article from NewsAPI data without source"""
        article_data = {
            "title": "No Source Article",
            "url": "https://example.com/no-source",
            "publishedAt": "2023-12-01T10:00:00Z",
        }

        article, created = NewsArticle.create_from_newsapi(article_data, news_config)

        assert created is True
        assert article.source_name == "Unknown"
        assert article.source_id is None

    def test_ordering(self, news_config):
        """Test that articles are ordered by published_at descending"""
        older_article = NewsArticleFactory(
            search_config=news_config,
            published_at=datetime(2023, 12, 1, tzinfo=timezone.utc),
        )
        newer_article = NewsArticleFactory(
            search_config=news_config,
            published_at=datetime(2023, 12, 2, tzinfo=timezone.utc),
        )

        articles = list(NewsArticle.objects.all())
        assert articles[0] == newer_article
        assert articles[1] == older_article

    def test_search_config_cascade_delete(self, news_config):
        """Test that deleting search config cascades to articles"""
        article = NewsArticleFactory(search_config=news_config)
        article_id = article.id

        news_config.delete()

        assert not NewsArticle.objects.filter(id=article_id).exists()


@pytest.mark.django_db
class TestModelIntegration:
    """Integration tests for model relationships"""

    def test_user_configs_relationship(self, user):
        """Test user -> configs relationship"""
        config1 = NewsSearchConfigFactory(user=user, name="Config 1")
        config2 = NewsSearchConfigFactory(user=user, name="Config 2")

        user_configs = user.news_configs.all()
        assert config1 in user_configs
        assert config2 in user_configs
        assert user_configs.count() == 2

    def test_config_articles_relationship(self, news_config):
        """Test config -> articles relationship"""
        article1 = NewsArticleFactory(search_config=news_config)
        article2 = NewsArticleFactory(search_config=news_config)

        config_articles = news_config.articles.all()
        assert article1 in config_articles
        assert article2 in config_articles
        assert config_articles.count() == 2
