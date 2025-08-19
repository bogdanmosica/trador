// Types for the Strategy API

export interface StrategyParameterSchema {
  type: string;
  minimum?: number;
  maximum?: number;
  default: any;
  description: string;
  enum?: any[];
}

export interface StrategyInfo {
  name: string;
  file_path: string;
  description: string;
  required_indicators: string[];
  parameter_schema: Record<string, StrategyParameterSchema>;
  available_presets: string[];
}

export interface StrategyConfig {
  name: string;
  file_path: string;
  strategy_class: string;
  parameters: Record<string, any>;
  metadata?: Record<string, any>;
}

export interface StrategyDiscoveryResponse {
  strategies: StrategyInfo[];
  configurations: StrategyConfig[];
  total_strategies: number;
  total_configurations: number;
}

export interface StrategyValidationRequest {
  strategy_name: string;
  parameters: Record<string, any>;
}

export interface StrategyValidationResponse {
  is_valid: boolean;
  errors: string[];
}