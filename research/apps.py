import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)

class ResearchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'research'

    def ready(self):
        """
        Initialize the Vector Store on startup.
        This prevents the first user request from being blocked by index loading.
        """
        try:
            # Import inside ready() to avoid AppRegistryNotReady errors
            from .services import VectorStoreService
            # Preload the index
            VectorStoreService.get_index()
            logger.info("Research app ready: Vector Store loaded.")
        except Exception as e:
            logger.warning(f"Failed to preload Vector Store: {e}")
