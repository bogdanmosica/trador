// This component displays a summary of a bot and its controls.
import React, { useState } from 'react';
import { BotIdentifier } from '@/types/bots';
import { Link } from '@tanstack/react-router';
import { useStartBot, useStopBot, useBotStatus } from '@/hooks/useBots';
import { BOT_STATUS } from '@/constants/botStatus';

interface BotCardProps {
  bot: BotIdentifier;
}

const BotCard: React.FC<BotCardProps> = ({ bot }) => {
  const [isLoading, setIsLoading] = useState(false);
  
  // Get bot status for additional metrics
  const { data: botStatus } = useBotStatus(bot.id);
  
  // Mutations for bot control
  const startBotMutation = useStartBot();
  const stopBotMutation = useStopBot();

  const handleStartBot = async () => {
    setIsLoading(true);
    try {
      await startBotMutation.mutateAsync(bot.id);
    } catch (error) {
      console.error('Failed to start bot:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStopBot = async () => {
    setIsLoading(true);
    try {
      await stopBotMutation.mutateAsync(bot.id);
    } catch (error) {
      console.error('Failed to stop bot:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case BOT_STATUS.RUNNING:
        return 'bg-green-100 text-green-800'
      case BOT_STATUS.STOPPED:
        return 'bg-gray-100 text-gray-800'
      case BOT_STATUS.ERROR:
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-yellow-100 text-yellow-800'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case BOT_STATUS.RUNNING:
        return '✅'
      case BOT_STATUS.STOPPED:
        return '⏸️'
      case BOT_STATUS.ERROR:
        return '❌'
      default:
        return '⚠️'
    }
  }

  return (
    <div className="bg-white border border-gray-200 p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{bot.id}</h3>
          <p className="text-sm text-gray-600 mt-1">{bot.mode} mode</p>
        </div>
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(bot.status)}`}>
          <span className="mr-1">{getStatusIcon(bot.status)}</span>
          {bot.status}
        </span>
      </div>

      {/* Metrics */}
      <div className="space-y-2 mb-4">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">P&L</span>
          <span className={`text-sm font-medium ${(botStatus?.pnl ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {botStatus?.pnl !== undefined ? `$${botStatus.pnl.toFixed(2)}` : 'Loading...'}
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Equity</span>
          <span className="text-sm font-medium text-gray-900">
            {botStatus?.equity !== undefined ? `$${botStatus.equity.toFixed(2)}` : '-'}
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        <Link 
          to="/bots/$botId" 
          params={{ botId: bot.id }} 
          className="flex-1 text-center bg-blue-50 hover:bg-blue-100 text-blue-700 px-3 py-2 rounded-md text-sm font-medium transition-colors"
        >
          View Details
        </Link>
        {bot.status === BOT_STATUS.RUNNING ? (
          <button 
            onClick={handleStopBot}
            disabled={isLoading}
            className="px-3 py-2 bg-red-50 hover:bg-red-100 text-red-700 rounded-md text-sm font-medium transition-colors disabled:opacity-50"
          >
            {isLoading ? 'Stopping...' : 'Stop'}
          </button>
        ) : (
          <button 
            onClick={handleStartBot}
            disabled={isLoading}
            className="px-3 py-2 bg-green-50 hover:bg-green-100 text-green-700 rounded-md text-sm font-medium transition-colors disabled:opacity-50"
          >
            {isLoading ? 'Starting...' : 'Start'}
          </button>
        )}
      </div>
    </div>
  );
};

export default BotCard;
