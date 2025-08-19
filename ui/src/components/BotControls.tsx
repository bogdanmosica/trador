// This component provides buttons for bot control actions.
import React, { useState } from 'react';
import { useStartBot, useStopBot, useKillBot, useBots } from '@/hooks/useBots';
import { BOT_STATUS } from '@/constants/botStatus';
import ConfirmDialog from './ConfirmDialog';
import BotModal from './BotModal';

interface BotControlsProps {
  botId: string;
}

const BotControls: React.FC<BotControlsProps> = ({ botId }) => {
  const [isKillDialogOpen, setIsKillDialogOpen] = useState(false);
  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);
  
  const { data: bots } = useBots();
  const startMutation = useStartBot();
  const stopMutation = useStopBot();
  const killMutation = useKillBot();
  
  // Get current bot status
  const currentBot = bots?.find(bot => bot.id === botId);
  const botStatus = currentBot?.status || BOT_STATUS.UNKNOWN;
  const isRunning = botStatus === BOT_STATUS.RUNNING;

  const handleStart = () => {
    startMutation.mutate(botId);
  };

  const handleStop = () => {
    stopMutation.mutate(botId);
  };

  const handleKillConfirm = () => {
    killMutation.mutate(botId);
  };

  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-gray-50 to-slate-50 px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-bold text-gray-900 flex items-center">
          <span className="mr-2">🎮</span>
          Bot Controls
        </h3>
      </div>

      {/* Controls Grid */}
      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {/* Start/Stop Button - Conditional */}
          {!isRunning ? (
            <button 
              onClick={handleStart} 
              disabled={startMutation.isPending}
              className="flex flex-col items-center justify-center p-4 bg-green-50 hover:bg-green-100 border border-green-200 rounded-lg text-green-700 transition-all duration-200 hover:shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span className="text-2xl mb-2">▶️</span>
              <span className="text-sm font-medium">
                {startMutation.isPending ? 'Starting...' : 'Start Bot'}
              </span>
            </button>
          ) : (
            <button 
              onClick={handleStop} 
              disabled={stopMutation.isPending}
              className="flex flex-col items-center justify-center p-4 bg-yellow-50 hover:bg-yellow-100 border border-yellow-200 rounded-lg text-yellow-700 transition-all duration-200 hover:shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span className="text-2xl mb-2">⏸️</span>
              <span className="text-sm font-medium">
                {stopMutation.isPending ? 'Stopping...' : 'Stop Bot'}
              </span>
            </button>
          )}

          {/* Emergency Kill Switch Button */}
          <button 
            onClick={() => setIsKillDialogOpen(true)} 
            disabled={killMutation.isPending || !isRunning}
            className="flex flex-col items-center justify-center p-4 bg-red-50 hover:bg-red-100 border border-red-200 rounded-lg text-red-700 transition-all duration-200 hover:shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span className="text-2xl mb-2">🚨</span>
            <span className="text-sm font-medium">
              {killMutation.isPending ? 'Killing...' : 'Emergency Kill'}
            </span>
          </button>

          {/* Config Button */}
          <button 
            onClick={() => setIsConfigModalOpen(true)} 
            className="flex flex-col items-center justify-center p-4 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-lg text-blue-700 transition-all duration-200 hover:shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span className="text-2xl mb-2">⚙️</span>
            <span className="text-sm font-medium">
              Configure
            </span>
          </button>
        </div>
        
        {/* Bot Status Indicator */}
        <div className="mt-4 p-3 bg-gray-50 border border-gray-200 rounded-lg">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-600">Bot Status:</span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
              isRunning 
                ? 'bg-green-100 text-green-800' 
                : botStatus === BOT_STATUS.ERROR 
                ? 'bg-red-100 text-red-800'
                : 'bg-gray-100 text-gray-800'
            }`}>
              {botStatus.toUpperCase()}
            </span>
          </div>
        </div>

        {/* Status Messages */}
        <div className="mt-4">
          {startMutation.isError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-700">Failed to start bot. Please try again.</p>
            </div>
          )}
          {stopMutation.isError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-700">Failed to stop bot. Please try again.</p>
            </div>
          )}
          {killMutation.isError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-700">Emergency stop failed. Please contact support.</p>
            </div>
          )}
        </div>
        
        {/* Dialogs and Modals */}
        <ConfirmDialog
          isOpen={isKillDialogOpen}
          onClose={() => setIsKillDialogOpen(false)}
          onConfirm={handleKillConfirm}
          title="Emergency Kill Switch"
          message="Are you sure you want to trigger the emergency kill switch? This will immediately stop the bot and close all positions. This action cannot be undone."
          confirmText="Emergency Kill"
          cancelText="Cancel"
          type="danger"
        />
        
        <BotModal
          isOpen={isConfigModalOpen}
          onClose={() => setIsConfigModalOpen(false)}
          mode="edit"
          botId={botId}
        />
      </div>
    </div>
  );
};

export default BotControls;