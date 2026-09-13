import { apiClient } from './client.ts';
import type {
  Constraint,
  ConstraintCreateRequest,
  ConstraintListResponse,
} from '../types/constraint.ts';

export const constraintsApi = {
  getConstraints: async (projectId: number): Promise<Constraint[]> => {
    const response = await apiClient.get<ConstraintListResponse>(`/api/projects/${projectId}/constraints`);
    return response.data.constraints;
  },

  createConstraint: async (
    projectId: number,
    payload: ConstraintCreateRequest
  ): Promise<Constraint> => {
    const response = await apiClient.post<Constraint>(
      `/api/projects/${projectId}/constraints`,
      payload
    );
    return response.data;
  },
};

export default constraintsApi;
