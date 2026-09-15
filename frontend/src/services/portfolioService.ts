import { apiClient } from './apiClient';
import type { HoldingOut, TransactionIn, TransactionResponse } from '../types/api';

export const portfolioService = {
  async getHoldings(): Promise<HoldingOut[]> {
    const response = await apiClient.get<HoldingOut[]>('/portfolio/holdings');
    return response.data;
  },

  async createTransaction(payload: TransactionIn): Promise<TransactionResponse> {
    const response = await apiClient.post<TransactionResponse>('/portfolio/transactions', payload);
    return response.data;
  },
};
