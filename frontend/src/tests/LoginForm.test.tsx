import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { authApi } from "../api/authApi";
import { LoginPage } from "../pages/LoginPage";

vi.mock("../api/authApi", () => ({
  authApi: {
    login: vi.fn(),
  },
}));

describe("LoginPage", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it("renders login form", () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: "Вход" })).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByLabelText("Пароль")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Войти" })).toBeInTheDocument();
  });

  it("submits login form and saves tokens", async () => {
    vi.mocked(authApi.login).mockResolvedValueOnce({
      access_token: "test-access-token",
      refresh_token: "test-refresh-token",
      token_type: "bearer",
    });

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Войти" }));

    await waitFor(() => {
      expect(authApi.login).toHaveBeenCalledWith({
        email: "admin@example.com",
        password: "admin12345",
      });
    });

    expect(localStorage.getItem("access_token")).toBe("test-access-token");
    expect(localStorage.getItem("refresh_token")).toBe("test-refresh-token");
  });

  it("shows error when backend returns invalid credentials", async () => {
    vi.mocked(authApi.login).mockRejectedValueOnce({
      isAxiosError: true,
      response: {
        data: {
          detail: "Invalid email or password",
        },
      },
    });

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Войти" }));

    expect(await screen.findByText("Invalid email or password")).toBeInTheDocument();
  });
});