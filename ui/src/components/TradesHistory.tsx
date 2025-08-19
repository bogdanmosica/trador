// This component displays the trade history for a bot.
import React, { useState, useMemo, useEffect } from 'react';
import { useBotTrades, useBotStatus } from '@/hooks/useBots';
import { POSITION_STATUS, POSITION_DIRECTION, TRADE_SIDE, TRADE_TYPE } from '@/constants/botStatus';
import Badge from './Badge';

interface TradesHistoryProps {
  botId: string;
}

const TRADES_PER_PAGE = 5;

const TradesHistory: React.FC<TradesHistoryProps> = ({ botId }) => {
  const { data: trades, isLoading, error, refetch: refetchTrades } = useBotTrades(botId);
  const { data: botStatus, refetch: refetchStatus } = useBotStatus(botId);
  const [currentPage, setCurrentPage] = useState(1);

  // Auto-refresh data every second for live updates
  useEffect(() => {
    const interval = setInterval(() => {
      refetchTrades();
      refetchStatus();
    }, 1000);

    return () => clearInterval(interval);
  }, [refetchTrades, refetchStatus]);

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

  const formatDateTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Determine position direction based on trade sequence and type
  const getPositionDirection = (trade: any, allTrades: any[]) => {
    // If we have explicit backend type, use trade context to determine direction
    if (trade.type === TRADE_TYPE.OPEN) {
      // Opening trade: buy = long position, sell = short position
      return trade.side === TRADE_SIDE.BUY ? POSITION_DIRECTION.LONG : POSITION_DIRECTION.SHORT;
    } else if (trade.type === TRADE_TYPE.CLOSE) {
      // Closing trade: find the corresponding opening trade
      const openingTrade = findOpeningTrade(trade, allTrades);
      if (openingTrade) {
        return openingTrade.side === TRADE_SIDE.BUY ? POSITION_DIRECTION.LONG : POSITION_DIRECTION.SHORT;
      }
    }
    
    // Fallback: try to determine from current positions or trade sequence
    if (botStatus?.positions) {
      const position = botStatus.positions.find((pos: any) => pos.symbol === trade.symbol);
      if (position) {
        return position.side;
      }
    }
    
    // Final fallback: assume based on trade side
    return trade.side === TRADE_SIDE.BUY ? POSITION_DIRECTION.LONG : POSITION_DIRECTION.SHORT;
  };
  
  // Find the corresponding opening trade for a closing trade
  const findOpeningTrade = (closingTrade: any, allTrades: any[]) => {
    // Look backwards from current trade to find the opening trade
    const closingIndex = allTrades.findIndex(t => t.timestamp === closingTrade.timestamp);
    if (closingIndex === -1) return null;
    
    // Find the most recent opening trade for the same symbol
    for (let i = closingIndex - 1; i >= 0; i--) {
      const trade = allTrades[i];
      if (trade.symbol === closingTrade.symbol && trade.type === TRADE_TYPE.OPEN) {
        return trade;
      }
    }
    return null;
  };

  const getPositionIcon = (side: string) => {
    switch (side.toLowerCase()) {
      case TRADE_SIDE.BUY:
        return '📈';
      case TRADE_SIDE.SELL:
        return '📉';
      default:
        return '🔄';
    }
  };

  // Calculate P&L for trades (enhanced with live data)
  const calculateTradePnL = (trade: any, index: number) => {
    if (!trades) return { pnl: null, isLive: false };
    
    // If trade has explicit P&L, use it (realized P&L)
    if (trade.pnl !== undefined && trade.pnl !== 0) {
      return { pnl: trade.pnl, isLive: false };
    }
    
    // For open positions, calculate unrealized P&L using current market price
    const positionStatus = getPositionStatus(trade);
    if (positionStatus === 'open' && botStatus && botStatus.positions) {
      const position = botStatus.positions.find((pos: any) => pos.symbol === trade.symbol);
      if (position) {
        // Get current market price from the position or estimate it
        const currentPrice = position.price; // This should be current market price
        const entryPrice = trade.price;
        
        let unrealizedPnL = 0;
        if (trade.side === TRADE_SIDE.BUY) {
          // Long position
          unrealizedPnL = (currentPrice - entryPrice) * trade.quantity;
        } else if (trade.side === TRADE_SIDE.SELL) {
          // Short position
          unrealizedPnL = (entryPrice - currentPrice) * trade.quantity;
        }
        
        return { pnl: unrealizedPnL, isLive: true };
      }
    }
    
    // Simple P&L calculation for completed buy/sell pairs (realized P&L)
    if (trade.side === TRADE_SIDE.SELL && index > 0) {
      const prevTrade = trades[index - 1];
      if (prevTrade && prevTrade.side === TRADE_SIDE.BUY && prevTrade.symbol === trade.symbol) {
        const realizedPnL = (trade.price - prevTrade.price) * Math.min(trade.quantity, prevTrade.quantity);
        return { pnl: realizedPnL, isLive: false };
      }
    }
    
    return { pnl: null, isLive: false };
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case POSITION_STATUS.OPEN:
        return '🚪';
      case POSITION_STATUS.CLOSED:
        return '🔒';
      default:
        return '🔄';
    }
  };

  // Get position status (open/closed) from trade type
  const getPositionStatus = (trade: any) => {
    // Use explicit backend type if available
    if (trade.type === TRADE_TYPE.OPEN) return POSITION_STATUS.OPEN;
    if (trade.type === TRADE_TYPE.CLOSE) return POSITION_STATUS.CLOSED;
    
    // Fallback logic based on current positions
    if (!botStatus || !botStatus.positions) return POSITION_STATUS.UNKNOWN;
    
    const hasOpenPosition = botStatus.positions.some((pos: any) => pos.symbol === trade.symbol);
    
    // For trades without explicit type, make educated guess
    // This is imperfect but better than the previous logic
    if (hasOpenPosition) {
      // If position is still open, this might be the opening trade
      return POSITION_STATUS.OPEN;
    } else {
      // If no position exists, this might be a closing trade
      return POSITION_STATUS.CLOSED;
    }
  };


  const getPnLColor = (pnl: number | null) => {
    if (pnl === null) return 'text-gray-500';
    if (pnl > 0) return 'text-green-600';
    if (pnl < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  // Pagination logic
  const paginatedTrades = useMemo(() => {
    if (!trades) return [];
    
    // Sort trades by timestamp (newest first)
    const sortedTrades = [...trades].sort((a, b) => 
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
    
    const startIndex = (currentPage - 1) * TRADES_PER_PAGE;
    return sortedTrades.slice(startIndex, startIndex + TRADES_PER_PAGE);
  }, [trades, currentPage]);

  const totalPages = trades ? Math.ceil(trades.length / TRADES_PER_PAGE) : 0;

  const goToPage = (page: number) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)));
  };

  if (isLoading) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-100 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-6">
        <div className="text-center py-8">
          <span className="text-3xl mb-2 block">⚠️</span>
          <p className="text-red-600">Error loading trades</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-50 to-emerald-50 px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-bold text-gray-900 flex items-center">
            <span className="mr-2">📊</span>
            Trade History
          </h3>
          <div className="flex items-center space-x-3">
            <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium">
              {trades?.length || 0} total trades
            </span>
            <span className="bg-red-100 text-red-800 px-3 py-1 rounded-full text-sm font-medium flex items-center">
              <span className="w-2 h-2 bg-red-500 rounded-full mr-2 animate-pulse"></span>
              LIVE
            </span>
            {totalPages > 1 && (
              <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
                Page {currentPage} of {totalPages}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Trades List */}
      <div className="p-6">
        {!trades || trades.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <span className="text-4xl mb-4 block">📈</span>
            <h4 className="text-lg font-medium text-gray-900 mb-2">No trades yet</h4>
            <p className="text-sm">Start the bot to see trading activity here.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {paginatedTrades.map((trade, index) => {
              const pnlResult = calculateTradePnL(trade, index);
              const positionStatus = getPositionStatus(trade);
              const positionDirection = getPositionDirection(trade, trades || []);
              const tradeId = `${trade.symbol}-${trade.timestamp}`;
              
              return (
              <div key={tradeId} className="bg-gray-50 border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2 flex-wrap">
                      <span className="text-lg">{getPositionIcon(trade.side)}</span>
                      <Badge 
                        variant={positionDirection as 'long' | 'short'}
                      >
                        {positionDirection.toUpperCase()}
                      </Badge>
                      <Badge 
                        variant={positionStatus as 'open' | 'closed'}
                        icon={getStatusIcon(positionStatus)}
                      >
                        {positionStatus.toUpperCase()}
                      </Badge>
                      {/* Trade ID for debugging */}
                      <span className="text-xs text-gray-400 font-mono">
                        {trade.side.toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <div className="font-semibold text-gray-900">{trade.symbol}</div>
                      <div className="text-xs text-gray-500">{formatDateTime(trade.timestamp)}</div>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className="flex items-center space-x-4">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {formatNumber(trade.quantity)}
                        </div>
                        <div className="text-xs text-gray-500">Quantity</div>
                      </div>
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {formatCurrency(trade.price)}
                        </div>
                        <div className="text-xs text-gray-500">Price</div>
                      </div>
                      {/* P&L Column - Always Visible */}
                      <div>
                        <div className={`text-sm font-bold ${getPnLColor(pnlResult.pnl)}`}>
                          {pnlResult.pnl !== null ? (
                            <>
                              {pnlResult.pnl > 0 ? '+' : ''}{formatCurrency(pnlResult.pnl)}
                              {pnlResult.isLive && (
                                <span className="text-xs ml-1 font-normal text-gray-500">LIVE</span>
                              )}
                            </>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </div>
                        <div className="text-xs text-gray-500">
                          {pnlResult.isLive ? 'Unrealized P&L' : 'P&L'}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              );
            })}
          </div>
        )}

        {/* Pagination Controls */}
        {totalPages > 1 && (
          <div className="mt-6 flex items-center justify-between border-t border-gray-200 pt-4">
            <div className="text-sm text-gray-600">
              Showing {((currentPage - 1) * TRADES_PER_PAGE) + 1} to {Math.min(currentPage * TRADES_PER_PAGE, trades?.length || 0)} of {trades?.length || 0} trades
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => goToPage(currentPage - 1)}
                disabled={currentPage === 1}
                className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              
              {/* Page Numbers */}
              <div className="flex space-x-1">
                {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                  let pageNum;
                  if (totalPages <= 5) {
                    pageNum = i + 1;
                  } else if (currentPage <= 3) {
                    pageNum = i + 1;
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i;
                  } else {
                    pageNum = currentPage - 2 + i;
                  }
                  
                  return (
                    <button
                      key={pageNum}
                      onClick={() => goToPage(pageNum)}
                      className={`px-3 py-2 text-sm font-medium rounded-md ${
                        currentPage === pageNum
                          ? 'bg-blue-600 text-white'
                          : 'text-gray-500 bg-white border border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      {pageNum}
                    </button>
                  );
                })}
              </div>

              <button
                onClick={() => goToPage(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TradesHistory;