import { http } from "./http";
import type {
  Task,
  TaskCreateRequest,
  TaskListResponse,
  TaskStatus,
  TaskUpdateRequest,
} from "../types/task";

export interface TaskListParams {
  status?: TaskStatus | "";
  deal_id?: number | "";
  assigned_to?: number | "";
  page?: number;
  size?: number;
}

export const tasksApi = {
  async list(params: TaskListParams): Promise<TaskListResponse> {
    const response = await http.get<TaskListResponse>("/tasks", {
      params: {
        status: params.status || undefined,
        deal_id: params.deal_id || undefined,
        assigned_to: params.assigned_to || undefined,
        page: params.page,
        size: params.size,
      },
    });

    return response.data;
  },

  async my(params: {
    status?: TaskStatus | "";
    page?: number;
    size?: number;
  }): Promise<TaskListResponse> {
    const response = await http.get<TaskListResponse>("/tasks/my", {
      params: {
        status: params.status || undefined,
        page: params.page,
        size: params.size,
      },
    });

    return response.data;
  },

  async overdue(params: {
    page?: number;
    size?: number;
  }): Promise<TaskListResponse> {
    const response = await http.get<TaskListResponse>("/tasks/overdue", {
      params: {
        page: params.page,
        size: params.size,
      },
    });

    return response.data;
  },

  async getById(taskId: number): Promise<Task> {
    const response = await http.get<Task>(`/tasks/${taskId}`);
    return response.data;
  },

  async create(data: TaskCreateRequest): Promise<Task> {
    const response = await http.post<Task>("/tasks", data);
    return response.data;
  },

  async update(taskId: number, data: TaskUpdateRequest): Promise<Task> {
    const response = await http.patch<Task>(`/tasks/${taskId}`, data);
    return response.data;
  },

  async delete(taskId: number): Promise<void> {
    await http.delete(`/tasks/${taskId}`);
  },
};