"""
Configuration Manager for Strategy Parameters

Handles loading, saving, and versioning of strategy parameter configurations
using JSON files with metadata support.
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class StrategyConfig:
    """
    Strategy configuration with metadata.
    
    Represents a complete strategy configuration including parameters
    and versioning metadata.
    """
    name: str
    base_strategy: str
    params: Dict[str, Any]
    status: str = "draft"  # draft, backtest, live, archived
    created_at: Optional[str] = None
    notes: str = ""
    version: Optional[str] = None
    
    def __post_init__(self):
        """Set default values after initialization."""
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


class ConfigManager:
    """
    Manages strategy configuration files and versioning.
    
    Provides functionality to load, save, and manage different versions
    of strategy configurations using JSON files.
    """
    
    def __init__(self, config_dir: str = "strategy/configs"):
        """
        Initialize the configuration manager.
        
        Args:
            config_dir (str): Directory path where config files are stored
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def save_config(self, config: StrategyConfig) -> bool:
        """
        Save a strategy configuration to a JSON file.
        
        Args:
            config (StrategyConfig): Configuration to save
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            file_path = self.config_dir / f"{config.name}.json"
            
            # Convert config to dictionary for JSON serialization
            config_dict = {
                "strategy": {
                    "name": config.name,
                    "class": config.base_strategy,
                    "description": f"Configuration for {config.base_strategy}"
                },
                "parameters": config.params,
                "metadata": {
                    "status": config.status,
                    "created_at": config.created_at,
                    "notes": config.notes,
                    "version": config.version
                }
            }
            
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(config_dict, file, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error saving config {config.name}: {e}")
            return False
    
    def load_config(self, config_name: str) -> Optional[StrategyConfig]:
        """
        Load a strategy configuration from a JSON file.
        
        Args:
            config_name (str): Name of the configuration to load
            
        Returns:
            Optional[StrategyConfig]: Loaded configuration or None if not found
        """
        try:
            file_path = self.config_dir / f"{config_name}.json"
            
            if not file_path.exists():
                print(f"Config file not found: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as file:
                config_dict = json.load(file)
            
            # Extract strategy info and metadata
            strategy_info = config_dict.get("strategy", {})
            metadata = config_dict.get("metadata", {})
            
            return StrategyConfig(
                name=strategy_info.get("name", config_name),
                base_strategy=strategy_info.get("class", ""),
                params=config_dict.get("parameters", {}),
                status=metadata.get("status", "draft"),
                created_at=metadata.get("created_at"),
                notes=metadata.get("notes", ""),
                version=metadata.get("version")
            )
            
        except Exception as e:
            print(f"Error loading config {config_name}: {e}")
            return None
    
    def list_configs(self, base_strategy: Optional[str] = None) -> List[str]:
        """
        List all available configuration names.
        
        Args:
            base_strategy (Optional[str]): Filter by base strategy type
            
        Returns:
            List[str]: List of configuration names
        """
        config_files = list(self.config_dir.glob("*.json"))
        config_names = []
        
        for file_path in config_files:
            if base_strategy:
                # Load config to check base_strategy
                config = self.load_config(file_path.stem)
                if config and config.base_strategy == base_strategy:
                    config_names.append(file_path.stem)
            else:
                config_names.append(file_path.stem)
        
        return sorted(config_names)
    
    def get_config_metadata(self, config_name: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a configuration without loading full config.
        
        Args:
            config_name (str): Name of the configuration
            
        Returns:
            Optional[Dict[str, Any]]: Metadata dictionary or None
        """
        config = self.load_config(config_name)
        if config:
            return {
                "status": config.status,
                "created_at": config.created_at,
                "notes": config.notes,
                "version": config.version,
                "base_strategy": config.base_strategy
            }
        return None
    
    def delete_config(self, config_name: str) -> bool:
        """
        Delete a configuration file.
        
        Args:
            config_name (str): Name of the configuration to delete
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            file_path = self.config_dir / f"{config_name}.json"
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error deleting config {config_name}: {e}")
            return False
    
    def create_version(self, base_config_name: str, new_version_name: str, 
                      status: str = "draft", notes: str = "") -> bool:
        """
        Create a new version of an existing configuration.
        
        Args:
            base_config_name (str): Name of the base configuration
            new_version_name (str): Name for the new version
            status (str): Status of the new version
            notes (str): Notes for the new version
            
        Returns:
            bool: True if version created successfully, False otherwise
        """
        base_config = self.load_config(base_config_name)
        if not base_config:
            return False
        
        # Create new version with updated metadata
        new_config = StrategyConfig(
            name=new_version_name,
            base_strategy=base_config.base_strategy,
            params=base_config.params.copy(),
            status=status,
            notes=notes,
            version=new_version_name
        )
        
        return self.save_config(new_config)
    
    def export_config_json(self, config_name: str, output_path: str) -> bool:
        """
        Export configuration to JSON format.
        
        Args:
            config_name (str): Name of the configuration to export
            output_path (str): Path for the JSON output file
            
        Returns:
            bool: True if exported successfully, False otherwise
        """
        config = self.load_config(config_name)
        if not config:
            return False
        
        try:
            config_dict = asdict(config)
            with open(output_path, 'w', encoding='utf-8') as file:
                json.dump(config_dict, file, indent=2, default=str)
            return True
        except Exception as e:
            print(f"Error exporting config to JSON: {e}")
            return False