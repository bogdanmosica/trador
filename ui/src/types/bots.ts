// This file defines TypeScript types for bot-related data.

export interface BotIdentifier {
  id: string;
  mode: string;
  status: string;
}

export interface Position {
  symbol: string;
  quantity: number;
  price: number;
  side: 'long' | 'short';
}

export interface BotStatus {
  pnl: number;
  positions: Position[];
  balance: number;
  equity: number;
}

export interface Trade {
  timestamp: string;
  symbol: string;
  side: string;
  price: number;
  quantity: number;
  type?: string; // 'open', 'close', or 'unknown'
  pnl?: number; // P&L for closing trades
}

export interface RiskEvaluationDetails {
  value?: number;
  threshold?: number;
  message?: string;
  [key: string]: unknown;
}

export interface RiskEvaluation {
  rule_name: string;
  is_violated: boolean;
  details: RiskEvaluationDetails;
}

export interface BotRisk {
  evaluations: RiskEvaluation[];
  kill_switch_activated: boolean;
}

export interface BotConfig {
  id: string;
  strategy: string;
  symbol: string;
  mode: string;
  initial_balance: number;
  status: string;
  parameters: {
    [key: string]: string | number | boolean;
  };
  risk_settings?: {
    max_position_size?: number;
    max_drawdown?: number;
    [key: string]: unknown;
  };
}

export interface BotConfigUpdate {
  strategy?: string;
  symbol?: string;
  mode?: string;
  initial_balance?: number;
  parameters?: {
    [key: string]: string | number | boolean;
  };
  risk_settings?: {
    max_position_size?: number;
    max_drawdown?: number;
    [key: string]: unknown;
  };
}
