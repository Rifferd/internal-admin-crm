import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

import { authApi } from "../api/authApi";
import { authStorage } from "../features/auth/authStorage";

export function LoginPage() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("admin12345");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError(null);

    if (!email.trim()) {
      setError("Введите email");
      return;
    }

    if (!password.trim()) {
      setError("Введите пароль");
      return;
    }

    try {
      setIsLoading(true);

      const tokens = await authApi.login({
        email,
        password,
      });

      authStorage.setTokens(tokens.access_token, tokens.refresh_token);

      navigate("/dashboard");
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail;

        if (typeof detail === "string") {
          setError(detail);
          return;
        }
      }

      setError("Не удалось войти. Проверь backend и данные пользователя.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-card">
        <div className="login-header">
          <p className="login-kicker">Internal Admin CRM</p>
          <h1>Вход</h1>
          <p className="login-subtitle">
            Войди в систему, чтобы управлять клиентами, сделками и задачами.
          </p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <label className="form-field">
            <span>Email</span>
            <input
              type="email"
              value={email}
              placeholder="admin@example.com"
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>

          <label className="form-field">
            <span>Пароль</span>
            <input
              type="password"
              value={password}
              placeholder="admin12345"
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>

          {error && <div className="form-error">{error}</div>}

          <button className="primary-button" type="submit" disabled={isLoading}>
            {isLoading ? "Входим..." : "Войти"}
          </button>
        </form>
      </section>
    </main>
  );
}