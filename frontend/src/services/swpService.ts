import { apiClient } from './apiClient';
import type { SWPExecutionOut, SWPPlanCreate, SWPPlanOut, SWPPlanType } from '../types/api';

export const swpService = {
  async getPlans(params?: { goal_id?: string; plan_type?: SWPPlanType }): Promise<SWPPlanOut[]> {
    const response = await apiClient.get<SWPPlanOut[]>('/swp/plans', { params });
    return response.data;
  },

  async createPlan(payload: SWPPlanCreate): Promise<SWPPlanOut> {
    const response = await apiClient.post<SWPPlanOut>('/swp/plans', payload);
    return response.data;
  },

  async executePlan(planId: string): Promise<SWPExecutionOut> {
    const response = await apiClient.post<SWPExecutionOut>(`/swp/plans/${planId}/execute`);
    return response.data;
  },
};
