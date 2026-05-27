export type ClientStatus = "lead" | "active" | "inactive" | "archived";

export interface Client {
  id: number;
  name: string;
  phone: string | null;
  email: string | null;
  source: string | null;
  status: ClientStatus;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

export interface PageMeta {
  page: number;
  size: number;
  total: number;
  pages: number;
}

export interface ClientListResponse {
  items: Client[];
  meta: PageMeta;
}

export interface ClientCreateRequest {
  name: string;
  phone: string | null;
  email: string | null;
  source: string | null;
  status: ClientStatus;
}

export type ClientUpdateRequest = Partial<ClientCreateRequest>;