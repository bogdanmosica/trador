// This file contains the API client for interacting with the backend.
import axios from 'axios';
import { BotIdentifier, BotStatus, Trade, BotRisk, BotConfig, BotConfigUpdate } from '@/types/bots';
import { GlobalMetrics } from '@/types/metrics';
import { StrategyDiscoveryResponse, StrategyInfo, StrategyConfig, StrategyValidationRequest, StrategyValidationResponse } from '@/types/strategies';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
});

export const fetchBots = async (): Promise<BotIdentifier[]> => {
  const response = await api.get<BotIdentifier[]>('/bots');
  return response.data;
};

export const createBot = async (botData: any): Promise<void> => {
  await api.post('/bots', botData);
};

export const fetchBotStatus = async (botId: string): Promise<BotStatus> => {
  const response = await api.get<BotStatus>(`/bots/${botId}/status`);
  return response.data;
};

export const fetchBotTrades = async (botId: string): Promise<Trade[]> => {
  try {
    const response = await api.get<Trade[]>(`/bots/${botId}/trades`);
    return response.data;
  } catch (error: any) {
    // If no trades found (404), return empty array instead of throwing error
    if (error?.response?.status === 404) {
      return [];
    }
    // Re-throw other errors
    throw error;
  }
};

export const fetchBotRisk = async (botId: string): Promise<BotRisk> => {
  const response = await api.get<BotRisk>(`/bots/${botId}/risk`);
  return response.data;
};

export const fetchBotLogs = async (botId: string): Promise<string[]> => {
  const response = await api.get<string[]>(`/bots/${botId}/logs`);
  return response.data;
};

export const fetchBotConfig = async (botId: string): Promise<BotConfig> => {
  const response = await api.get<BotConfig>(`/bots/${botId}/config`);
  return response.data;
};

export const startBot = async (botId: string): Promise<void> => {
  await api.post(`/bots/${botId}/start`);
};

export const stopBot = async (botId: string): Promise<void> => {
  await api.post(`/bots/${botId}/stop`);
};

export const killBot = async (botId: string): Promise<void> => {
  await api.post(`/bots/${botId}/kill`);
};

export const updateBotConfig = async (botId: string, config: BotConfigUpdate): Promise<void> => {
  await api.put(`/bots/${botId}/config`, config);
};

export const fetchGlobalMetrics = async (): Promise<GlobalMetrics> => {
  const response = await api.get<GlobalMetrics>('/metrics/global');
  return response.data;
};

export const fetchAvailableStrategies = async (): Promise<Array<{value: string; label: string}>> => {
  const response = await api.get<Array<{value: string; label: string}>>('/available-strategies');
  return response.data;
};

export const fetchAvailableSymbols = async (): Promise<Array<{value: string; label: string}>> => {
  const response = await api.get<Array<{value: string; label: string}>>('/available-symbols');
  return response.data;
};

// Strategy API functions
export const fetchStrategies = async (force_rescan?: boolean): Promise<StrategyDiscoveryResponse> => {
  const params = force_rescan ? { force_rescan: true } : {};
  const response = await api.get<StrategyDiscoveryResponse>('/strategies', { params });
  return response.data;
};

export const fetchStrategyDetails = async (strategyName: string): Promise<StrategyInfo> => {
  const response = await api.get<StrategyInfo>(`/strategies/${strategyName}`);
  return response.data;
};

export const fetchStrategySchema = async (strategyName: string): Promise<Record<string, any>> => {
  const response = await api.get<Record<string, any>>(`/strategies/${strategyName}/schema`);
  return response.data;
};

export const fetchConfigurations = async (strategyClass?: string): Promise<StrategyConfig[]> => {
  const params = strategyClass ? { strategy_class: strategyClass } : {};
  const response = await api.get<StrategyConfig[]>('/configurations', { params });
  return response.data;
};

export const fetchConfigurationDetails = async (configName: string): Promise<StrategyConfig> => {
  const response = await api.get<StrategyConfig>(`/configurations/${configName}`);
  return response.data;
};

export const validateStrategyParameters = async (
  strategyName: string,
  request: StrategyValidationRequest
): Promise<StrategyValidationResponse> => {
  const response = await api.post<StrategyValidationResponse>(`/strategies/${strategyName}/validate`, request);
  return response.data;
};

export const rescanStrategies = async (): Promise<{message: string; total_strategies: number; total_configurations: number}> => {
  const response = await api.post<{message: string; total_strategies: number; total_configurations: number}>('/strategies/rescan');
  return response.data;
};
