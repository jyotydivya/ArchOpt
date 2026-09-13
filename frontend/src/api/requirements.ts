import { apiClient } from './client.ts';
import type {
  CampusRequirements,
  RequirementsSaveRequest,
} from '../types/requirements.ts';

export const requirementsApi = {
  getRequirements: async (projectId: number): Promise<CampusRequirements> => {
    const response = await apiClient.get<CampusRequirements>(`/api/projects/${projectId}/requirements`);
    return response.data;
  },

  saveRequirements: async (
    projectId: number,
    payload: RequirementsSaveRequest
  ): Promise<CampusRequirements> => {
    const response = await apiClient.post<CampusRequirements>(
      `/api/projects/${projectId}/requirements`,
      payload
    );
    return response.data;
  },
};

export default requirementsApi;
