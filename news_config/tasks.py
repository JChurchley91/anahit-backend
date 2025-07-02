import logging
import requests
from datetime import datetime, timezone
from celery import shared_task
from django.conf import settings
from django.utils import timezone as django_timezone

from .models import NewsSearchConfig, NewsArticle

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def fetch_news_for_config(self, config_id: int, news_api_key: str = None):
    """
    Fetch news articles for a specific configuration using NewsAPI.
    
    Args:
        config_id: ID of the NewsSearchConfig to process
        news_api_key: NewsAPI key (optional, can be passed or use env var)
    
    Returns:
        dict: Results summary with counts and status
    """
    try:
        # Get the configuration
        try:
            config = NewsSearchConfig.objects.get(id=config_id, is_active=True)
        except NewsSearchConfig.DoesNotExist:
            logger.error(f"Configuration {config_id} not found or inactive")
            return {"error": "Configuration not found or inactive"}
        
        # Use provided API key or get from environment
        api_key = news_api_key or getattr(settings, 'NEWS_API_KEY', None)
        if not api_key:
            logger.error("No NewsAPI key provided")
            return {"error": "No NewsAPI key configured"}
        
        # Build NewsAPI request parameters
        params = config.get_newsapi_params()
        params['apiKey'] = api_key
        params['pageSize'] = 100  # Max articles per request
        
        # Make request to NewsAPI
        logger.info(f"Fetching news for config {config_id}: {config.name}")
        response = requests.get(
            'https://newsapi.org/v2/top-headlines',
            params=params,
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') != 'ok':
            error_msg = data.get('message', 'Unknown NewsAPI error')
            logger.error(f"NewsAPI error for config {config_id}: {error_msg}")
            return {"error": f"NewsAPI error: {error_msg}"}
        
        # Process articles
        articles = data.get('articles', [])
        created_count = 0
        duplicate_count = 0
        
        for article_data in articles:
            try:
                article, created = NewsArticle.create_from_newsapi(article_data, config)
                if created:
                    created_count += 1
                    logger.debug(f"Created article: {article.title}")
                else:
                    duplicate_count += 1
                    logger.debug(f"Duplicate article: {article.title}")
                    
            except Exception as e:
                logger.error(f"Error creating article: {e}")
                continue
        
        # Update last executed timestamp
        config.last_executed = django_timezone.now()
        config.save(update_fields=['last_executed'])
        
        result = {
            "config_id": config_id,
            "config_name": config.name,
            "total_articles": len(articles),
            "created_count": created_count,
            "duplicate_count": duplicate_count,
            "status": "success"
        }
        
        logger.info(f"Completed news fetch for config {config_id}: {result}")
        return result
        
    except requests.RequestException as e:
        logger.error(f"Network error fetching news for config {config_id}: {e}")
        # Retry on network errors
        raise self.retry(countdown=60 * (self.request.retries + 1), exc=e)
        
    except Exception as e:
        logger.error(f"Unexpected error fetching news for config {config_id}: {e}")
        return {"error": f"Unexpected error: {str(e)}"}


@shared_task(bind=True)
def fetch_news_for_all_active_configs(self, news_api_key: str = None):
    """
    Fetch news for all active configurations.
    
    Args:
        news_api_key: NewsAPI key (optional)
    
    Returns:
        dict: Summary of all fetch operations
    """
    try:
        # Get all active configurations
        active_configs = NewsSearchConfig.objects.filter(is_active=True)
        
        if not active_configs.exists():
            logger.info("No active configurations found")
            return {"message": "No active configurations", "configs_processed": 0}
        
        logger.info(f"Processing {active_configs.count()} active configurations")
        
        results = []
        total_created = 0
        total_duplicates = 0
        
        for config in active_configs:
            # Schedule individual fetch task for each config
            result = fetch_news_for_config.delay(config.id, news_api_key)
            
            # Note: In a real implementation, you might want to:
            # 1. Add rate limiting between API calls
            # 2. Process configs in smaller batches
            # 3. Handle API rate limits more gracefully
            
            logger.info(f"Scheduled news fetch for config {config.id}: {config.name}")
            results.append({
                "config_id": config.id,
                "config_name": config.name,
                "task_id": result.id,
                "status": "scheduled"
            })
        
        return {
            "message": f"Scheduled news fetch for {len(results)} configurations",
            "configs_processed": len(results),
            "scheduled_tasks": results,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error scheduling news fetch for all configs: {e}")
        return {"error": f"Error scheduling tasks: {str(e)}"}


@shared_task(bind=True)
def cleanup_old_articles(self, days_to_keep: int = 30):
    """
    Clean up old news articles to prevent database bloat.
    
    Args:
        days_to_keep: Number of days of articles to keep (default: 30)
    
    Returns:
        dict: Cleanup results
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        
        # Find old articles
        old_articles = NewsArticle.objects.filter(
            created_at__lt=cutoff_date
        )
        
        count = old_articles.count()
        
        if count > 0:
            # Delete old articles
            old_articles.delete()
            logger.info(f"Deleted {count} articles older than {days_to_keep} days")
            
            return {
                "deleted_count": count,
                "cutoff_date": cutoff_date.isoformat(),
                "status": "success"
            }
        else:
            logger.info(f"No articles older than {days_to_keep} days found")
            return {
                "deleted_count": 0,
                "cutoff_date": cutoff_date.isoformat(),
                "status": "success"
            }
            
    except Exception as e:
        logger.error(f"Error cleaning up old articles: {e}")
        return {"error": f"Cleanup error: {str(e)}"}