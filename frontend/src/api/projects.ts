import { apiClient } from './client.ts';
import type {
  Project,
  ProjectCreateRequest,
  ProjectUpdateRequest,
} from '../types/project.ts';

export const projectsApi = {
  createProject: async (payload: ProjectCreateRequest): Promise<Project> => {
    const response = await apiClient.post<Project>('/api/projects', payload);
    return response.data;
  },

  getProject: async (projectId: number): Promise<Project> => {
    const response = await apiClient.get<Project>(`/api/projects/${projectId}`);
    return response.data;
  },

  updateProject: async (projectId: number, payload: ProjectUpdateRequest): Promise<Project> => {
    const response = await apiClient.put<Project>(`/api/projects/${projectId}`, payload);
    return response.data;
  },

  deleteProject: async (projectId: number): Promise<void> => {
    await apiClient.delete(`/api/projects/${projectId}`);
  },
};

export default projectsApi;
