import { http } from "./http";
import type {
  Deal,
  DealCreateRequest,
  DealListResponse,
  DealStatus,
  DealUpdateRequest,
} from "../types/deal";

export interface DealListParams {
  status?: DealStatus | "";
  client_id?: number | "";
  manager_id?: number | "";
  page?: number;
  size?: number;
}

export const dealsApi = {
  async list(params: DealListParams): Promise<DealListResponse> {
    const response = await http.get<DealListResponse>("/deals", {
      params: {
        status: params.status || undefined,
        client_id: params.client_id || undefined,
        manager_id: params.manager_id || undefined,
        page: params.page,
        size: params.size,
      },
    });

    return response.data;
  },

  async getById(dealId: number): Promise<Deal> {
    const response = await http.get<Deal>(`/deals/${dealId}`);
    return response.data;
  },

  async create(data: DealCreateRequest): Promise<Deal> {
    const response = await http.post<Deal>("/deals", data);
    return response.data;
  },

  async update(dealId: number, data: DealUpdateRequest): Promise<Deal> {
    const response = await http.patch<Deal>(`/deals/${dealId}`, data);
    return response.data;
  },

  async delete(dealId: number): Promise<void> {
    await http.delete(`/deals/${dealId}`);
  },
};