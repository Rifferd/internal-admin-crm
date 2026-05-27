import axios from "axios";

import { authStorage } from "../features/auth/authStorage";

export const http = axios.create({
  baseURL: "http://localhost:8000/api/v1",
});

http.interceptors.request.use((config) => {
  const token = authStorage.getAccessToken();

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});