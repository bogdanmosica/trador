import React, { useState, useEffect } from 'react';
import { useBotConfig, useUpdateBotConfig, useAvailableStrategies, useAvailableSymbols } from '@/hooks/useBots';
import { BotConfig } from '@/types/bots';

interface ConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  botId: string;
}

const ConfigModal: React.FC<ConfigModalProps> = ({ isOpen, onClose, botId }) => {
  const { data: config, isLoading: configLoading, error, refetch } = useBotConfig(botId);
  const { data: availableStrategies, isLoading: strategiesLoading } = useAvailableStrategies();
  const { data: availableSymbols, isLoading: symbolsLoading } = useAvailableSymbols();
  const updateConfigMutation = useUpdateBotConfig();
  
  const [formData, setFormData] = useState<Partial<BotConfig>>({});
  const [hasChanges, setHasChanges] = useState(false);

  const isLoading = configLoading || strategiesLoading || symbolsLoading;

  // Update form data when config loads
  useEffect(() => {
    if (config && isOpen) {
      setFormData({
        strategy: config.strategy,
        symbol: config.symbol,
        mode: config.mode,
        initial_balance: config.initial_balance,
        parameters: { ...config.parameters },
      });
      setHasChanges(false);
    }
  }, [config, isOpen]);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleParameterChange = (key: string, value: string | number | boolean) => {
    setFormData(prev => ({
      ...prev,
      parameters: {
        ...prev.parameters,
        [key]: value
      }
    }));
    setHasChanges(true);
  };

  const handleBasicFieldChange = (key: keyof BotConfig, value: string | number) => {
    setFormData(prev => ({
      ...prev,
      [key]: value
    }));
    setHasChanges(true);
  };

  const handleSave = async () => {
    try {
      await updateConfigMutation.mutateAsync({
        botId,
        config: {
          strategy: formData.strategy || '',
          symbol: formData.symbol || '',
          mode: formData.mode || '',
          initial_balance: formData.initial_balance || 0,
          parameters: formData.parameters || {}
        }
      });
      setHasChanges(false);
      await refetch(); // Refresh the config
      onClose();
    } catch (error) {
      console.error('Failed to update config:', error);
    }
  };

  const handleReset = () => {
    if (config) {
      setFormData({
        strategy: config.strategy,
        symbol: config.symbol,
        mode: config.mode,
        initial_balance: config.initial_balance,
        parameters: { ...config.parameters },
      });
      setHasChanges(false);
    }
  };

  const renderParameterInput = (key: string, value: any) => {
    const paramType = typeof value;
    
    if (paramType === 'boolean') {
      return (
        <div key={key} className="flex items-center justify-between py-2">
          <label className="text-sm font-medium text-gray-700">{key}</label>
          <input
            type="checkbox"
            checked={value}
            onChange={(e) => handleParameterChange(key, e.target.checked)}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
        </div>
      );
    }
    
    if (paramType === 'number') {
      return (
        <div key={key} className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">{key}</label>
          <input
            type="number"
            value={value}
            step="any"
            onChange={(e) => handleParameterChange(key, parseFloat(e.target.value) || 0)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
          />
        </div>
      );
    }
    
    // Default to string input
    return (
      <div key={key} className="space-y-1">
        <label className="block text-sm font-medium text-gray-700">{key}</label>
        <input
          type="text"
          value={value?.toString() || ''}
          onChange={(e) => handleParameterChange(key, e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
        />
      </div>
    );
  };

  return (
    <div className="fixed inset-0 z-[9999] overflow-y-auto" onClick={onClose}>
      <div className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"></div>
      
      <div className="flex min-h-full items-center justify-center p-4">
        <div 
          className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 transform transition-all"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <span className="mr-2">⚙️</span>
                Bot Configuration
              </h3>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <span className="sr-only">Close</span>
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="px-6 py-4 max-h-96 overflow-y-auto">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span className="ml-2 text-gray-600">Loading configuration...</span>
              </div>
            ) : error ? (
              <div className="text-center py-8">
                <span className="text-red-600">Error loading configuration</span>
              </div>
            ) : config ? (
              <div className="space-y-6">
                {/* Basic Info */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-3">Bot Information</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Bot ID</label>
                      <input
                        type="text"
                        value={config.id}
                        disabled
                        className="w-full px-3 py-2 bg-gray-100 border border-gray-300 rounded-md text-sm text-gray-600 cursor-not-allowed"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Strategy</label>
                      <select
                        value={formData.strategy || ''}
                        onChange={(e) => handleBasicFieldChange('strategy', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
                      >
                        <option value="">Select Strategy</option>
                        {availableStrategies?.map((strategy) => (
                          <option key={strategy.value} value={strategy.value}>
                            {strategy.label}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Symbol</label>
                      <select
                        value={formData.symbol || ''}
                        onChange={(e) => handleBasicFieldChange('symbol', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
                      >
                        <option value="">Select Trading Pair</option>
                        {availableSymbols?.map((symbol) => (
                          <option key={symbol.value} value={symbol.value}>
                            {symbol.label}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Mode</label>
                      <select
                        value={formData.mode || ''}
                        onChange={(e) => handleBasicFieldChange('mode', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
                      >
                        <option value="paper">Paper Trading</option>
                        <option value="live">Live Trading</option>
                        <option value="backtest">Backtest</option>
                      </select>
                    </div>
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">Initial Balance</label>
                      <input
                        type="number"
                        value={formData.initial_balance || 0}
                        onChange={(e) => handleBasicFieldChange('initial_balance', parseFloat(e.target.value) || 0)}
                        step="0.01"
                        min="0"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
                      />
                    </div>
                  </div>
                </div>

                {/* Strategy Parameters */}
                {formData.parameters && Object.keys(formData.parameters).length > 0 && (
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <h4 className="font-medium text-gray-900 mb-3">Strategy Parameters</h4>
                    <div className="space-y-3">
                      {Object.entries(formData.parameters).map(([key, value]) => 
                        renderParameterInput(key, value)
                      )}
                    </div>
                  </div>
                )}

                {/* Status */}
                <div className="bg-yellow-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-3">Status</h4>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      config.status === 'running' ? 'bg-green-100 text-green-800' : 
                      config.status === 'stopped' ? 'bg-gray-100 text-gray-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {config.status.toUpperCase()}
                    </span>
                    <span className="text-sm text-gray-600">
                      {config.status === 'running' ? 'Bot is currently active' : 'Bot is inactive'}
                    </span>
                  </div>
                </div>
              </div>
            ) : null}
          </div>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-gray-200 flex justify-between">
            <div className="flex space-x-2">
              {hasChanges && (
                <button
                  onClick={handleReset}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                >
                  Reset
                </button>
              )}
            </div>
            
            <div className="flex space-x-3">
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={!hasChanges || updateConfigMutation.isPending}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {updateConfigMutation.isPending ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConfigModal;