import { http } from "./http";
import type { User } from "../types/user";

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
}

export interface AuthUserResponse {
  user: User;
}

export const authApi = {
  async login(data: LoginRequest): Promise<TokenResponse> {
    const response = await http.post<TokenResponse>("/auth/login", data);
    return response.data;
  },

  async me(): Promise<AuthUserResponse> {
    const response = await http.get<AuthUserResponse>("/auth/me");
    return response.data;
  },

  async logout(refreshToken: string): Promise<void> {
    await http.post("/auth/logout", {
      refresh_token: refreshToken,
    });
  },
};