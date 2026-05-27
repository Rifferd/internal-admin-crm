import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";

import { clientsApi } from "../api/clientsApi";
import type {
  Client,
  ClientCreateRequest,
  ClientStatus,
  ClientUpdateRequest,
  PageMeta,
} from "../types/client";

const CLIENT_STATUSES: ClientStatus[] = ["lead", "active", "inactive", "archived"];

const STATUS_LABELS: Record<ClientStatus, string> = {
  lead: "Лид",
  active: "Активный",
  inactive: "Неактивный",
  archived: "Архив",
};

interface ClientFormState {
  name: string;
  phone: string;
  email: string;
  source: string;
  status: ClientStatus;
}

const emptyForm: ClientFormState = {
  name: "",
  phone: "",
  email: "",
  source: "",
  status: "lead",
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

function formatDate(value: string) {
  return new Date(value).toLocaleDateString("ru-RU", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
}

export function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [meta, setMeta] = useState<PageMeta>({
    page: 1,
    size: 10,
    total: 0,
    pages: 0,
  });

  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<ClientStatus | "">("");

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingClient, setEditingClient] = useState<Client | null>(null);
  const [form, setForm] = useState<ClientFormState>(emptyForm);

  async function loadClients(page = meta.page) {
    try {
      setIsLoading(true);
      setError(null);

      const data = await clientsApi.list({
        search,
        status,
        page,
        size: meta.size,
      });

      setClients(data.items);
      setMeta(data.meta);
    } catch (error) {
      setError(getErrorMessage(error, "Не удалось загрузить клиентов."));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadClients(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function openCreateModal() {
    setEditingClient(null);
    setForm(emptyForm);
    setIsModalOpen(true);
    setError(null);
  }

  function openEditModal(client: Client) {
    setEditingClient(client);
    setForm({
      name: client.name,
      phone: client.phone ?? "",
      email: client.email ?? "",
      source: client.source ?? "",
      status: client.status,
    });
    setIsModalOpen(true);
    setError(null);
  }

  function closeModal() {
    if (isSaving) {
      return;
    }

    setIsModalOpen(false);
    setEditingClient(null);
    setForm(emptyForm);
  }

  async function handleFilterSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await loadClients(1);
  }

  async function handleSubmitClient(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!form.name.trim()) {
      setError("Введите название клиента.");
      return;
    }

    const payload: ClientCreateRequest = {
      name: form.name.trim(),
      phone: toNullable(form.phone),
      email: toNullable(form.email),
      source: toNullable(form.source),
      status: form.status,
    };

    try {
      setIsSaving(true);
      setError(null);

      if (editingClient) {
        await clientsApi.update(editingClient.id, payload as ClientUpdateRequest);
      } else {
        await clientsApi.create(payload);
      }

      closeModal();
      await loadClients(editingClient ? meta.page : 1);
    } catch (error) {
      setError(getErrorMessage(error, "Не удалось сохранить клиента."));
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDeleteClient(client: Client) {
    const confirmed = window.confirm(
      `Удалить клиента "${client.name}"? Это soft delete.`,
    );

    if (!confirmed) {
      return;
    }

    try {
      setError(null);
      await clientsApi.delete(client.id);
      await loadClients(meta.page);
    } catch (error) {
      setError(getErrorMessage(error, "Не удалось удалить клиента."));
    }
  }

  return (
    <main className="page">
      <div className="page-header">
        <div>
          <p className="page-kicker">CRM</p>
          <h1>Клиенты</h1>
          <p>Поиск, фильтрация, создание и редактирование клиентов.</p>
        </div>

        <button className="primary-button" type="button" onClick={openCreateModal}>
          Добавить клиента
        </button>
      </div>

      <section className="panel">
        <form className="filters-row" onSubmit={handleFilterSubmit}>
          <label className="filter-field">
            <span>Поиск</span>
            <input
              value={search}
              placeholder="Имя, телефон или email"
              onChange={(event) => setSearch(event.target.value)}
            />
          </label>

          <label className="filter-field">
            <span>Статус</span>
            <select
              value={status}
              onChange={(event) => setStatus(event.target.value as ClientStatus | "")}
            >
              <option value="">Все статусы</option>
              {CLIENT_STATUSES.map((item) => (
                <option key={item} value={item}>
                  {STATUS_LABELS[item]}
                </option>
              ))}
            </select>
          </label>

          <button className="secondary-button" type="submit">
            Применить
          </button>
        </form>
      </section>

      {error && <div className="state-card state-card-error">{error}</div>}

      <section className="panel table-panel">
        {isLoading ? (
          <div className="state-card">Загрузка клиентов...</div>
        ) : clients.length === 0 ? (
          <div className="empty-state">Клиентов пока нет.</div>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Клиент</th>
                  <th>Контакты</th>
                  <th>Источник</th>
                  <th>Статус</th>
                  <th>Создан</th>
                  <th>Действия</th>
                </tr>
              </thead>

              <tbody>
                {clients.map((client) => (
                  <tr key={client.id}>
                    <td>{client.id}</td>
                    <td>
                      <Link className="table-link" to={`/clients/${client.id}`}>
                        {client.name}
                      </Link>
                    </td>
                    <td>
                      <div className="muted-stack">
                        <span>{client.phone || "—"}</span>
                        <span>{client.email || "—"}</span>
                      </div>
                    </td>
                    <td>{client.source || "—"}</td>
                    <td>
                      <span className={`status-badge status-${client.status}`}>
                        {STATUS_LABELS[client.status]}
                      </span>
                    </td>
                    <td>{formatDate(client.created_at)}</td>
                    <td>
                      <div className="table-actions">
                        <button
                          className="link-button"
                          type="button"
                          onClick={() => openEditModal(client)}
                        >
                          Изменить
                        </button>

                        <button
                          className="danger-button"
                          type="button"
                          onClick={() => handleDeleteClient(client)}
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
              onClick={() => loadClients(meta.page - 1)}
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
              onClick={() => loadClients(meta.page + 1)}
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
                <h2>{editingClient ? "Редактировать клиента" : "Новый клиент"}</h2>
                <p>
                  {editingClient
                    ? "Измени данные клиента."
                    : "Заполни данные нового клиента."}
                </p>
              </div>

              <button className="icon-button" type="button" onClick={closeModal}>
                ×
              </button>
            </div>

            <form className="modal-form" onSubmit={handleSubmitClient}>
              <label className="form-field">
                <span>Название</span>
                <input
                  value={form.name}
                  placeholder="ОсОО Альфа"
                  onChange={(event) =>
                    setForm((prev) => ({ ...prev, name: event.target.value }))
                  }
                />
              </label>

              <label className="form-field">
                <span>Телефон</span>
                <input
                  value={form.phone}
                  placeholder="+996700111222"
                  onChange={(event) =>
                    setForm((prev) => ({ ...prev, phone: event.target.value }))
                  }
                />
              </label>

              <label className="form-field">
                <span>Email</span>
                <input
                  type="email"
                  value={form.email}
                  placeholder="client@example.com"
                  onChange={(event) =>
                    setForm((prev) => ({ ...prev, email: event.target.value }))
                  }
                />
              </label>

              <label className="form-field">
                <span>Источник</span>
                <input
                  value={form.source}
                  placeholder="website / instagram / referral"
                  onChange={(event) =>
                    setForm((prev) => ({ ...prev, source: event.target.value }))
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
                      status: event.target.value as ClientStatus,
                    }))
                  }
                >
                  {CLIENT_STATUSES.map((item) => (
                    <option key={item} value={item}>
                      {STATUS_LABELS[item]}
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