import { apiClient } from './client.ts';
import type {
  Building,
  BuildingCreateRequest,
  BuildingListResponse,
} from '../types/building.ts';

export const buildingsApi = {
  getBuildings: async (projectId: number): Promise<Building[]> => {
    const response = await apiClient.get<BuildingListResponse>(`/api/projects/${projectId}/buildings`);
    return response.data.buildings;
  },

  createBuilding: async (
    projectId: number,
    payload: BuildingCreateRequest
  ): Promise<Building> => {
    const response = await apiClient.post<Building>(
      `/api/projects/${projectId}/buildings`,
      payload
    );
    return response.data;
  },
};

export default buildingsApi;
