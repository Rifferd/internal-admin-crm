import { FormEvent, useEffect, useState } from "react";
import axios from "axios";

import { tasksApi } from "../api/tasksApi";
import type {
  Task,
  TaskCreateRequest,
  TaskStatus,
  TaskUpdateRequest,
} from "../types/task";

const TASK_STATUSES: TaskStatus[] = ["todo", "in_progress", "done", "cancelled"];

const TASK_STATUS_LABELS: Record<TaskStatus, string> = {
  todo: "К выполнению",
  in_progress: "В работе",
  done: "Готово",
  cancelled: "Отменено",
};

type TaskMode = "all" | "my" | "overdue";

interface TaskFormState {
  deal_id: string;
  assigned_to: string;
  title: string;
  description: string;
  deadline: string;
  status: TaskStatus;
}

const emptyForm: TaskFormState = {
  deal_id: "",
  assigned_to: "",
  title: "",
  description: "",
  deadline: "",
  status: "todo",
};

function getErrorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;

    if (typeof detail === "string") {
      return detail;
    }
  }

  return fallback;
}

function toNullable(value: string) {
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

function toBackendDateTime(value: string) {
  return new Date(value).toISOString();
}

function toDateTimeLocalValue(value: string) {
  const date = new Date(value);
  const timezoneOffset = date.getTimezoneOffset() * 60000;
  const localDate = new Date(date.getTime() - timezoneOffset);

  return localDate.toISOString().slice(0, 16);
}

function formatDateTime(value: string) {
  return new Date(value).toLocaleString("ru-RU", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function isOverdue(task: Task) {
  const deadline = new Date(task.deadline).getTime();
  const now = Date.now();

  return (
    deadline < now &&
    task.status !== "done" &&
    task.status !== "cancelled"
  );
}

export function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [meta, setMeta] = useState({
    page: 1,
    size: 10,
    total: 0,
    pages: 0,
  });

  const [mode, setMode] = useState<TaskMode>("all");
  const [status, setStatus] = useState<TaskStatus | "">("");
  const [dealId, setDealId] = useState("");
  const [assignedTo, setAssignedTo] = useState("");

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [form, setForm] = useState<TaskFormState>(emptyForm);

  async function loadTasks(page = meta.page, nextMode = mode) {
    try {
      setIsLoading(true);
      setError(null);

      let data;

      if (nextMode === "my") {
        data = await tasksApi.my({
          status,
          page,
          size: meta.size,
        });
      } else if (nextMode === "overdue") {
        data = await tasksApi.overdue({
          page,
          size: meta.size,
        });
      } else {
        data = await tasksApi.list({
          status,
          deal_id: dealId ? Number(dealId) : "",
          assigned_to: assignedTo ? Number(assignedTo) : "",
          page,
          size: meta.size,
        });
      }

      setTasks(data.items);
      setMeta(data.meta);
    } catch (error) {
      setError(getErrorMessage(error, "Не удалось загрузить задачи."));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadTasks(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function changeMode(nextMode: TaskMode) {
    setMode(nextMode);
    await loadTasks(1, nextMode);
  }

  function openCreateModal() {
    setEditingTask(null);
    setForm(emptyForm);
    setError(null);
    setIsModalOpen(true);
  }

  function openEditModal(task: Task) {
    setEditingTask(task);
    setForm({
      deal_id: String(task.deal_id),
      assigned_to: String(task.assigned_to),
      title: task.title,
      description: task.description ?? "",
      deadline: toDateTimeLocalValue(task.deadline),
      status: task.status,
    });
    setError(null);
    setIsModalOpen(true);
  }

  function closeModal() {
    if (isSaving) {
      return;
    }

    setIsModalOpen(false);
    setEditingTask(null);
    setForm(emptyForm);
  }

  async function handleFilterSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await loadTasks(1);
  }

  async function handleSubmitTask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!form.deal_id.trim()) {
      setError("Введите deal_id.");
      return;
    }

    if (!form.title.trim()) {
      setError("Введите название задачи.");
      return;
    }

    if (!form.deadline.trim()) {
      setError("Укажите дедлайн.");
      return;
    }

    const payload: TaskCreateRequest = {
      deal_id: Number(form.deal_id),
      assigned_to: form.assigned_to ? Number(form.assigned_to) : null,
      title: form.title.trim(),
      description: toNullable(form.description),
      deadline: toBackendDateTime(form.deadline),
      status: form.status,
    };

    try {
      setIsSaving(true);
      setError(null);

      if (editingTask) {
        await tasksApi.update(editingTask.id, payload as TaskUpdateRequest);
      } else {
        await tasksApi.create(payload);
      }

      closeModal();
      await loadTasks(editingTask ? meta.page : 1);
    } catch (error) {
      setError(getErrorMessage(error, "Не удалось сохранить задачу."));
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDeleteTask(task: Task) {
    const confirmed = window.confirm(`Удалить задачу "${task.title}"?`);

    if (!confirmed) {
      return;
    }

    try {
      setError(null);
      await tasksApi.delete(task.id);
      await loadTasks(meta.page);
    } catch (error) {
      setError(getErrorMessage(error, "Не удалось удалить задачу."));
    }
  }

  return (
    <main className="page">
      <div className="page-header">
        <div>
          <p className="page-kicker">Workload</p>
          <h1>Задачи</h1>
          <p>Создание, фильтрация и контроль дедлайнов по задачам.</p>
        </div>

        <button className="primary-button" type="button" onClick={openCreateModal}>
          Добавить задачу
        </button>
      </div>

      <section className="panel">
        <div className="tabs-row">
          <button
            className={mode === "all" ? "tab-button active" : "tab-button"}
            type="button"
            onClick={() => changeMode("all")}
          >
            Все задачи
          </button>

          <button
            className={mode === "my" ? "tab-button active" : "tab-button"}
            type="button"
            onClick={() => changeMode("my")}
          >
            Мои задачи
          </button>

          <button
            className={mode === "overdue" ? "tab-button active" : "tab-button"}
            type="button"
            onClick={() => changeMode("overdue")}
          >
            Просроченные
          </button>
        </div>

        <form className="filters-row tasks-filters" onSubmit={handleFilterSubmit}>
          <label className="filter-field">
            <span>Статус</span>
            <select
              value={status}
              disabled={mode === "overdue"}
              onChange={(event) => setStatus(event.target.value as TaskStatus | "")}
            >
              <option value="">Все статусы</option>
              {TASK_STATUSES.map((item) => (
                <option key={item} value={item}>
                  {TASK_STATUS_LABELS[item]}
                </option>
              ))}
            </select>
          </label>

          <label className="filter-field">
            <span>Deal ID</span>
            <input
              type="number"
              min="1"
              value={dealId}
              disabled={mode !== "all"}
              placeholder="Например: 1"
              onChange={(event) => setDealId(event.target.value)}
            />
          </label>

          <label className="filter-field">
            <span>Assigned to</span>
            <input
              type="number"
              min="1"
              value={assignedTo}
              disabled={mode !== "all"}
              placeholder="User ID"
              onChange={(event) => setAssignedTo(event.target.value)}
            />
          </label>

          <button className="secondary-button" type="submit">
            Применить
          </button>
        </form>
      </section>

      {error && <div className="state-card state-card-error">{error}</div>}

      <section className="panel table-panel">
        {isLoading ? (
          <div className="state-card">Загрузка задач...</div>
        ) : tasks.length === 0 ? (
          <div className="empty-state">Задач пока нет.</div>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Задача</th>
                  <th>Deal ID</th>
                  <th>Assigned to</th>
                  <th>Дедлайн</th>
                  <th>Статус</th>
                  <th>Действия</th>
                </tr>
              </thead>

              <tbody>
                {tasks.map((task) => (
                  <tr key={task.id}>
                    <td>{task.id}</td>
                    <td>
                      <div className="muted-stack">
                        <strong>{task.title}</strong>
                        <span>{task.description || "—"}</span>
                      </div>
                    </td>
                    <td>{task.deal_id}</td>
                    <td>{task.assigned_to}</td>
                    <td>
                      <span className={isOverdue(task) ? "deadline-overdue" : ""}>
                        {formatDateTime(task.deadline)}
                      </span>
                    </td>
                    <td>
                      <span className={`status-badge status-task-${task.status}`}>
                        {TASK_STATUS_LABELS[task.status]}
                      </span>
                    </td>
                    <td>
                      <div className="table-actions">
                        <button
                          className="link-button"
                          type="button"
                          onClick={() => openEditModal(task)}
                        >
                          Изменить
                        </button>

                        <button
                          className="danger-button"
                          type="button"
                          onClick={() => handleDeleteTask(task)}
                        >
                          Удалить
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="pagination-row">
          <span>
            Всего: <strong>{meta.total}</strong>
          </span>

          <div className="pagination-actions">
            <button
              className="secondary-button"
              type="button"
              disabled={meta.page <= 1 || isLoading}
              onClick={() => loadTasks(meta.page - 1)}
            >
              Назад
            </button>

            <span>
              {meta.page} / {meta.pages || 1}
            </span>

            <button
              className="secondary-button"
              type="button"
              disabled={meta.page >= meta.pages || isLoading}
              onClick={() => loadTasks(meta.page + 1)}
            >
              Вперед
            </button>
          </div>
        </div>
      </section>

      {isModalOpen && (
        <div className="modal-backdrop" onMouseDown={closeModal}>
          <div className="modal-card" onMouseDown={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h2>{editingTask ? "Редактировать задачу" : "Новая задача"}</h2>
                <p>
                  {editingTask
                    ? "Измени данные задачи."
                    : "Создай задачу по сделке."}
                </p>
              </div>

              <button className="icon-button" type="button" onClick={closeModal}>
                ×
              </button>
            </div>

            <form className="modal-form" onSubmit={handleSubmitTask}>
              <label className="form-field">
                <span>Deal ID</span>
                <input
                  type="number"
                  min="1"
                  value={form.deal_id}
                  placeholder="1"
                  onChange={(event) =>
                    setForm((prev) => ({ ...prev, deal_id: event.target.value }))
                  }
                />
              </label>

              <label className="form-field">
                <span>Assigned to</span>
                <input
                  type="number"
                  min="1"
                  value={form.assigned_to}
                  placeholder="Можно оставить пустым"
                  onChange={(event) =>
                    setForm((prev) => ({ ...prev, assigned_to: event.target.value }))
                  }
                />
              </label>

              <label className="form-field">
                <span>Название</span>
                <input
                  value={form.title}
                  placeholder="Позвонить клиенту"
                  onChange={(event) =>
                    setForm((prev) => ({ ...prev, title: event.target.value }))
                  }
                />
              </label>

              <label className="form-field">
                <span>Описание</span>
                <textarea
                  value={form.description}
                  placeholder="Уточнить детали сделки"
                  onChange={(event) =>
                    setForm((prev) => ({ ...prev, description: event.target.value }))
                  }
                />
              </label>

              <label className="form-field">
                <span>Дедлайн</span>
                <input
                  type="datetime-local"
                  value={form.deadline}
                  onChange={(event) =>
                    setForm((prev) => ({ ...prev, deadline: event.target.value }))
                  }
                />
              </label>

              <label className="form-field">
                <span>Статус</span>
                <select
                  value={form.status}
                  onChange={(event) =>
                    setForm((prev) => ({
                      ...prev,
                      status: event.target.value as TaskStatus,
                    }))
                  }
                >
                  {TASK_STATUSES.map((item) => (
                    <option key={item} value={item}>
                      {TASK_STATUS_LABELS[item]}
                    </option>
                  ))}
                </select>
              </label>

              <div className="modal-actions">
                <button className="secondary-button" type="button" onClick={closeModal}>
                  Отмена
                </button>

                <button className="primary-button" type="submit" disabled={isSaving}>
                  {isSaving ? "Сохраняем..." : "Сохранить"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
}