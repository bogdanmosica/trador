// This component displays detailed strategy information.
import React from 'react';
import { BotStatus } from '@/types/bots';

interface StrategyDetailsProps {
  status: BotStatus;
}

const StrategyDetails: React.FC<StrategyDetailsProps> = ({ status }) => {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  const formatNumber = (num: number, decimals: number = 4) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(num);
  };

  const getPnLColor = (pnl: number) => {
    if (pnl > 0) return 'text-green-600';
    if (pnl < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const getPnLIcon = (pnl: number) => {
    if (pnl > 0) return '↗️';
    if (pnl < 0) return '↘️';
    return '➡️';
  };

  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-4 border-b border-gray-200">
        <h3 className="text-xl font-bold text-gray-900 flex items-center">
          <span className="mr-2">📊</span>
          Strategy Performance
        </h3>
      </div>

      {/* Key Metrics Grid */}
      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          {/* P&L Card */}
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-100">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600">Total P&L</span>
              <span className="text-lg">{getPnLIcon(status.pnl)}</span>
            </div>
            <div className={`text-2xl font-bold ${getPnLColor(status.pnl)}`}>
              {formatCurrency(status.pnl)}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {status.pnl > 0 ? 'Profit' : status.pnl < 0 ? 'Loss' : 'Break Even'}
            </div>
          </div>

          {/* Balance Card */}
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-100">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600">Available Balance</span>
              <span className="text-lg">💰</span>
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {formatCurrency(status.balance)}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Cash available
            </div>
          </div>

          {/* Equity Card */}
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-100">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600">Total Equity</span>
              <span className="text-lg">📈</span>
            </div>
            <div className="text-2xl font-bold text-blue-600">
              {formatCurrency(status.equity)}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Balance + positions
            </div>
          </div>
        </div>

        {/* Positions Section */}
        <div className="border-t border-gray-200 pt-6">
          <div className="flex items-center mb-4">
            <span className="text-lg font-semibold text-gray-900 mr-2">Open Positions</span>
            <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-medium">
              {status.positions.length} active
            </span>
          </div>
          
          {status.positions.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <span className="text-3xl mb-2 block">📊</span>
              <p className="text-sm">No open positions</p>
            </div>
          ) : (
            <div className="space-y-3">
              {status.positions.map((pos, index) => (
                <div key={index} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className={`w-3 h-3 rounded-full ${pos.side === 'long' ? 'bg-green-400' : 'bg-red-400'}`}></div>
                      <div>
                        <span className="font-semibold text-gray-900">{pos.symbol}</span>
                        <span className={`ml-2 px-2 py-1 rounded text-xs font-medium ${
                          pos.side === 'long' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {pos.side.toUpperCase()}
                        </span>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-gray-900">
                        {formatNumber(pos.quantity)} @ {formatCurrency(pos.price)}
                      </div>
                      <div className="text-xs text-gray-500">
                        Value: {formatCurrency(pos.quantity * pos.price)}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StrategyDetails;
