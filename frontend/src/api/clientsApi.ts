import { http } from "./http";
import type {
  Client,
  ClientCreateRequest,
  ClientListResponse,
  ClientStatus,
  ClientUpdateRequest,
} from "../types/client";

export interface ClientListParams {
  search?: string;
  status?: ClientStatus | "";
  page?: number;
  size?: number;
}

export const clientsApi = {
  async list(params: ClientListParams): Promise<ClientListResponse> {
    const response = await http.get<ClientListResponse>("/clients", {
      params: {
        search: params.search || undefined,
        status: params.status || undefined,
        page: params.page,
        size: params.size,
      },
    });

    return response.data;
  },

  async getById(clientId: number): Promise<Client> {
    const response = await http.get<Client>(`/clients/${clientId}`);
    return response.data;
  },

  async create(data: ClientCreateRequest): Promise<Client> {
    const response = await http.post<Client>("/clients", data);
    return response.data;
  },

  async update(clientId: number, data: ClientUpdateRequest): Promise<Client> {
    const response = await http.patch<Client>(`/clients/${clientId}`, data);
    return response.data;
  },

  async delete(clientId: number): Promise<void> {
    await http.delete(`/clients/${clientId}`);
  },
};