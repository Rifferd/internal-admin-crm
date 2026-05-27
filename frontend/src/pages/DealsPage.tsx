import { FormEvent, useEffect, useState } from "react";
import axios from "axios";

import { dealsApi } from "../api/dealsApi";
import type {
  Deal,
  DealCreateRequest,
  DealStatus,
  DealUpdateRequest,
} from "../types/deal";

const DEAL_STATUSES: DealStatus[] = ["new", "in_progress", "won", "lost"];

const DEAL_STATUS_LABELS: Record<DealStatus, string> = {
  new: "Новая",
  in_progress: "В работе",
  won: "Выиграна",
  lost: "Проиграна",
};

interface DealFormState {
  client_id: string;
  manager_id: string;
  title: string;
  amount: string;
  status: DealStatus;
}

const emptyForm: DealFormState = {
  client_id: "",
  manager_id: "",
  title: "",
  amount: "",
  status: "new",
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

function formatDate(value: string | null) {
  if (!value) {
    return "—";
  }

  return new Date(value).toLocaleDateString("ru-RU", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
}

function formatMoney(value: string) {
  return Number(value).toLocaleString("ru-RU", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export function DealsPage() {
  const [deals, setDeals] = useState<Deal[]>([]);
  const [meta, setMeta] = useState({
    page: 1,
    size: 10,
    total: 0,
    pages: 0,
  });

  const [status, setStatus] = useState<DealStatus | "">("");
  const [clientId, setClientId] = useState("");
  const [managerId, setManagerId] = useState("");

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingDeal, setEditingDeal] = useState<Deal | null>(null);
  const [form, setForm] = useState<DealFormState>(emptyForm);

  async function loadDeals(page = meta.page) {
    try {
      setIsLoading(true);
      setError(null);

      const data = await dealsApi.list({
        status,
        client_id: clientId ? Number(clientId) : "",
        manager_id: managerId ? Number(managerId) : "",
        page,
        size: meta.size,
      });

      setDeals(data.items);
      setMeta(data.meta);
    } catch (error) {
      setError(getErrorMessage(error, "Не удалось загрузить сделки."));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadDeals(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function openCreateModal() {
    setEditingDeal(null);
    setForm(emptyForm);
    setError(null);
    setIsModalOpen(true);
  }

  function openEditModal(deal: Deal) {
    setEditingDeal(deal);
    setForm({
      client_id: String(deal.client_id),
      manager_id: String(deal.manager_id),
      title: deal.title,
      amount: deal.amount,
      status: deal.status,
    });
    setError(null);
    setIsModalOpen(true);
  }

  function closeModal() {
    if (isSaving) {
      return;
    }

    setIsModalOpen(false);
    setEditingDeal(null);
    setForm(emptyForm);
  }

  async function handleFilterSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await loadDeals(1);
  }

  async function handleSubmitDeal(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!form.client_id.trim()) {
      setError("Введите client_id.");
      return;
    }

    if (!form.title.trim()) {
      setError("Введите название сделки.");
      return;
    }

    if (!form.amount.trim() || Number(form.amount) <= 0) {
      setError("Введите сумму сделки больше 0.");
      return;
    }

    const payload: DealCreateRequest = {
      client_id: Number(form.client_id),
      manager_id: form.manager_id ? Number(form.manager_id) : null,
      title: form.title.trim(),
      amount: form.amount,
      status: form.status,
    };

    try {
      setIsSaving(true);
      setError(null);

      if (editingDeal) {
        await dealsApi.update(editingDeal.id, payload as DealUpdateRequest);
      } else {
        await dealsApi.create(payload);
      }

      closeModal();
      await loadDeals(editingDeal ? meta.page : 1);
    } catch (error) {
      setError(getErrorMessage(error, "Не удалось сохранить сделку."));
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDeleteDeal(deal: Deal) {
    const confirmed = window.confirm(`Удалить сделку "${deal.title}"?`);

    if (!confirmed) {
      return;
    }

    try {
      setError(null);
      await dealsApi.delete(deal.id);
      await loadDeals(meta.page);
    } catch (error) {
      setError(getErrorMessage(error, "Не удалось удалить сделку."));
    }
  }

  return (
    <main className="page">
      <div className="page-header">
        <div>
          <p className="page-kicker">Sales</p>
          <h1>Сделки</h1>
          <p>Создание, фильтрация и управление сделками.</p>
        </div>

        <button className="primary-button" type="button" onClick={openCreateModal}>
          Добавить сделку
        </button>
      </div>

      <section className="panel">
        <form className="filters-row deals-filters" onSubmit={handleFilterSubmit}>
          <label className="filter-field">
            <span>Статус</span>
            <select
              value={status}
              onChange={(event) => setStatus(event.target.value as DealStatus | "")}
            >
              <option value="">Все статусы</option>
              {DEAL_STATUSES.map((item) => (
                <option key={item} value={item}>
                  {DEAL_STATUS_LABELS[item]}
                </option>
              ))}
            </select>
          </label>

          <label className="filter-field">
            <span>Client ID</span>
            <input
              type="number"
              min="1"
              value={clientId}
              placeholder="Например: 1"
              onChange={(event) => setClientId(event.target.value)}
            />
          </label>

          <label className="filter-field">
            <span>Manager ID</span>
            <input
              type="number"
              min="1"
              value={managerId}
              placeholder="Например: 2"
              onChange={(event) => setManagerId(event.target.value)}
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
          <div className="state-card">Загрузка сделок...</div>
        ) : deals.length === 0 ? (
          <div className="empty-state">Сделок пока нет.</div>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Название</th>
                  <th>Client ID</th>
                  <th>Manager ID</th>
                  <th>Сумма</th>
                  <th>Статус</th>
                  <th>Создана</th>
                  <th>Закрыта</th>
                  <th>Действия</th>
                </tr>
              </thead>

              <tbody>
                {deals.map((deal) => (
                  <tr key={deal.id}>
                    <td>{deal.id}</td>
                    <td>{deal.title}</td>
                    <td>{deal.client_id}</td>
                    <td>{deal.manager_id}</td>
                    <td>{formatMoney(deal.amount)} сом</td>
                    <td>
                      <span className={`status-badge status-deal-${deal.status}`}>
                        {DEAL_STATUS_LABELS[deal.status]}
                      </span>
                    </td>
                    <td>{formatDate(deal.created_at)}</td>
                    <td>{formatDate(deal.closed_at)}</td>
                    <td>
                      <div className="table-actions">
                        <button
                          className="link-button"
                          type="button"
                          onClick={() => openEditModal(deal)}
                        >
                          Изменить
                        </button>

                        <button
                          className="danger-button"
                          type="button"
                          onClick={() => handleDeleteDeal(deal)}
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
              onClick={() => loadDeals(meta.page - 1)}
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
              onClick={() => loadDeals(meta.page + 1)}
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
                <h2>{editingDeal ? "Редактировать сделку" : "Новая сделка"}</h2>
                <p>
                  {editingDeal
                    ? "Измени данные сделки."
                    : "Создай сделку для клиента."}
                </p>
              </div>

              <button className="icon-button" type="button" onClick={closeModal}>
                ×
              </button>
            </div>

            <form className="modal-form" onSubmit={handleSubmitDeal}>
              <label className="form-field">
                <span>Client ID</span>
                <input
                  type="number"
                  min="1"
                  value={form.client_id}
                  placeholder="1"
                  onChange={(event) =>
                    setForm((prev) => ({ ...prev, client_id: event.target.value }))
                  }
                />
              </label>

              <label className="form-field">
                <span>Manager ID</span>
                <input
                  type="number"
                  min="1"
                  value={form.manager_id}
                  placeholder="Можно оставить пустым"
                  onChange={(event) =>
                    setForm((prev) => ({ ...prev, manager_id: event.target.value }))
                  }
                />
              </label>

              <label className="form-field">
                <span>Название</span>
                <input
                  value={form.title}
                  placeholder="Продажа CRM"
                  onChange={(event) =>
                    setForm((prev) => ({ ...prev, title: event.target.value }))
                  }
                />
              </label>

              <label className="form-field">
                <span>Сумма</span>
                <input
                  type="number"
                  min="1"
                  step="0.01"
                  value={form.amount}
                  placeholder="50000.00"
                  onChange={(event) =>
                    setForm((prev) => ({ ...prev, amount: event.target.value }))
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
                      status: event.target.value as DealStatus,
                    }))
                  }
                >
                  {DEAL_STATUSES.map((item) => (
                    <option key={item} value={item}>
                      {DEAL_STATUS_LABELS[item]}
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