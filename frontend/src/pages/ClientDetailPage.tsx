import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import axios from "axios";

import { clientsApi } from "../api/clientsApi";
import { dealsApi } from "../api/dealsApi";
import type { Client, ClientStatus } from "../types/client";
import type { Deal, DealStatus } from "../types/deal";

const CLIENT_STATUS_LABELS: Record<ClientStatus, string> = {
  lead: "Лид",
  active: "Активный",
  inactive: "Неактивный",
  archived: "Архив",
};

const DEAL_STATUS_LABELS: Record<DealStatus, string> = {
  new: "Новая",
  in_progress: "В работе",
  won: "Выиграна",
  lost: "Проиграна",
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

export function ClientDetailPage() {
  const params = useParams();

  const clientId = Number(params.id);

  const [client, setClient] = useState<Client | null>(null);
  const [deals, setDeals] = useState<Deal[]>([]);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadClientDetail() {
    if (!clientId || Number.isNaN(clientId)) {
      setError("Некорректный ID клиента.");
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const [clientData, dealsData] = await Promise.all([
        clientsApi.getById(clientId),
        dealsApi.list({
          client_id: clientId,
          page: 1,
          size: 20,
        }),
      ]);

      setClient(clientData);
      setDeals(dealsData.items);
    } catch (error) {
      setError(getErrorMessage(error, "Не удалось загрузить клиента."));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadClientDetail();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clientId]);

  if (isLoading) {
    return (
      <main className="page">
        <h1>Клиент</h1>
        <div className="state-card">Загрузка клиента...</div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="page">
        <div className="page-header">
          <div>
            <p className="page-kicker">CRM</p>
            <h1>Клиент</h1>
          </div>

          <Link className="secondary-button link-as-button" to="/clients">
            Назад к клиентам
          </Link>
        </div>

        <div className="state-card state-card-error">{error}</div>

        <button className="primary-button" type="button" onClick={loadClientDetail}>
          Повторить
        </button>
      </main>
    );
  }

  if (!client) {
    return null;
  }

  return (
    <main className="page">
      <div className="page-header">
        <div>
          <p className="page-kicker">Client profile</p>
          <h1>{client.name}</h1>
          <p>Карточка клиента и связанные сделки.</p>
        </div>

        <Link className="secondary-button link-as-button" to="/clients">
          Назад к клиентам
        </Link>
      </div>

      <section className="detail-grid">
        <article className="panel">
          <h2>Данные клиента</h2>

          <dl className="info-list">
            <div>
              <dt>ID</dt>
              <dd>{client.id}</dd>
            </div>

            <div>
              <dt>Название</dt>
              <dd>{client.name}</dd>
            </div>

            <div>
              <dt>Телефон</dt>
              <dd>{client.phone || "—"}</dd>
            </div>

            <div>
              <dt>Email</dt>
              <dd>{client.email || "—"}</dd>
            </div>

            <div>
              <dt>Источник</dt>
              <dd>{client.source || "—"}</dd>
            </div>

            <div>
              <dt>Статус</dt>
              <dd>
                <span className={`status-badge status-${client.status}`}>
                  {CLIENT_STATUS_LABELS[client.status]}
                </span>
              </dd>
            </div>

            <div>
              <dt>Создан</dt>
              <dd>{formatDate(client.created_at)}</dd>
            </div>

            <div>
              <dt>Обновлен</dt>
              <dd>{formatDate(client.updated_at)}</dd>
            </div>
          </dl>
        </article>

        <article className="panel">
          <h2>Кратко по сделкам</h2>

          <div className="summary-list">
            <div>
              <span>Всего сделок</span>
              <strong>{deals.length}</strong>
            </div>

            <div>
              <span>Выиграно</span>
              <strong>{deals.filter((deal) => deal.status === "won").length}</strong>
            </div>

            <div>
              <span>В работе</span>
              <strong>
                {
                  deals.filter(
                    (deal) =>
                      deal.status === "new" || deal.status === "in_progress",
                  ).length
                }
              </strong>
            </div>
          </div>
        </article>
      </section>

      <section className="panel table-panel">
        <div className="section-header">
          <div>
            <h2>Сделки клиента</h2>
            <p>Последние 20 сделок, привязанные к этому клиенту.</p>
          </div>

          <Link className="secondary-button link-as-button" to="/deals">
            Все сделки
          </Link>
        </div>

        {deals.length === 0 ? (
          <div className="empty-state">У клиента пока нет сделок.</div>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Название</th>
                  <th>Сумма</th>
                  <th>Статус</th>
                  <th>Создана</th>
                  <th>Закрыта</th>
                </tr>
              </thead>

              <tbody>
                {deals.map((deal) => (
                  <tr key={deal.id}>
                    <td>{deal.id}</td>
                    <td>{deal.title}</td>
                    <td>{formatMoney(deal.amount)} сом</td>
                    <td>
                      <span className={`status-badge status-deal-${deal.status}`}>
                        {DEAL_STATUS_LABELS[deal.status]}
                      </span>
                    </td>
                    <td>{formatDate(deal.created_at)}</td>
                    <td>{formatDate(deal.closed_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}