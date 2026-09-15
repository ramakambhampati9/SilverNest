import { apiClient } from './apiClient';
import type { InsuranceOverviewOut, InsurancePolicyCreate, InsurancePolicyOut } from '../types/api';

export const insuranceService = {
  async getPolicies(): Promise<InsuranceOverviewOut> {
    const response = await apiClient.get<InsuranceOverviewOut>('/insurance/policies');
    return response.data;
  },
  async createPolicy(payload: InsurancePolicyCreate): Promise<InsurancePolicyOut> {
    const response = await apiClient.post<InsurancePolicyOut>('/insurance/policies', payload);
    return response.data;
  },
  async deletePolicy(policyId: string): Promise<void> {
    await apiClient.delete(`/insurance/policies/${policyId}`);
  },
};
