import { apiClient } from './apiClient';
import type { InAppNotificationFeed } from '../types/api';

export const notificationService = {
  async getFeed(): Promise<InAppNotificationFeed> {
    const response = await apiClient.get<InAppNotificationFeed>('/notifications/feed');
    return response.data;
  },
};
