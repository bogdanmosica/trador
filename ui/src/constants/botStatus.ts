export const BOT_STATUS = {
  RUNNING: 'running',
  STOPPED: 'stopped',
  ERROR: 'error',
  KILLED: 'killed',
  UNKNOWN: 'unknown'
} as const;

export const POSITION_STATUS = {
  OPEN: 'open',
  CLOSED: 'closed',
  UNKNOWN: 'unknown'
} as const;

export const POSITION_DIRECTION = {
  LONG: 'long',
  SHORT: 'short',
  UNKNOWN: 'unknown'
} as const;

export const TRADE_SIDE = {
  BUY: 'buy',
  SELL: 'sell'
} as const;

export const TRADE_TYPE = {
  OPEN: 'open',
  CLOSE: 'close',
  UNKNOWN: 'unknown'
} as const;

export type BotStatus = typeof BOT_STATUS[keyof typeof BOT_STATUS];
export type PositionStatus = typeof POSITION_STATUS[keyof typeof POSITION_STATUS];
export type PositionDirection = typeof POSITION_DIRECTION[keyof typeof POSITION_DIRECTION];
export type TradeSide = typeof TRADE_SIDE[keyof typeof TRADE_SIDE];
export type TradeType = typeof TRADE_TYPE[keyof typeof TRADE_TYPE];