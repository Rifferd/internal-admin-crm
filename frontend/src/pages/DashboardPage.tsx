import { useEffect, useState } from "react";
import axios from "axios";

import { dashboardApi } from "../api/dashboardApi";
import type { DashboardStats } from "../types/dashboard";

function formatMoney(value: string | number) {
  return Number(value).toLocaleString("ru-RU", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadStats() {
    try {
      setIsLoading(true);
      setError(null);

      const data = await dashboardApi.getStats();
      setStats(data);
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail;

        if (typeof detail === "string") {
          setError(detail);
          return;
        }
      }

      setError("Не удалось загрузить dashboard statistics.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadStats();
  }, []);

  if (isLoading) {
    return (
      <main className="page">
        <h1>Dashboard</h1>
        <div className="state-card">Загрузка статистики...</div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="page">
        <h1>Dashboard</h1>
        <div className="state-card state-card-error">{error}</div>
        <button className="primary-button" type="button" onClick={loadStats}>
          Повторить
        </button>
      </main>
    );
  }

  if (!stats) {
    return null;
  }

  return (
    <main className="page">
      <div className="page-header">
        <div>
          <p className="page-kicker">Overview</p>
          <h1>Dashboard</h1>
          <p>Краткая статистика по клиентам, сделкам и задачам.</p>
        </div>

        <button className="secondary-button" type="button" onClick={loadStats}>
          Обновить
        </button>
      </div>

      <section className="stats-grid">
        <article className="stat-card">
          <span>Всего клиентов</span>
          <strong>{stats.clients_total}</strong>
          <small>Активных: {stats.clients_active}</small>
        </article>

        <article className="stat-card">
          <span>Всего сделок</span>
          <strong>{stats.deals_total}</strong>
          <small>Открытых: {stats.deals_open}</small>
        </article>

        <article className="stat-card">
          <span>Выигранные сделки</span>
          <strong>{stats.deals_won}</strong>
          <small>Проигранных: {stats.deals_lost}</small>
        </article>

        <article className="stat-card">
          <span>Просроченные задачи</span>
          <strong>{stats.tasks_overdue}</strong>
          <small>Всего задач: {stats.tasks_total}</small>
        </article>
      </section>

      <section className="dashboard-panels">
        <article className="panel">
          <h2>Сумма всех сделок</h2>
          <p className="money-value">
            {formatMoney(stats.deals_total_amount)} сом
          </p>
        </article>

        <article className="panel">
          <h2>Сумма выигранных сделок</h2>
          <p className="money-value">{formatMoney(stats.deals_won_amount)} сом</p>
        </article>
      </section>
    </main>
  );
}