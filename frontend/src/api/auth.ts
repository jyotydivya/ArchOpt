import { apiClient } from './client.ts';
import type {
  UserLoginRequest,
  UserLoginResponse,
  UserRegisterRequest,
  UserRegisterResponse,
} from '../types/auth.ts';

export const authApi = {
  login: async (credentials: UserLoginRequest): Promise<UserLoginResponse> => {
    const response = await apiClient.post<UserLoginResponse>('/api/auth/login', credentials);
    return response.data;
  },

  register: async (data: UserRegisterRequest): Promise<UserRegisterResponse> => {
    const response = await apiClient.post<UserRegisterResponse>('/api/auth/register', data);
    return response.data;
  },
};

export default authApi;
