export type TaskStatus = "todo" | "in_progress" | "done" | "cancelled";

export interface Task {
  id: number;
  deal_id: number;
  assigned_to: number;
  title: string;
  description: string | null;
  deadline: string;
  status: TaskStatus;
  created_at: string;
  updated_at: string;
}

export interface TaskListResponse {
  items: Task[];
  meta: {
    page: number;
    size: number;
    total: number;
    pages: number;
  };
}

export interface TaskCreateRequest {
  deal_id: number;
  assigned_to?: number | null;
  title: string;
  description: string | null;
  deadline: string;
  status: TaskStatus;
}

export type TaskUpdateRequest = Partial<TaskCreateRequest>;