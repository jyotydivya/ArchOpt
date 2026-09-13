import { apiClient } from './client.ts';
import type {
  LayoutRunCreateRequest,
  LayoutRunCreateResponse,
  LayoutListResponse,
  LayoutSummary,
  LayoutDetail,
  LayoutSelectResponse,
} from '../types/layout.ts';
import type { Blueprint } from '../types/blueprint.ts';

export const layoutsApi = {
  createLayoutRun: async (
    projectId: number,
    payload: LayoutRunCreateRequest = { candidateCount: 100, topK: 5, algorithm: 'GNN_NSGA2' }
  ): Promise<LayoutRunCreateResponse> => {
    const response = await apiClient.post<LayoutRunCreateResponse>(
      `/api/projects/${projectId}/layout-runs`,
      payload
    );
    return response.data;
  },

  getLayouts: async (projectId: number): Promise<LayoutSummary[]> => {
    const response = await apiClient.get<LayoutListResponse>(`/api/projects/${projectId}/layouts`);
    return response.data.layouts;
  },

  getLayoutDetail: async (layoutId: number): Promise<LayoutDetail> => {
    const response = await apiClient.get<LayoutDetail>(`/api/layouts/${layoutId}`);
    return response.data;
  },

  selectLayout: async (layoutId: number): Promise<LayoutSelectResponse> => {
    const response = await apiClient.post<LayoutSelectResponse>(
      `/api/layouts/${layoutId}/select`,
      {}
    );
    return response.data;
  },

  getBlueprint: async (layoutId: number): Promise<Blueprint> => {
    const response = await apiClient.get<Blueprint>(`/api/layouts/${layoutId}/blueprint`);
    return response.data;
  },
};

export default layoutsApi;
