export type DealStatus = "new" | "in_progress" | "won" | "lost";

export interface Deal {
  id: number;
  client_id: number;
  manager_id: number;
  title: string;
  amount: string;
  status: DealStatus;
  created_at: string;
  closed_at: string | null;
}

export interface DealListResponse {
  items: Deal[];
  meta: {
    page: number;
    size: number;
    total: number;
    pages: number;
  };
}

export interface DealCreateRequest {
  client_id: number;
  manager_id?: number | null;
  title: string;
  amount: string;
  status: DealStatus;
}

export type DealUpdateRequest = Partial<DealCreateRequest>;