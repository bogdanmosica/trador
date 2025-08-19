// This component provides a modal for creating new trading bots.
import React, { useState, useEffect } from 'react';
import { fetchStrategies, fetchConfigurations } from '../lib/api';
import { StrategyInfo, StrategyConfig } from '../types/strategies';

interface CreateBotModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (botData: any) => void;
}

const CreateBotModal: React.FC<CreateBotModalProps> = ({ isOpen, onClose, onSubmit }) => {
  const [formData, setFormData] = useState({
    id: '',
    strategy: '',
    configuration: '',
    symbol: 'BTCUSDT',
    mode: 'paper',
    initial_balance: 10000,
    parameters: {} as Record<string, any>
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [strategies, setStrategies] = useState<StrategyInfo[]>([]);
  const [configurations, setConfigurations] = useState<StrategyConfig[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<StrategyInfo | null>(null);
  const [loading, setLoading] = useState(false);

  // Load strategies when modal opens
  useEffect(() => {
    if (isOpen) {
      loadStrategies();
    }
  }, [isOpen]);

  // Load configurations when strategy changes
  useEffect(() => {
    if (formData.strategy) {
      loadConfigurations(formData.strategy);
    }
  }, [formData.strategy]);

  // Update selected strategy info when strategy changes
  useEffect(() => {
    const strategy = strategies.find(s => s.name === formData.strategy);
    setSelectedStrategy(strategy || null);
    // Reset parameters when strategy changes
    if (strategy) {
      setFormData(prev => ({ ...prev, parameters: {} }));
    }
  }, [formData.strategy, strategies]);

  const loadStrategies = async () => {
    try {
      setLoading(true);
      const response = await fetchStrategies();
      setStrategies(response.strategies);
      // Set first strategy as default if none selected
      if (!formData.strategy && response.strategies.length > 0) {
        setFormData(prev => ({ ...prev, strategy: response.strategies[0].name }));
      }
    } catch (error) {
      console.error('Failed to load strategies:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadConfigurations = async (strategyName: string) => {
    try {
      const strategy = strategies.find(s => s.name === strategyName);
      if (strategy) {
        const configs = await fetchConfigurations(strategy.name);
        setConfigurations(configs);
      }
    } catch (error) {
      console.error('Failed to load configurations:', error);
      setConfigurations([]);
    }
  };

  const handleConfigurationChange = (configName: string) => {
    const config = configurations.find(c => c.name === configName);
    if (config) {
      setFormData(prev => ({
        ...prev,
        configuration: configName,
        parameters: { ...config.parameters },
        symbol: config.parameters.symbol || prev.symbol
      }));
    }
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.id.trim()) {
      newErrors.id = 'Bot ID is required';
    } else if (!/^[a-zA-Z0-9_-]+$/.test(formData.id)) {
      newErrors.id = 'Bot ID can only contain letters, numbers, hyphens, and underscores';
    }

    if (!formData.strategy) {
      newErrors.strategy = 'Strategy is required';
    }

    if (formData.initial_balance <= 0) {
      newErrors.initial_balance = 'Initial balance must be greater than 0';
    }

    // Validate parameters based on strategy schema
    if (selectedStrategy) {
      Object.entries(selectedStrategy.parameter_schema).forEach(([key, schema]) => {
        const value = formData.parameters[key];
        
        if (schema.minimum !== undefined && value < schema.minimum) {
          newErrors[`param_${key}`] = `${key} must be at least ${schema.minimum}`;
        }
        
        if (schema.maximum !== undefined && value > schema.maximum) {
          newErrors[`param_${key}`] = `${key} must be at most ${schema.maximum}`;
        }
        
        if (value === undefined || value === '') {
          newErrors[`param_${key}`] = `${key} is required`;
        }
      });
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (validateForm()) {
      const botData = {
        id: formData.id,
        strategy: formData.strategy,
        symbol: formData.symbol,
        mode: formData.mode,
        initial_balance: formData.initial_balance,
        parameters: formData.parameters
      };
      
      onSubmit(botData);
    }
  };

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const handleParameterChange = (paramKey: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      parameters: { ...prev.parameters, [paramKey]: value }
    }));
    // Clear error when user starts typing
    const errorKey = `param_${paramKey}`;
    if (errors[errorKey]) {
      setErrors(prev => ({ ...prev, [errorKey]: '' }));
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-gray-900 flex items-center">
              <span className="mr-2">🤖</span>
              Create New Trading Bot
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
            >
              ×
            </button>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Bot ID */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Bot ID *
            </label>
            <input
              type="text"
              value={formData.id}
              onChange={(e) => handleInputChange('id', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="e.g., my_sma_bot_001"
            />
            {errors.id && <p className="text-red-500 text-xs mt-1">{errors.id}</p>}
          </div>

          {/* Strategy */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Strategy *
            </label>
            <select
              value={formData.strategy}
              onChange={(e) => handleInputChange('strategy', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            >
              <option value="">Select a strategy...</option>
              {strategies.map((strategy) => (
                <option key={strategy.name} value={strategy.name}>
                  {strategy.name}
                </option>
              ))}
            </select>
            {errors.strategy && <p className="text-red-500 text-xs mt-1">{errors.strategy}</p>}
          </div>

          {/* Configuration */}
          {formData.strategy && configurations.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Configuration (Optional)
              </label>
              <select
                value={formData.configuration}
                onChange={(e) => handleConfigurationChange(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Use default values...</option>
                {configurations.map((config) => (
                  <option key={config.name} value={config.name}>
                    {config.name} ({config.metadata?.risk_profile || 'N/A'})
                  </option>
                ))}
              </select>
              {formData.configuration && (
                <p className="text-xs text-gray-600 mt-1">
                  Selected: {configurations.find(c => c.name === formData.configuration)?.metadata?.description || formData.configuration}
                </p>
              )}
            </div>
          )}

          {/* Symbol */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Trading Pair
            </label>
            <select
              value={formData.symbol}
              onChange={(e) => handleInputChange('symbol', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="BTCUSDT">BTC/USDT</option>
              <option value="ETHUSDT">ETH/USDT</option>
              <option value="BNBUSDT">BNB/USDT</option>
              <option value="ADAUSDT">ADA/USDT</option>
              <option value="DOTUSDT">DOT/USDT</option>
              <option value="LINKUSDT">LINK/USDT</option>
            </select>
          </div>

          {/* Mode */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Trading Mode
            </label>
            <select
              value={formData.mode}
              onChange={(e) => handleInputChange('mode', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="paper">Paper Trading (Demo)</option>
              <option value="simulated">Simulated Trading</option>
              <option value="live">Live Trading</option>
            </select>
          </div>

          {/* Initial Balance */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Initial Balance ($)
            </label>
            <input
              type="number"
              value={formData.initial_balance}
              onChange={(e) => handleInputChange('initial_balance', Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              min="1"
              step="100"
            />
            {errors.initial_balance && <p className="text-red-500 text-xs mt-1">{errors.initial_balance}</p>}
          </div>

          {/* Strategy Parameters */}
          {selectedStrategy && Object.keys(selectedStrategy.parameter_schema).length > 0 && (
            <div className="border-t border-gray-200 pt-4">
              <h3 className="text-sm font-medium text-gray-700 mb-3">
                Strategy Parameters
                {formData.configuration && (
                  <span className="text-xs text-green-600 ml-2">
                    (Values from {formData.configuration})
                  </span>
                )}
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(selectedStrategy.parameter_schema).map(([key, schema]) => {
                  const value = formData.parameters[key];
                  const errorKey = `param_${key}`;
                  
                  return (
                    <div key={key}>
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        {schema.description && (
                          <span className="text-gray-400 font-normal ml-1">
                            ({schema.description})
                          </span>
                        )}
                      </label>
                      
                      {schema.enum ? (
                        // Render select dropdown for enum values
                        <select
                          value={value || ''}
                          onChange={(e) => handleParameterChange(key, e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="">Select {key}...</option>
                          {schema.enum.map((option: any) => (
                            <option key={option} value={option}>
                              {option}
                            </option>
                          ))}
                        </select>
                      ) : schema.type === 'boolean' ? (
                        // Render checkbox for boolean values
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={value || false}
                            onChange={(e) => handleParameterChange(key, e.target.checked)}
                            className="mr-2"
                          />
                          <span className="text-sm">Enable {key.replace(/_/g, ' ')}</span>
                        </label>
                      ) : (
                        // Render input for other types
                        <input
                          type={schema.type === 'integer' || schema.type === 'number' ? 'number' : 'text'}
                          value={value || ''}
                          onChange={(e) => {
                            const inputValue = schema.type === 'integer' || schema.type === 'number'
                              ? Number(e.target.value)
                              : e.target.value;
                            handleParameterChange(key, inputValue);
                          }}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                          min={schema.minimum}
                          max={schema.maximum}
                          step={schema.type === 'integer' ? '1' : 'any'}
                          placeholder={schema.default ? `Default: ${schema.default}` : ''}
                        />
                      )}
                      
                      {errors[errorKey] && (
                        <p className="text-red-500 text-xs mt-1">{errors[errorKey]}</p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Buttons */}
          <div className="flex space-x-4 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Create Bot
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateBotModal;