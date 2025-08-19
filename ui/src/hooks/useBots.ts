// This file contains React Query hooks for fetching bot data.
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchBots,
  createBot,
  fetchBotStatus,
  fetchBotTrades,
  fetchBotRisk,
  fetchBotLogs,
  fetchBotConfig,
  fetchAvailableStrategies,
  fetchAvailableSymbols,
  startBot,
  stopBot,
  killBot,
  updateBotConfig,
  fetchGlobalMetrics,
  fetchStrategies,
  fetchStrategyDetails,
  fetchStrategySchema,
  fetchConfigurations,
  fetchConfigurationDetails,
  validateStrategyParameters,
  rescanStrategies,
} from '@/lib/api';
import { BotIdentifier, BotStatus, Trade, BotRisk, BotConfig, BotConfigUpdate } from '@/types/bots';
import { GlobalMetrics } from '@/types/metrics';
import { StrategyDiscoveryResponse, StrategyInfo, StrategyConfig, StrategyValidationRequest } from '@/types/strategies';

export const useBots = () => {
  return useQuery<BotIdentifier[]>({ queryKey: ['bots'], queryFn: fetchBots });
};

export const useBotStatus = (botId: string) => {
  return useQuery<BotStatus>({ queryKey: ['botStatus', botId], queryFn: () => fetchBotStatus(botId) });
};

export const useBotTrades = (botId: string) => {
  return useQuery<Trade[]>({ queryKey: ['botTrades', botId], queryFn: () => fetchBotTrades(botId) });
};

export const useBotRisk = (botId: string) => {
  return useQuery<BotRisk>({ queryKey: ['botRisk', botId], queryFn: () => fetchBotRisk(botId) });
};

export const useBotLogs = (botId: string) => {
  return useQuery<string[]>({ queryKey: ['botLogs', botId], queryFn: () => fetchBotLogs(botId) });
};

export const useBotConfig = (botId: string, enabled: boolean = true) => {
  return useQuery<BotConfig>({ 
    queryKey: ['botConfig', botId], 
    queryFn: () => fetchBotConfig(botId),
    enabled: enabled && !!botId
  });
};

export const useGlobalMetrics = () => {
  return useQuery<GlobalMetrics>({ queryKey: ['globalMetrics'], queryFn: fetchGlobalMetrics });
};

export const useAvailableStrategies = () => {
  return useQuery<Array<{value: string; label: string}>>({ 
    queryKey: ['availableStrategies'], 
    queryFn: fetchAvailableStrategies 
  });
};

export const useAvailableSymbols = () => {
  return useQuery<Array<{value: string; label: string}>>({ 
    queryKey: ['availableSymbols'], 
    queryFn: fetchAvailableSymbols 
  });
};

export const useStartBot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: startBot,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bots'] });
      queryClient.invalidateQueries({ queryKey: ['botStatus'] });
    },
  });
};

export const useStopBot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: stopBot,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bots'] });
      queryClient.invalidateQueries({ queryKey: ['botStatus'] });
    },
  });
};

export const useKillBot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: killBot,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bots'] });
      queryClient.invalidateQueries({ queryKey: ['botStatus'] });
      queryClient.invalidateQueries({ queryKey: ['botRisk'] });
    },
  });
};

export const useUpdateBotConfig = () => {
  const queryClient = useQueryClient();
  return useMutation<void, Error, { botId: string; config: BotConfigUpdate }>({
    mutationFn: ({ botId, config }) => updateBotConfig(botId, config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bots'] });
      queryClient.invalidateQueries({ queryKey: ['botStatus'] });
      queryClient.invalidateQueries({ queryKey: ['botConfig'] });
    },
  });
};

export const useCreateBot = () => {
  const queryClient = useQueryClient();
  return useMutation<void, Error, any>({
    mutationFn: (botData) => createBot(botData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bots'] });
    },
  });
};

// Strategy hooks
export const useStrategies = (forceRescan?: boolean) => {
  return useQuery<StrategyDiscoveryResponse>({ 
    queryKey: ['strategies', forceRescan], 
    queryFn: () => fetchStrategies(forceRescan)
  });
};

export const useStrategyDetails = (strategyName: string, enabled: boolean = true) => {
  return useQuery<StrategyInfo>({ 
    queryKey: ['strategyDetails', strategyName], 
    queryFn: () => fetchStrategyDetails(strategyName),
    enabled: enabled && !!strategyName
  });
};

export const useStrategySchema = (strategyName: string, enabled: boolean = true) => {
  return useQuery<Record<string, any>>({ 
    queryKey: ['strategySchema', strategyName], 
    queryFn: () => fetchStrategySchema(strategyName),
    enabled: enabled && !!strategyName
  });
};

export const useConfigurations = (strategyClass?: string) => {
  return useQuery<StrategyConfig[]>({ 
    queryKey: ['configurations', strategyClass], 
    queryFn: () => fetchConfigurations(strategyClass)
  });
};

export const useConfigurationDetails = (configName: string, enabled: boolean = true) => {
  return useQuery<StrategyConfig>({ 
    queryKey: ['configurationDetails', configName], 
    queryFn: () => fetchConfigurationDetails(configName),
    enabled: enabled && !!configName
  });
};

export const useValidateStrategyParameters = () => {
  return useMutation<any, Error, {strategyName: string; request: StrategyValidationRequest}>({
    mutationFn: ({ strategyName, request }) => validateStrategyParameters(strategyName, request),
  });
};

export const useRescanStrategies = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: rescanStrategies,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['strategies'] });
      queryClient.invalidateQueries({ queryKey: ['configurations'] });
    },
  });
};
