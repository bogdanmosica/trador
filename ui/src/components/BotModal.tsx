// Unified modal for creating and editing trading bots with dynamic strategy discovery
import React, { useState, useEffect, useMemo } from 'react';
import { 
  useStrategies, 
  useConfigurations, 
  useStrategyDetails,
  useAvailableSymbols,
  useCreateBot,
  useUpdateBotConfig,
  useBotConfig,
  useRescanStrategies,
} from '@/hooks/useBots';
import { StrategyInfo, StrategyConfig } from '@/types/strategies';

interface BotModalProps {
  isOpen: boolean;
  onClose: () => void;
  mode: 'create' | 'edit';
  botId?: string; // Required for edit mode
}

interface FormData {
  id: string;
  strategy: string;
  symbol: string;
  mode: string;
  initial_balance: number;
  parameters: Record<string, any>;
  configuration?: string; // Selected configuration preset
}

interface ValidationErrors {
  [key: string]: string;
}

const BotModal: React.FC<BotModalProps> = ({ isOpen, onClose, mode, botId }) => {
  // API hooks
  const { data: strategiesData, isLoading: strategiesLoading } = useStrategies();
  const { data: availableSymbols, isLoading: symbolsLoading } = useAvailableSymbols();
  const { data: botConfig, isLoading: botConfigLoading } = useBotConfig(botId || '', mode === 'edit');
  const createBotMutation = useCreateBot();
  const updateBotMutation = useUpdateBotConfig();
  const rescanMutation = useRescanStrategies();
  
  // Form state
  const [formData, setFormData] = useState<FormData>({
    id: '',
    strategy: '',
    symbol: '',
    mode: 'paper',
    initial_balance: 10000,
    parameters: {},
    configuration: ''
  });
  
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [selectedStrategy, setSelectedStrategy] = useState<StrategyInfo | null>(null);
  // Configurations for the selected strategy
  const { data: configurations } = useConfigurations(formData.strategy);
  
  const { data: strategyDetails } = useStrategyDetails(formData.strategy, !!formData.strategy);
  
  const availableConfigs: StrategyConfig[] = useMemo(() => {
    if (configurations && configurations.length > 0) return configurations;
    const all = strategiesData?.configurations || [];
    if (formData.strategy) {
      return all.filter(c => c.strategy_class === formData.strategy);
    }
    return [];
  }, [configurations, strategiesData, formData.strategy]);
  
  // Update selected strategy details
  useEffect(() => {
    if (strategyDetails) {
      setSelectedStrategy(strategyDetails);
    }
  }, [strategyDetails]);

  // When strategy changes (and details load), prefill defaults for create mode
  useEffect(() => {
    if (mode === 'create' && selectedStrategy?.parameter_schema) {
      const defaults: Record<string, any> = Object.fromEntries(
        Object.entries(selectedStrategy.parameter_schema).map(([k, schema]: any) => [
          k,
          schema?.default !== undefined ? schema.default : ''
        ])
      );
      const symbolDefault = (selectedStrategy.parameter_schema as any)?.symbol?.default;
      setFormData(prev => ({ 
        ...prev, 
        parameters: defaults, 
        configuration: '',
        symbol: symbolDefault ?? prev.symbol
      }));
    }
  }, [selectedStrategy, mode]);
  
  // Initialize form data for edit mode
  useEffect(() => {
    if (mode === 'edit' && botConfig && isOpen) {
      setFormData({
        id: botConfig.id,
        strategy: botConfig.strategy,
        symbol: botConfig.symbol,
        mode: botConfig.mode,
        initial_balance: botConfig.initial_balance,
        parameters: { ...botConfig.parameters },
        configuration: ''
      });
    } else if (mode === 'create' && isOpen) {
      // Reset form for create mode
      setFormData({
        id: '',
        strategy: '',
        symbol: '',
        mode: 'paper',
        initial_balance: 10000,
        parameters: {},
        configuration: ''
      });
    }
  }, [mode, botConfig, isOpen]);
  
  // Available strategies for dropdown - only show strategy classes, not configurations
  const availableStrategies = useMemo(() => {
    if (!strategiesData?.strategies) return [];
    return strategiesData.strategies.map(strategy => ({
      value: strategy.name,
      label: strategy.name.replace('Strategy', '').replace(/([A-Z])/g, ' $1').trim(),
      description: strategy.description,
      strategy: strategy
    }));
  }, [strategiesData]);
  
  // Available symbols for dropdown
  const symbolOptions = useMemo(() => {
    if (!availableSymbols) return [];
    return availableSymbols;
  }, [availableSymbols]);
  
  // Handle form field changes
  const handleFieldChange = (field: keyof FormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear related errors
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
    
    // Handle strategy change
    if (field === 'strategy' && value !== formData.strategy) {
      setFormData(prev => ({ 
        ...prev, 
        [field]: value, 
        parameters: {},
        configuration: ''
      }));
    }
  };
  
  // Handle parameter changes
  const handleParameterChange = (paramName: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      parameters: {
        ...prev.parameters,
        [paramName]: value
      }
    }));
    
    // Clear parameter errors
    const errorKey = `parameters.${paramName}`;
    if (errors[errorKey]) {
      setErrors(prev => ({ ...prev, [errorKey]: '' }));
    }
  };
  
  // Handle configuration preset selection
  const handleConfigurationChange = (configName: string) => {
    const config = availableConfigs.find(c => c.name === configName);
    if (config) {
      setFormData(prev => ({
        ...prev,
        configuration: configName,
        parameters: { ...config.parameters },
        // Apply symbol from preset if present
        symbol: (config.parameters as any)?.symbol ?? prev.symbol,
      }));
    } else {
      // Reset to strategy defaults when clearing selection
      if (selectedStrategy?.parameter_schema) {
        const defaults: Record<string, any> = Object.fromEntries(
          Object.entries(selectedStrategy.parameter_schema).map(([k, schema]: any) => [
            k,
            schema?.default !== undefined ? schema.default : ''
          ])
        );
        setFormData(prev => ({ ...prev, configuration: '', parameters: defaults }));
      } else {
        setFormData(prev => ({ ...prev, configuration: '', parameters: {} }));
      }
    }
  };
  
  // Form validation
  const validateForm = (): boolean => {
    const newErrors: ValidationErrors = {};
    
    // Basic field validation
    if (!formData.id.trim() && mode === 'create') {
      newErrors.id = 'Bot ID is required';
    } else if (formData.id && !/^[a-zA-Z0-9_-]+$/.test(formData.id)) {
      newErrors.id = 'Bot ID can only contain letters, numbers, hyphens, and underscores';
    }
    
    if (!formData.strategy) {
      newErrors.strategy = 'Strategy is required';
    }
    
    if (!formData.symbol) {
      newErrors.symbol = 'Trading symbol is required';
    }
    
    if (formData.initial_balance <= 0) {
      newErrors.initial_balance = 'Initial balance must be greater than 0';
    }
    
    // Parameter validation based on schema
    if (selectedStrategy?.parameter_schema) {
      Object.entries(selectedStrategy.parameter_schema).forEach(([paramName, schema]) => {
        const value = formData.parameters[paramName];
        
        // Check required parameters (assuming parameters with defaults are not required)
        if (value === undefined || value === null || value === '') {
          if (!('default' in schema)) {
            newErrors[`parameters.${paramName}`] = `${paramName} is required`;
          }
        }
        
        // Type and range validation
        if (value !== undefined && value !== null && value !== '') {
          if (schema.type === 'number' && isNaN(Number(value))) {
            newErrors[`parameters.${paramName}`] = `${paramName} must be a number`;
          } else if (schema.type === 'integer' && !Number.isInteger(Number(value))) {
            newErrors[`parameters.${paramName}`] = `${paramName} must be an integer`;
          } else if (schema.minimum !== undefined && Number(value) < schema.minimum) {
            newErrors[`parameters.${paramName}`] = `${paramName} must be at least ${schema.minimum}`;
          } else if (schema.maximum !== undefined && Number(value) > schema.maximum) {
            newErrors[`parameters.${paramName}`] = `${paramName} must be at most ${schema.maximum}`;
          }
        }
      });
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    try {
      if (mode === 'create') {
        const botData = {
          id: formData.id,
          strategy: formData.strategy,
          symbol: formData.symbol,
          mode: formData.mode,
          initial_balance: formData.initial_balance,
          parameters: formData.parameters
        };
        
        await createBotMutation.mutateAsync(botData);
      } else {
        const updateData = {
          strategy: formData.strategy,
          symbol: formData.symbol,
          mode: formData.mode,
          initial_balance: formData.initial_balance,
          parameters: formData.parameters
        };
        
        await updateBotMutation.mutateAsync({ 
          botId: botId!, 
          config: updateData 
        });
      }
      
      onClose();
    } catch (error) {
      console.error('Error submitting form:', error);
      // Handle error display
    }
  };
  
  // Render parameter input based on schema
  const renderParameterInput = (paramName: string, schema: any) => {
    const value = formData.parameters[paramName] ?? schema.default ?? '';
    const errorKey = `parameters.${paramName}`;
    
    const inputProps = {
      id: paramName,
      value: value,
      onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        let newValue: any = e.target.value;
        
        // Type conversion
        if (schema.type === 'number' || schema.type === 'integer') {
          newValue = schema.type === 'integer' ? parseInt(newValue) || 0 : parseFloat(newValue) || 0;
        } else if (schema.type === 'boolean') {
          newValue = e.target.type === 'checkbox' ? (e.target as HTMLInputElement).checked : newValue === 'true';
        }
        
        handleParameterChange(paramName, newValue);
      },
      className: `w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm ${
        errors[errorKey] ? 'border-red-500' : ''
      }`
    };
    
    if (schema.enum) {
      return (
        <div key={paramName} className="space-y-1">
          <label className="block text-sm font-medium text-gray-700" htmlFor={paramName}>
            {paramName}
            <span className="text-gray-400 text-xs ml-1">({schema.description})</span>
          </label>
          <select {...inputProps}>
            {schema.enum.map((option: any) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
          {errors[errorKey] && <p className="text-red-500 text-xs mt-1">{errors[errorKey]}</p>}
        </div>
      );
    }
    
    if (schema.type === 'boolean') {
      return (
        <div key={paramName} className="flex items-center justify-between py-2">
          <label className="text-sm font-medium text-gray-700 flex items-center">
            {paramName}
            <span className="text-gray-400 text-xs ml-2">({schema.description})</span>
          </label>
          <input
            type="checkbox"
            checked={value}
            onChange={inputProps.onChange}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          {errors[errorKey] && <p className="text-red-500 text-xs mt-1">{errors[errorKey]}</p>}
        </div>
      );
    }
    
    return (
      <div key={paramName} className="space-y-1">
        <label className="block text-sm font-medium text-gray-700" htmlFor={paramName}>
          {paramName}
          <span className="text-gray-400 text-xs ml-1">({schema.description})</span>
        </label>
        <input
          type={schema.type === 'number' || schema.type === 'integer' ? 'number' : 'text'}
          step={schema.type === 'number' ? 'any' : undefined}
          min={schema.minimum}
          max={schema.maximum}
          {...inputProps}
        />
        {errors[errorKey] && <p className="text-red-500 text-xs mt-1">{errors[errorKey]}</p>}
      </div>
    );
  };
  
  if (!isOpen) return null;
  
  const isLoading = strategiesLoading || symbolsLoading || (mode === 'edit' && botConfigLoading);
  const isSubmitting = createBotMutation.isPending || updateBotMutation.isPending;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-gray-900 flex items-center">
              <span className="mr-2">{mode === 'create' ? '🤖' : '⚙️'}</span>
              {mode === 'create' ? 'Create New Trading Bot' : `Edit Bot Configuration`}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
              disabled={isSubmitting}
            >
              ×
            </button>
          </div>
        </div>
        
        {/* Loading State */}
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2 text-gray-600">Loading...</span>
          </div>
        ) : (
          /* Form */
          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {/* Basic Configuration */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900 border-b border-gray-200 pb-2">
                Basic Configuration
              </h3>
              
              {/* Bot ID (only for create mode) */}
              {mode === 'create' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Bot ID *
                  </label>
                  <input
                    type="text"
                    value={formData.id}
                    onChange={(e) => handleFieldChange('id', e.target.value)}
                    className={`w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      errors.id ? 'border-red-500' : ''
                    }`}
                    placeholder="e.g., my_stat_arb_bot_001"
                  />
                  {errors.id && <p className="text-red-500 text-xs mt-1">{errors.id}</p>}
                </div>
              )}
              
              {/* Strategy */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-sm font-medium text-gray-700">
                    Strategy *
                  </label>
                  <button
                    type="button"
                    onClick={() => rescanMutation.mutate()}
                    className="text-xs px-2 py-1 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                    disabled={rescanMutation.isPending}
                    title="Rescan strategies and presets"
                  >
                    {rescanMutation.isPending ? 'Rescanning…' : 'Rescan'}
                  </button>
                </div>
                <select
                  value={formData.strategy}
                  onChange={(e) => handleFieldChange('strategy', e.target.value)}
                  className={`w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.strategy ? 'border-red-500' : ''
                  }`}
                >
                  <option value="">Select a strategy</option>
                  {availableStrategies.map((strategy) => (
                    <option key={strategy.value} value={strategy.value}>
                      {strategy.label}
                    </option>
                  ))}
                </select>
                {selectedStrategy && (
                  <p className="text-gray-500 text-sm mt-1">{selectedStrategy.description}</p>
                )}
                {errors.strategy && <p className="text-red-500 text-xs mt-1">{errors.strategy}</p>}
              </div>
              
              {/* Category (Configuration Preset) */}
              {formData.strategy && availableConfigs.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Category
                  </label>
                  <select
                    value={formData.configuration}
                    onChange={(e) => handleConfigurationChange(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Use strategy defaults...</option>
                    {(() => {
                      const grouped: Record<string, StrategyConfig[]> = {};
                      availableConfigs.forEach(cfg => {
                        const key = (cfg.metadata?.risk_profile || 'other').toString().toLowerCase();
                        if (!grouped[key]) grouped[key] = [];
                        grouped[key].push(cfg);
                      });
                      const order = ['low', 'balanced', 'medium', 'high', 'aggressive', 'other'];
                      const keys = Object.keys(grouped).sort((a, b) => {
                        const ia = order.indexOf(a);
                        const ib = order.indexOf(b);
                        return (ia === -1 ? 999 : ia) - (ib === -1 ? 999 : ib);
                      });
                      const labelFor = (k: string) => {
                        const map: Record<string, string> = {
                          low: 'Low (Conservative)',
                          balanced: 'Balanced',
                          medium: 'Medium',
                          high: 'High (Aggressive)',
                          aggressive: 'Aggressive',
                          other: 'Other',
                        };
                        return map[k] || (k.charAt(0).toUpperCase() + k.slice(1));
                      };
                      return keys.map(k => (
                        <optgroup key={k} label={labelFor(k)}>
                          {grouped[k]
                            .slice()
                            .sort((a, b) => {
                              const va = (a.metadata?.version || '').toString();
                              const vb = (b.metadata?.version || '').toString();
                              const na = parseInt(va.replace(/\D/g, '')) || 0;
                              const nb = parseInt(vb.replace(/\D/g, '')) || 0;
                              if (na !== nb) return nb - na; // newest first
                              return a.name.localeCompare(b.name);
                            })
                            .map(config => (
                            <option key={config.name} value={config.name}>
                              {config.name}
                              {config.metadata?.version ? ` (${config.metadata.version})` : ''}
                            </option>
                          ))}
                        </optgroup>
                      ));
                    })()}
                  </select>
                  {/* Selected preset details */}
                  {formData.configuration && (() => {
                    const sel = availableConfigs.find(c => c.name === formData.configuration);
                    if (!sel) return null;
                    return (
                      <div className="mt-2 text-xs text-gray-600">
                        <div className="flex items-center justify-between">
                          <span>
                            {sel.metadata?.description || 'Preset selected'}
                          </span>
                          {sel.metadata?.risk_profile && (
                            <span className="ml-2 inline-block px-2 py-0.5 rounded-full bg-gray-100 border border-gray-200 text-gray-700">
                              {String(sel.metadata.risk_profile).toUpperCase()}
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })()}
                </div>
              )}
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Symbol */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Trading Pair *
                  </label>
                  <select
                    value={formData.symbol}
                    onChange={(e) => handleFieldChange('symbol', e.target.value)}
                    className={`w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      errors.symbol ? 'border-red-500' : ''
                    }`}
                  >
                    <option value="">Select trading pair</option>
                    {symbolOptions.map((symbol) => (
                      <option key={symbol.value} value={symbol.value}>
                        {symbol.label}
                      </option>
                    ))}
                  </select>
                  {errors.symbol && <p className="text-red-500 text-xs mt-1">{errors.symbol}</p>}
                </div>
                
                {/* Mode */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Trading Mode
                  </label>
                  <select
                    value={formData.mode}
                    onChange={(e) => handleFieldChange('mode', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="paper">Paper Trading (Demo)</option>
                    <option value="simulated">Simulated Trading</option>
                    <option value="backtest">Backtest</option>
                    <option value="live">Live Trading</option>
                  </select>
                </div>
              </div>
              
              {/* Initial Balance */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Initial Balance ($)
                </label>
                <input
                  type="number"
                  value={formData.initial_balance}
                  onChange={(e) => handleFieldChange('initial_balance', Number(e.target.value))}
                  className={`w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.initial_balance ? 'border-red-500' : ''
                  }`}
                  min="1"
                  step="100"
                />
                {errors.initial_balance && <p className="text-red-500 text-xs mt-1">{errors.initial_balance}</p>}
              </div>
            </div>
            
            {/* Strategy Parameters */}
            {selectedStrategy?.parameter_schema && Object.keys(selectedStrategy.parameter_schema).length > 0 && (
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-gray-900 border-b border-gray-200 pb-2">
                  Strategy Parameters
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(selectedStrategy.parameter_schema).map(([paramName, schema]) =>
                    renderParameterInput(paramName, schema)
                  )}
                </div>
              </div>
            )}
            
            {/* Buttons */}
            <div className="flex space-x-4 pt-6 border-t border-gray-200">
              <button
                type="button"
                onClick={onClose}
                disabled={isSubmitting}
                className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
              >
                {isSubmitting ? 'Saving...' : mode === 'create' ? 'Create Bot' : 'Save Changes'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default BotModal;
