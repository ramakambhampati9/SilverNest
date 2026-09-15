import { apiClient } from './apiClient';
import type { RebalancingOverviewOut, RebalancingTargetIn } from '../types/api';

export const rebalancingService = {
  async getAllocations(goalId?: string): Promise<RebalancingOverviewOut> {
    const response = await apiClient.get<RebalancingOverviewOut>('/rebalancing/allocations', { params: goalId ? { goal_id: goalId } : {} });
    return response.data;
  },
  async setAllocations(goalId: string | undefined, targets: RebalancingTargetIn[]): Promise<RebalancingOverviewOut> {
    const response = await apiClient.put<RebalancingOverviewOut>('/rebalancing/allocations', { goal_id: goalId || null, targets });
    return response.data;
  },
};
