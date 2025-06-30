import pytest
import json
from datetime import datetime, timezone
from django.urls import reverse
from django.contrib.auth.models import User
from news_config.models import NewsSearchConfig, NewsArticle
from tests.conftest import NewsSearchConfigFactory, NewsArticleFactory, UserFactory


@pytest.mark.django_db
class TestNewsSearchConfigAPI:
    """Tests for NewsSearchConfig API endpoints"""

    def test_list_configs(self, client):
        """Test GET /api/configs - list all active configurations"""
        user = UserFactory()
        active_config = NewsSearchConfigFactory(user=user, is_active=True)
        inactive_config = NewsSearchConfigFactory(user=user, is_active=False)

        response = client.get("/api/configs")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == active_config.id
        assert data[0]["name"] == active_config.name
        assert data[0]["is_active"] is True

    def test_get_config_detail(self, client, news_config):
        """Test GET /api/configs/{id} - get specific configuration"""
        response = client.get(f"/api/configs/{news_config.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == news_config.id
        assert data["name"] == news_config.name
        assert data["country"] == news_config.country
        assert data["category"] == news_config.category

    def test_get_config_not_found(self, client):
        """Test GET /api/configs/{id} with non-existent ID"""
        response = client.get("/api/configs/999")

        assert response.status_code == 404

    def test_create_config(self, client):
        """Test POST /api/configs - create new configuration"""
        payload = {
            "name": "Test Config",
            "keywords": "python programming",
            "country": "us",
            "category": "technology",
            "frequency": "daily",
        }

        response = client.post(
            "/api/configs", data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Config"
        assert data["keywords"] == "python programming"
        assert data["country"] == "us"
        assert data["category"] == "technology"
        assert data["is_active"] is True

        # Verify in database
        config = NewsSearchConfig.objects.get(id=data["id"])
        assert config.name == "Test Config"

    def test_create_config_with_sources(self, client):
        """Test creating config with sources"""
        payload = {
            "name": "Source Config",
            "sources": "bbc-news,cnn",
            "sort_by": "popularity",
        }

        response = client.post(
            "/api/configs", data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sources"] == "bbc-news,cnn"
        assert data["sort_by"] == "popularity"

    def test_update_config(self, client, news_config):
        """Test PUT /api/configs/{id} - update configuration"""
        payload = {
            "name": "Updated Config",
            "keywords": "updated keywords",
            "country": "ca",
            "category": "business",
            "frequency": "weekly",
            "is_active": False,
        }

        response = client.put(
            f"/api/configs/{news_config.id}",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Config"
        assert data["country"] == "ca"
        assert data["category"] == "business"
        assert data["is_active"] is False

        # Verify in database
        news_config.refresh_from_db()
        assert news_config.name == "Updated Config"
        assert news_config.country == "ca"

    def test_delete_config(self, client, news_config):
        """Test DELETE /api/configs/{id} - delete configuration"""
        config_id = news_config.id

        response = client.delete(f"/api/configs/{config_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify deletion
        assert not NewsSearchConfig.objects.filter(id=config_id).exists()

    def test_update_last_executed(self, client, news_config):
        """Test PATCH /api/configs/{id}/last-executed"""
        assert news_config.last_executed is None

        response = client.patch(f"/api/configs/{news_config.id}/last-executed")

        assert response.status_code == 200
        data = response.json()
        assert data["last_executed"] is not None

        # Verify in database
        news_config.refresh_from_db()
        assert news_config.last_executed is not None


@pytest.mark.django_db
class TestNewsArticleAPI:
    """Tests for NewsArticle API endpoints"""

    def test_list_articles(self, client):
        """Test GET /api/articles - list recent articles"""
        config = NewsSearchConfigFactory()
        article1 = NewsArticleFactory(search_config=config)
        article2 = NewsArticleFactory(search_config=config)

        response = client.get("/api/articles")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert any(a["id"] == article1.id for a in data)
        assert any(a["id"] == article2.id for a in data)

    def test_list_articles_with_limit(self, client):
        """Test GET /api/articles with limit parameter"""
        config = NewsSearchConfigFactory()
        for _ in range(5):
            NewsArticleFactory(search_config=config)

        response = client.get("/api/articles?limit=3")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_get_config_articles(self, client, news_config):
        """Test GET /api/configs/{id}/articles - get articles for specific config"""
        article1 = NewsArticleFactory(search_config=news_config)
        article2 = NewsArticleFactory(search_config=news_config)
        # Create article for different config
        other_config = NewsSearchConfigFactory()
        NewsArticleFactory(search_config=other_config)

        response = client.get(f"/api/configs/{news_config.id}/articles")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(a["search_config_id"] == news_config.id for a in data)

    def test_create_article(self, client, news_config):
        """Test POST /api/articles - create new article"""
        payload = {
            "search_config_id": news_config.id,
            "title": "Test Article",
            "description": "Test description",
            "url": "https://example.com/test-article",
            "url_to_image": "https://example.com/image.jpg",
            "published_at": "2023-12-01T10:00:00Z",
            "content": "Test content",
            "source_id": "test-source",
            "source_name": "Test Source",
            "author": "Test Author",
        }

        response = client.post(
            "/api/articles", data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Article"
        assert data["source_name"] == "Test Source"
        assert data["search_config_id"] == news_config.id

        # Verify in database
        article = NewsArticle.objects.get(id=data["id"])
        assert article.title == "Test Article"
        assert article.url == "https://example.com/test-article"

    def test_create_articles_from_newsapi(self, client, news_config):
        """Test POST /api/articles/from-newsapi - bulk create from NewsAPI"""
        articles_data = [
            {
                "source": {"id": "bbc-news", "name": "BBC News"},
                "author": "John Doe",
                "title": "Article 1",
                "description": "Description 1",
                "url": "https://example.com/article1",
                "urlToImage": "https://example.com/image1.jpg",
                "publishedAt": "2023-12-01T10:00:00Z",
                "content": "Content 1",
            },
            {
                "source": {"id": "cnn", "name": "CNN"},
                "author": "Jane Smith",
                "title": "Article 2",
                "description": "Description 2",
                "url": "https://example.com/article2",
                "urlToImage": "https://example.com/image2.jpg",
                "publishedAt": "2023-12-01T11:00:00Z",
                "content": "Content 2",
            },
        ]

        payload = {"search_config_id": news_config.id, "articles_data": articles_data}

        response = client.post(
            "/api/articles/from-newsapi",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["title"] == "Article 1"
        assert data[0]["source_name"] == "BBC News"
        assert data[1]["title"] == "Article 2"
        assert data[1]["source_name"] == "CNN"

        # Verify in database
        articles = NewsArticle.objects.filter(search_config=news_config)
        assert articles.count() == 2


@pytest.mark.django_db
class TestAPIErrorHandling:
    """Tests for API error handling"""

    def test_invalid_json(self, client):
        """Test handling of invalid JSON"""
        response = client.post(
            "/api/configs", data="invalid json", content_type="application/json"
        )

        assert response.status_code == 422

    def test_missing_required_fields(self, client):
        """Test handling of missing required fields"""
        payload = {
            "keywords": "test"
            # Missing required 'name' field
        }

        response = client.post(
            "/api/configs", data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 422

    def test_invalid_foreign_key(self, client):
        """Test handling of invalid foreign key reference"""
        payload = {
            "search_config_id": 999,  # Non-existent config
            "title": "Test Article",
            "url": "https://example.com/test",
            "published_at": "2023-12-01T10:00:00Z",
            "source_name": "Test Source",
        }

        response = client.post(
            "/api/articles", data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 404


@pytest.mark.django_db
class TestAPIIntegration:
    """Integration tests for API workflows"""

    def test_full_workflow(self, client):
        """Test complete workflow: create config, create articles, retrieve data"""
        # 1. Create configuration
        config_payload = {
            "name": "Integration Test Config",
            "keywords": "integration test",
            "country": "us",
            "category": "technology",
        }

        config_response = client.post(
            "/api/configs",
            data=json.dumps(config_payload),
            content_type="application/json",
        )
        assert config_response.status_code == 200
        config_id = config_response.json()["id"]

        # 2. Create article for the configuration
        article_payload = {
            "search_config_id": config_id,
            "title": "Integration Test Article",
            "url": "https://example.com/integration-test",
            "published_at": "2023-12-01T10:00:00Z",
            "source_name": "Test Source",
        }

        article_response = client.post(
            "/api/articles",
            data=json.dumps(article_payload),
            content_type="application/json",
        )
        assert article_response.status_code == 200

        # 3. Retrieve articles for the configuration
        articles_response = client.get(f"/api/configs/{config_id}/articles")
        assert articles_response.status_code == 200
        articles_data = articles_response.json()
        assert len(articles_data) == 1
        assert articles_data[0]["title"] == "Integration Test Article"

        # 4. Update last executed timestamp
        update_response = client.patch(f"/api/configs/{config_id}/last-executed")
        assert update_response.status_code == 200

        # 5. Verify configuration was updated
        config_detail_response = client.get(f"/api/configs/{config_id}")
        assert config_detail_response.status_code == 200
        config_data = config_detail_response.json()
        assert config_data["last_executed"] is not None
