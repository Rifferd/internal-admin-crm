import { http } from "./http";
import type { DashboardStats } from "../types/dashboard";

export const dashboardApi = {
  async getStats(): Promise<DashboardStats> {
    const response = await http.get<DashboardStats>("/dashboard/stats");
    return response.data;
  },
};