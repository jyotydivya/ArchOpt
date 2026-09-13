export interface UserAuthSummary {
  id: number;
  name: string;
  role: string;
}

export interface UserRegisterRequest {
  name: string;
  email: string;
  password: string;
}

export interface UserRegisterResponse {
  id: number;
  name: string;
  email: string;
  role: string;
}

export interface UserLoginRequest {
  email: string;
  password: string;
}

export interface UserLoginResponse {
  accessToken: string;
  tokenType: string;
  user: UserAuthSummary;
}
