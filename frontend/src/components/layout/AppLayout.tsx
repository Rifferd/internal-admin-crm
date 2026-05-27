import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { authApi } from "../../api/authApi";
import { authStorage } from "../../features/auth/authStorage";

export function AppLayout() {
  const navigate = useNavigate();

  async function handleLogout() {
    const refreshToken = authStorage.getRefreshToken();

    try {
      if (refreshToken) {
        await authApi.logout(refreshToken);
      }
    } finally {
      authStorage.clearTokens();
      navigate("/login");
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <span className="logo-mark">CRM</span>
          <div>
            <strong>Internal Admin</strong>
            <small>Management panel</small>
          </div>
        </div>

        <nav className="sidebar-nav">
          <NavLink to="/dashboard">Dashboard</NavLink>
          <NavLink to="/clients">Клиенты</NavLink>
          <NavLink to="/deals">Сделки</NavLink>
          <NavLink to="/tasks">Задачи</NavLink>
        </nav>

        <button className="logout-button" type="button" onClick={handleLogout}>
          Выйти
        </button>
      </aside>

      <div className="app-content">
        <Outlet />
      </div>
    </div>
  );
}