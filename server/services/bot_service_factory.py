"""
Bot Service Factory

This module provides a factory to create the appropriate bot service
based on available dependencies.
"""

import logging
import sys
import os
from typing import Any

# Add the project root to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logger = logging.getLogger(__name__)


class BotServiceFactory:
    """Factory for creating bot service instances."""
    
    @staticmethod
    def create_bot_service():
        """
        Create a bot service instance.
        
        Returns:
            Bot service instance (integrated, simple, or mock)
        """
        try:
            # Try the simple bot service first (no complex dependencies)
            from server.services.simple_bot_service import SimpleBotService
            logger.info("Using SimpleBotService with real trading simulation")
            return SimpleBotService()
            
        except ImportError as e:
            logger.warning(f"Could not load SimpleBotService: {e}")
            
            try:
                # Try to import and use the integrated service
                from server.services.integrated_bot_service import IntegratedBotService
                logger.info("Using IntegratedBotService with real bot modules")
                return IntegratedBotService()
                
            except ImportError as e2:
                logger.warning(f"Could not load IntegratedBotService: {e2}")
                logger.info("Falling back to mock BotService")
                
                # Fallback to mock service
                from server.services.mock_bot_service import MockBotService
                return MockBotService()
        
        except Exception as e:
            logger.error(f"Error creating bot service: {e}")
            logger.info("Falling back to mock BotService")
            
            # Final fallback
            from server.services.mock_bot_service import MockBotService
            return MockBotService()


# Global service instance
_bot_service_instance = None


def get_bot_service():
    """Get the global bot service instance."""
    global _bot_service_instance
    if _bot_service_instance is None:
        _bot_service_instance = BotServiceFactory.create_bot_service()
    return _bot_service_instance