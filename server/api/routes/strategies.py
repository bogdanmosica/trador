"""
Strategies API Routes

Provides endpoints for discovering, managing, and configuring trading strategies.
Dynamically scans the strategies folder to find available strategies and their
configurations.
"""

import os
import importlib
import importlib.util
import inspect
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

# Import base strategy for type checking
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "..", "strategy"))
from base_strategy import BaseStrategy


# Pydantic models for API responses
class StrategyInfo(BaseModel):
    """Information about a discovered strategy."""
    name: str = Field(..., description="Strategy class name")
    file_path: str = Field(..., description="Path to strategy file")
    description: str = Field(..., description="Strategy description")
    required_indicators: List[str] = Field(..., description="Required technical indicators")
    parameter_schema: Dict[str, Any] = Field(..., description="Parameter configuration schema")
    available_presets: List[str] = Field(..., description="Available parameter presets")


class StrategyConfig(BaseModel):
    """Strategy configuration from JSON file."""
    name: str = Field(..., description="Configuration name")
    file_path: str = Field(..., description="Path to config file")
    strategy_class: str = Field(..., description="Associated strategy class")
    parameters: Dict[str, Any] = Field(..., description="Strategy parameters")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class StrategyDiscoveryResponse(BaseModel):
    """Response containing discovered strategies and configurations."""
    strategies: List[StrategyInfo] = Field(..., description="Available strategy classes")
    configurations: List[StrategyConfig] = Field(..., description="Available configurations")
    total_strategies: int = Field(..., description="Total number of strategies found")
    total_configurations: int = Field(..., description="Total number of configurations found")


class StrategyValidationRequest(BaseModel):
    """Request to validate strategy parameters."""
    strategy_name: str = Field(..., description="Strategy class name")
    parameters: Dict[str, Any] = Field(..., description="Parameters to validate")


class StrategyValidationResponse(BaseModel):
    """Response from parameter validation."""
    is_valid: bool = Field(..., description="Whether parameters are valid")
    errors: List[str] = Field(default_factory=list, description="Validation error messages")


# Create API router
router = APIRouter()

# Set up logging
logger = logging.getLogger(__name__)


class StrategyDiscoveryService:
    """Service for discovering and managing trading strategies."""
    
    def __init__(self):
        """Initialize the strategy discovery service."""
        self.strategy_path = self._get_strategy_path()
        self.config_path = self._get_config_path()
        self._strategy_cache = {}
        self._last_scan_time = 0
    
    def _get_strategy_path(self) -> Path:
        """Get the path to the strategies directory."""
        current_dir = Path(__file__).parent
        strategy_dir = current_dir / ".." / ".." / ".." / "strategy" / "strategies"
        return strategy_dir.resolve()
    
    def _get_config_path(self) -> Path:
        """Get the path to the strategy configs directory."""
        current_dir = Path(__file__).parent
        config_dir = current_dir / ".." / ".." / ".." / "strategy" / "configs"
        return config_dir.resolve()
    
    def discover_strategies(self, force_rescan: bool = False) -> StrategyDiscoveryResponse:
        """
        Discover all available strategies and configurations.
        
        Args:
            force_rescan (bool): Force rescan even if cache is recent
            
        Returns:
            StrategyDiscoveryResponse: Discovered strategies and configurations
        """
        try:
            current_time = os.path.getmtime(self.strategy_path) if self.strategy_path.exists() else 0
            
            # Use cache if recent scan and no force rescan
            if not force_rescan and current_time <= self._last_scan_time and self._strategy_cache:
                return self._strategy_cache.get('discovery_response')
            
            strategies = self._scan_strategies()
            configurations = self._scan_configurations()
            
            response = StrategyDiscoveryResponse(
                strategies=strategies,
                configurations=configurations,
                total_strategies=len(strategies),
                total_configurations=len(configurations)
            )
            
            # Cache the results
            self._strategy_cache['discovery_response'] = response
            self._last_scan_time = current_time
            
            logger.info(f"Discovered {len(strategies)} strategies and {len(configurations)} configurations")
            return response
            
        except Exception as e:
            logger.error(f"Error discovering strategies: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to discover strategies: {str(e)}"
            )
    
    def _scan_strategies(self) -> List[StrategyInfo]:
        """Scan the strategies directory for strategy classes."""
        strategies = []
        
        if not self.strategy_path.exists():
            logger.warning(f"Strategies directory not found: {self.strategy_path}")
            return strategies
        
        # Scan Python files in strategies directory
        for py_file in self.strategy_path.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
                
            try:
                strategy_info = self._extract_strategy_info(py_file)
                if strategy_info:
                    strategies.extend(strategy_info)
            except Exception as e:
                logger.warning(f"Error processing {py_file}: {str(e)}")
                continue
        
        return strategies
    
    def _extract_strategy_info(self, py_file: Path) -> List[StrategyInfo]:
        """Extract strategy information from a Python file."""
        strategies = []
        
        try:
            # Dynamically import the module
            module_name = py_file.stem
            spec = importlib.util.spec_from_file_location(module_name, py_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find strategy classes
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (obj != BaseStrategy and 
                    issubclass(obj, BaseStrategy) and 
                    obj.__module__ == module.__name__):
                    
                    # Create a temporary instance to get metadata
                    try:
                        instance = obj(f"temp_{name.lower()}")
                        
                        # Extract available presets
                        presets = self._extract_presets(instance)
                        
                        strategy_info = StrategyInfo(
                            name=name,
                            file_path=str(py_file.relative_to(self.strategy_path.parent.parent)),
                            description=self._extract_description(obj),
                            required_indicators=instance.get_required_indicators(),
                            parameter_schema=instance.get_parameter_schema(),
                            available_presets=presets
                        )
                        
                        strategies.append(strategy_info)
                        logger.debug(f"Found strategy: {name} in {py_file.name}")
                        
                    except Exception as e:
                        logger.warning(f"Error instantiating strategy {name}: {str(e)}")
                        continue
            
        except Exception as e:
            logger.error(f"Error importing module {py_file}: {str(e)}")
            raise
        
        return strategies
    
    def _extract_description(self, strategy_class) -> str:
        """Extract description from strategy class docstring."""
        docstring = inspect.getdoc(strategy_class)
        if docstring:
            # Get first line/paragraph as description
            lines = docstring.strip().split('\n')
            return lines[0].strip()
        return f"Trading strategy: {strategy_class.__name__}"
    
    def _extract_presets(self, strategy_instance) -> List[str]:
        """Extract available parameter presets from strategy."""
        presets = []
        
        # Try to get presets by calling update_parameters with known preset names
        common_presets = ['conservative', 'aggressive', 'balanced']
        
        for preset in common_presets:
            try:
                # Save current parameters
                original_params = strategy_instance.parameters.copy()
                
                # Try to update with preset
                if hasattr(strategy_instance, 'update_parameters') and strategy_instance.update_parameters(preset):
                    presets.append(preset)
                
                # Restore original parameters
                strategy_instance.parameters = original_params
                
            except Exception as e:
                # Log but continue - this is expected for some strategies
                logger.debug(f"Preset {preset} not available for {strategy_instance.__class__.__name__}: {str(e)}")
                continue
        
        return presets
    
    def _scan_configurations(self) -> List[StrategyConfig]:
        """Scan the configs directory for YAML configuration files."""
        configurations = []
        
        if not self.config_path.exists():
            logger.warning(f"Configs directory not found: {self.config_path}")
            return configurations
        
        # Scan JSON files in configs directory
        for json_file in self.config_path.glob("*.json"):
            try:
                config_info = self._parse_config_file(json_file)
                if config_info:
                    configurations.append(config_info)
            except Exception as e:
                logger.warning(f"Error processing config {json_file}: {str(e)}")
                continue
        
        return configurations
    
    def _parse_config_file(self, json_file: Path) -> Optional[StrategyConfig]:
        """Parse a JSON configuration file."""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            if not config_data or 'strategy' not in config_data:
                logger.warning(f"Invalid config format in {json_file}")
                return None
            
            strategy_info = config_data['strategy']
            
            config = StrategyConfig(
                name=strategy_info.get('name', json_file.stem),
                file_path=str(json_file.relative_to(self.config_path.parent.parent)),
                strategy_class=strategy_info.get('class', ''),
                parameters=config_data.get('parameters', {}),
                metadata=config_data.get('metadata', {})
            )
            
            logger.debug(f"Found config: {config.name} in {json_file.name}")
            return config
            
        except Exception as e:
            logger.error(f"Error parsing config file {json_file}: {str(e)}")
            return None
    
    def validate_strategy_parameters(self, strategy_name: str, parameters: Dict[str, Any]) -> StrategyValidationResponse:
        """
        Validate parameters for a specific strategy.
        
        Args:
            strategy_name (str): Name of the strategy class
            parameters (Dict[str, Any]): Parameters to validate
            
        Returns:
            StrategyValidationResponse: Validation results
        """
        try:
            # Find and instantiate the strategy
            strategy_instance = self._get_strategy_instance(strategy_name)
            
            if not strategy_instance:
                return StrategyValidationResponse(
                    is_valid=False,
                    errors=[f"Strategy '{strategy_name}' not found"]
                )
            
            # Validate parameters
            is_valid = strategy_instance.validate_parameters(parameters)
            
            errors = []
            if not is_valid:
                errors.append("Parameter validation failed. Check parameter ranges and required fields.")
            
            return StrategyValidationResponse(
                is_valid=is_valid,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Error validating parameters for {strategy_name}: {str(e)}")
            return StrategyValidationResponse(
                is_valid=False,
                errors=[f"Validation error: {str(e)}"]
            )
    
    def _get_strategy_instance(self, strategy_name: str):
        """Get an instance of the specified strategy."""
        # Scan strategies to find the class
        strategies = self._scan_strategies()
        
        for strategy_info in strategies:
            if strategy_info.name == strategy_name:
                # Load the module and instantiate the class
                py_file = Path(self.strategy_path.parent.parent) / strategy_info.file_path
                
                module_name = py_file.stem
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                strategy_class = getattr(module, strategy_name)
                return strategy_class(f"validation_{strategy_name.lower()}")
        
        return None


# Initialize the service
strategy_service = StrategyDiscoveryService()


# API Endpoints
@router.get("/strategies", response_model=StrategyDiscoveryResponse)
async def get_strategies(
    force_rescan: bool = Query(False, description="Force rescan of strategies directory")
):
    """
    Discover and return all available trading strategies and configurations.
    
    This endpoint scans the strategies directory to find strategy classes and
    configuration files, returning comprehensive information about each.
    """
    return strategy_service.discover_strategies(force_rescan=force_rescan)


@router.get("/strategies/{strategy_name}", response_model=StrategyInfo)
async def get_strategy_details(strategy_name: str):
    """
    Get detailed information about a specific strategy.
    
    Args:
        strategy_name (str): Name of the strategy class
    """
    discovery_response = strategy_service.discover_strategies()
    
    for strategy in discovery_response.strategies:
        if strategy.name == strategy_name:
            return strategy
    
    raise HTTPException(
        status_code=404,
        detail=f"Strategy '{strategy_name}' not found"
    )


@router.get("/strategies/{strategy_name}/schema", response_model=Dict[str, Any])
async def get_strategy_schema(strategy_name: str):
    """
    Get the parameter schema for a specific strategy.
    
    Args:
        strategy_name (str): Name of the strategy class
    """
    discovery_response = strategy_service.discover_strategies()
    
    for strategy in discovery_response.strategies:
        if strategy.name == strategy_name:
            return strategy.parameter_schema
    
    raise HTTPException(
        status_code=404,
        detail=f"Strategy '{strategy_name}' not found"
    )


@router.get("/configurations", response_model=List[StrategyConfig])
async def get_configurations(
    strategy_class: Optional[str] = Query(None, description="Filter by strategy class (e.g., SmaCrossoverStrategy, sma_crossover)")
):
    """
    Get all available strategy configurations.
    
    Args:
        strategy_class (str, optional): Filter configurations by strategy class
    """
    discovery_response = strategy_service.discover_strategies()
    configurations = discovery_response.configurations
    
    if strategy_class:
        def norm(s: str) -> str:
            import re
            return re.sub(r"[^a-z0-9]", "", s.lower()) if s else ""

        target = norm(strategy_class)
        # Accept multiple forms: full class, without 'strategy', snake-case names
        def matches(cfg: StrategyConfig) -> bool:
            cls = cfg.strategy_class or ""
            n_cls = norm(cls)
            n_cls_trim = n_cls.replace("strategy", "")
            n_name = norm(cfg.name)
            return target in {n_cls, n_cls_trim, n_name}

        filtered = [cfg for cfg in configurations if matches(cfg)]
        configurations = filtered
    
    return configurations


@router.get("/configurations/{config_name}", response_model=StrategyConfig)
async def get_configuration_details(config_name: str):
    """
    Get detailed information about a specific configuration.
    
    Args:
        config_name (str): Name of the configuration
    """
    discovery_response = strategy_service.discover_strategies()
    
    for config in discovery_response.configurations:
        if config.name == config_name:
            return config
    
    raise HTTPException(
        status_code=404,
        detail=f"Configuration '{config_name}' not found"
    )


@router.post("/strategies/{strategy_name}/validate", response_model=StrategyValidationResponse)
async def validate_strategy_parameters(
    strategy_name: str,
    request: StrategyValidationRequest
):
    """
    Validate parameters for a specific strategy.
    
    Args:
        strategy_name (str): Name of the strategy class
        request: Validation request containing parameters
    """
    if request.strategy_name != strategy_name:
        raise HTTPException(
            status_code=400,
            detail="Strategy name in URL must match strategy name in request body"
        )
    
    return strategy_service.validate_strategy_parameters(
        strategy_name,
        request.parameters
    )


@router.post("/strategies/rescan")
async def rescan_strategies():
    """
    Force a rescan of the strategies directory.
    
    Useful after adding new strategy files or configurations.
    """
    try:
        discovery_response = strategy_service.discover_strategies(force_rescan=True)
        return {
            "message": "Strategies rescanned successfully",
            "total_strategies": discovery_response.total_strategies,
            "total_configurations": discovery_response.total_configurations
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to rescan strategies: {str(e)}"
        )
