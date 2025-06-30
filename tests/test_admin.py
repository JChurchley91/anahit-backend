import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import RequestFactory
from news_config.admin import NewsSearchConfigAdmin, NewsArticleAdmin
from news_config.models import NewsSearchConfig, NewsArticle
from tests.conftest import NewsSearchConfigFactory, NewsArticleFactory, UserFactory


@pytest.mark.django_db
class TestNewsSearchConfigAdmin:
    """Tests for NewsSearchConfig admin interface"""

    def setup_method(self):
        """Set up test data for each test"""
        self.site = AdminSite()
        self.admin = NewsSearchConfigAdmin(NewsSearchConfig, self.site)
        self.factory = RequestFactory()

    def test_list_display(self):
        """Test that list_display contains expected fields"""
        expected_fields = [
            "name",
            "user",
            "country",
            "category",
            "frequency",
            "is_active",
            "last_executed",
            "created_at",
        ]
        assert self.admin.list_display == tuple(expected_fields)

    def test_list_filter(self):
        """Test that list_filter contains expected fields"""
        expected_filters = [
            "is_active",
            "frequency",
            "country",
            "category",
            "created_at",
        ]
        assert self.admin.list_filter == tuple(expected_filters)

    def test_search_fields(self):
        """Test that search_fields contains expected fields"""
        expected_search = ["name", "keywords", "user__username"]
        assert self.admin.search_fields == expected_search

    def test_readonly_fields(self):
        """Test that readonly_fields contains metadata fields"""
        expected_readonly = ("created_at", "updated_at", "last_executed")
        assert self.admin.readonly_fields == expected_readonly

    def test_fieldsets_structure(self):
        """Test that fieldsets are properly structured"""
        fieldsets = self.admin.fieldsets

        # Should have 4 sections
        assert len(fieldsets) == 4

        # Check section names
        section_names = [fieldset[0] for fieldset in fieldsets]
        expected_sections = [
            "Basic Information",
            "Search Parameters",
            "Scheduling",
            "Metadata",
        ]
        assert section_names == expected_sections

    def test_admin_display_methods(self, admin_user):
        """Test admin interface with actual data"""
        user = UserFactory()
        config = NewsSearchConfigFactory(
            user=user,
            name="Test Admin Config",
            country="us",
            category="technology",
            is_active=True,
        )

        # Test string representation shows in admin
        assert str(config) == f"Test Admin Config ({user.username})"

        # Test that config appears in queryset
        request = self.factory.get("/admin/news_config/newssearchconfig/")
        request.user = admin_user

        queryset = self.admin.get_queryset(request)
        assert config in queryset


@pytest.mark.django_db
class TestNewsArticleAdmin:
    """Tests for NewsArticle admin interface"""

    def setup_method(self):
        """Set up test data for each test"""
        self.site = AdminSite()
        self.admin = NewsArticleAdmin(NewsArticle, self.site)
        self.factory = RequestFactory()

    def test_list_display(self):
        """Test that list_display contains expected fields"""
        expected_fields = [
            "title",
            "source_name",
            "author",
            "search_config",
            "published_at",
            "is_read",
            "created_at",
        ]
        assert self.admin.list_display == tuple(expected_fields)

    def test_list_filter(self):
        """Test that list_filter contains expected fields"""
        expected_filters = [
            "is_read",
            "source_name",
            "search_config",
            "published_at",
            "created_at",
        ]
        assert self.admin.list_filter == tuple(expected_filters)

    def test_search_fields(self):
        """Test that search_fields contains expected fields"""
        expected_search = ["title", "description", "source_name", "author", "source_id"]
        assert self.admin.search_fields == expected_search

    def test_date_hierarchy(self):
        """Test that date_hierarchy is set to published_at"""
        assert self.admin.date_hierarchy == "published_at"

    def test_readonly_fields(self):
        """Test that readonly_fields contains created_at"""
        expected_readonly = ("created_at",)
        assert self.admin.readonly_fields == expected_readonly

    def test_fieldsets_structure(self):
        """Test that fieldsets are properly structured"""
        fieldsets = self.admin.fieldsets

        # Should have 4 sections
        assert len(fieldsets) == 4

        # Check section names
        section_names = [fieldset[0] for fieldset in fieldsets]
        expected_sections = [
            "Article Information",
            "Source & Publication",
            "Content",
            "Status",
        ]
        assert section_names == expected_sections

    def test_content_section_collapsed(self):
        """Test that Content section has collapse class"""
        fieldsets = self.admin.fieldsets
        content_section = fieldsets[2]  # Content is the 3rd section

        assert content_section[0] == "Content"
        assert "classes" in content_section[1]
        assert "collapse" in content_section[1]["classes"]

    def test_admin_display_methods(self, admin_user):
        """Test admin interface with actual data"""
        config = NewsSearchConfigFactory()
        article = NewsArticleFactory(
            search_config=config,
            title="Test Admin Article",
            source_name="Test Source",
            is_read=False,
        )

        # Test string representation shows in admin
        assert str(article) == "Test Admin Article (Test Source)"

        # Test that article appears in queryset
        request = self.factory.get("/admin/news_config/newsarticle/")
        request.user = admin_user

        queryset = self.admin.get_queryset(request)
        assert article in queryset


@pytest.mark.django_db
class TestAdminIntegration:
    """Integration tests for admin interface"""

    def test_config_admin_changelist(self, admin_client):
        """Test admin changelist view for configurations"""
        user = UserFactory()
        config = NewsSearchConfigFactory(user=user, name="Admin Test Config")

        response = admin_client.get("/admin/news_config/newssearchconfig/")

        assert response.status_code == 200
        assert config.name.encode() in response.content
        assert user.username.encode() in response.content

    def test_config_admin_change_form(self, admin_client):
        """Test admin change form for configuration"""
        user = UserFactory()
        config = NewsSearchConfigFactory(user=user)

        response = admin_client.get(
            f"/admin/news_config/newssearchconfig/{config.id}/change/"
        )

        assert response.status_code == 200
        assert config.name.encode() in response.content

    def test_article_admin_changelist(self, admin_client):
        """Test admin changelist view for articles"""
        config = NewsSearchConfigFactory()
        article = NewsArticleFactory(search_config=config, title="Admin Test Article")

        response = admin_client.get("/admin/news_config/newsarticle/")

        assert response.status_code == 200
        assert article.title.encode() in response.content
        assert article.source_name.encode() in response.content

    def test_article_admin_change_form(self, admin_client):
        """Test admin change form for article"""
        config = NewsSearchConfigFactory()
        article = NewsArticleFactory(search_config=config)

        response = admin_client.get(
            f"/admin/news_config/newsarticle/{article.id}/change/"
        )

        assert response.status_code == 200
        assert article.title.encode() in response.content

    def test_admin_filtering(self, admin_client):
        """Test admin list filtering functionality"""
        user = UserFactory()
        active_config = NewsSearchConfigFactory(user=user, is_active=True, country="us")
        inactive_config = NewsSearchConfigFactory(
            user=user, is_active=False, country="ca"
        )

        # Test filtering by is_active
        response = admin_client.get(
            "/admin/news_config/newssearchconfig/?is_active__exact=1"
        )
        assert response.status_code == 200
        assert active_config.name.encode() in response.content
        assert inactive_config.name.encode() not in response.content

        # Test filtering by country
        response = admin_client.get(
            "/admin/news_config/newssearchconfig/?country__exact=us"
        )
        assert response.status_code == 200
        assert active_config.name.encode() in response.content
        assert inactive_config.name.encode() not in response.content

    def test_admin_search(self, admin_client):
        """Test admin search functionality"""
        user = UserFactory(username="searchuser")
        config = NewsSearchConfigFactory(
            user=user, name="Searchable Config", keywords="searchable keywords"
        )

        # Search by name
        response = admin_client.get("/admin/news_config/newssearchconfig/?q=Searchable")
        assert response.status_code == 200
        assert config.name.encode() in response.content

        # Search by username
        response = admin_client.get("/admin/news_config/newssearchconfig/?q=searchuser")
        assert response.status_code == 200
        assert config.name.encode() in response.content

        # Search by keywords
        response = admin_client.get("/admin/news_config/newssearchconfig/?q=searchable")
        assert response.status_code == 200
        assert config.name.encode() in response.content
