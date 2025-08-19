// This component displays risk rule status and violations.
import React from 'react';
import { BotRisk } from '@/types/bots';

interface RiskPanelProps {
  risk: BotRisk;
}

const RiskPanel: React.FC<RiskPanelProps> = ({ risk }) => {
  const formatPercentage = (value: number) => {
    return `${value.toFixed(2)}%`;
  };

  const getRiskLevelColor = (isViolated: boolean) => {
    return isViolated ? 'text-red-600' : 'text-green-600';
  };

  const getRiskLevelBg = (isViolated: boolean) => {
    return isViolated ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200';
  };

  const getRiskIcon = (isViolated: boolean) => {
    return isViolated ? '🚨' : '✅';
  };

  const getKillSwitchColor = () => {
    return risk.kill_switch_activated ? 'bg-red-500' : 'bg-green-500';
  };

  const getKillSwitchIcon = () => {
    return risk.kill_switch_activated ? '🛑' : '🟢';
  };

  const getRuleDisplayName = (ruleName: string) => {
    const names: Record<string, string> = {
      'max_drawdown': 'Maximum Drawdown',
      'position_concentration': 'Position Concentration',
      'daily_loss_limit': 'Daily Loss Limit',
      'leverage_limit': 'Leverage Limit',
      'volatility_threshold': 'Volatility Threshold'
    };
    return names[ruleName] || ruleName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const getRuleDescription = (ruleName: string) => {
    const descriptions: Record<string, string> = {
      'max_drawdown': 'Monitors the maximum loss from peak equity',
      'position_concentration': 'Ensures portfolio diversification limits',
      'daily_loss_limit': 'Daily loss protection threshold',
      'leverage_limit': 'Maximum leverage exposure control',
      'volatility_threshold': 'Market volatility safety limits'
    };
    return descriptions[ruleName] || 'Risk management rule evaluation';
  };

  const getProgressPercentage = (details: any) => {
    if (!details) return 0;
    
    const current = parseFloat(details.current_drawdown_pct || details.concentration_pct || 0);
    const threshold = parseFloat(details.threshold_pct || 100);
    
    return Math.min((current / threshold) * 100, 100);
  };

  return (
    <div className="space-y-6">
      {/* Kill Switch Status */}
      <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
        <div className="bg-gradient-to-r from-red-50 to-orange-50 px-6 py-4 border-b border-gray-200">
          <h3 className="text-xl font-bold text-gray-900 flex items-center">
            <span className="mr-2">🛡️</span>
            Emergency Kill Switch
          </h3>
        </div>
        <div className="p-6">
          <div className={`flex items-center justify-between p-4 rounded-lg border-2 ${
            risk.kill_switch_activated 
              ? 'bg-red-50 border-red-200' 
              : 'bg-green-50 border-green-200'
          }`}>
            <div className="flex items-center space-x-3">
              <div className={`w-4 h-4 rounded-full ${getKillSwitchColor()}`}></div>
              <div>
                <h4 className="text-lg font-semibold text-gray-900">
                  {risk.kill_switch_activated ? 'ACTIVATED' : 'SAFE'}
                </h4>
                <p className="text-sm text-gray-600">
                  {risk.kill_switch_activated 
                    ? 'Emergency stop has been triggered' 
                    : 'All systems operating within safe parameters'
                  }
                </p>
              </div>
            </div>
            <span className="text-3xl">{getKillSwitchIcon()}</span>
          </div>
        </div>
      </div>

      {/* Risk Rules Overview */}
      <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-bold text-gray-900 flex items-center">
              <span className="mr-2">📊</span>
              Risk Rule Monitoring
            </h3>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-green-400 rounded-full"></div>
                <span className="text-sm text-gray-600">Passing</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-red-400 rounded-full"></div>
                <span className="text-sm text-gray-600">Violated</span>
              </div>
            </div>
          </div>
        </div>
        
        <div className="p-6">
          <div className="space-y-4">
            {risk.evaluations.map((evaluation, index) => (
              <div key={index} className={`border-2 rounded-lg p-4 transition-all ${getRiskLevelBg(evaluation.is_violated)}`}>
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">{getRiskIcon(evaluation.is_violated)}</span>
                    <div>
                      <h4 className="text-lg font-semibold text-gray-900">
                        {getRuleDisplayName(evaluation.rule_name)}
                      </h4>
                      <p className="text-sm text-gray-600">
                        {getRuleDescription(evaluation.rule_name)}
                      </p>
                    </div>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                    evaluation.is_violated 
                      ? 'bg-red-100 text-red-800' 
                      : 'bg-green-100 text-green-800'
                  }`}>
                    {evaluation.is_violated ? 'VIOLATED' : 'PASSING'}
                  </span>
                </div>

                {/* Rule Details */}
                {evaluation.details && (
                  <div className="space-y-3">
                    {/* Progress Bar */}
                    {(evaluation.details.current_drawdown_pct !== undefined || evaluation.details.concentration_pct !== undefined) && (
                      <div>
                        <div className="flex justify-between text-sm text-gray-600 mb-1">
                          <span>Current Level</span>
                          <span>Threshold</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                          <div 
                            className={`h-2 rounded-full transition-all ${
                              evaluation.is_violated ? 'bg-red-500' : 'bg-green-500'
                            }`}
                            style={{ width: `${getProgressPercentage(evaluation.details)}%` }}
                          ></div>
                        </div>
                      </div>
                    )}

                    {/* Metrics Grid */}
                    <div className="grid grid-cols-2 gap-4">
                      {evaluation.details.current_drawdown_pct !== undefined && (
                        <div className="bg-white bg-opacity-50 rounded-lg p-3">
                          <div className="text-xs text-gray-500 uppercase tracking-wide">Current Drawdown</div>
                          <div className={`text-lg font-bold ${getRiskLevelColor(evaluation.is_violated)}`}>
                            {formatPercentage(Number(evaluation.details.current_drawdown_pct) || 0)}
                          </div>
                        </div>
                      )}
                      
                      {evaluation.details.threshold_pct !== undefined && (
                        <div className="bg-white bg-opacity-50 rounded-lg p-3">
                          <div className="text-xs text-gray-500 uppercase tracking-wide">Threshold</div>
                          <div className="text-lg font-bold text-gray-700">
                            {formatPercentage(Number(evaluation.details.threshold_pct) || 0)}
                          </div>
                        </div>
                      )}

                      {evaluation.details.concentration_pct !== undefined && (
                        <div className="bg-white bg-opacity-50 rounded-lg p-3">
                          <div className="text-xs text-gray-500 uppercase tracking-wide">Concentration</div>
                          <div className={`text-lg font-bold ${getRiskLevelColor(evaluation.is_violated)}`}>
                            {formatPercentage(Number(evaluation.details.concentration_pct) || 0)}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Risk Summary */}
      <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
        <div className="bg-gradient-to-r from-purple-50 to-pink-50 px-6 py-4 border-b border-gray-200">
          <h3 className="text-xl font-bold text-gray-900 flex items-center">
            <span className="mr-2">📈</span>
            Risk Summary
          </h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-50 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-gray-900">
                {risk.evaluations.length}
              </div>
              <div className="text-sm text-gray-600">Total Rules</div>
            </div>
            <div className="bg-green-50 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-green-600">
                {risk.evaluations.filter(e => !e.is_violated).length}
              </div>
              <div className="text-sm text-gray-600">Passing</div>
            </div>
            <div className="bg-red-50 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-red-600">
                {risk.evaluations.filter(e => e.is_violated).length}
              </div>
              <div className="text-sm text-gray-600">Violations</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RiskPanel;
