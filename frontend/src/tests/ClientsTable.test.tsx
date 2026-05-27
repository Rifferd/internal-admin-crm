import { render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { clientsApi } from "../api/clientsApi";
import { ClientsPage } from "../pages/ClientsPage";

vi.mock("../api/clientsApi", () => ({
  clientsApi: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    getById: vi.fn(),
  },
}));

describe("ClientsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(clientsApi.list).mockResolvedValue({
      items: [
        {
          id: 1,
          name: "ОсОО Альфа",
          phone: "+996700111222",
          email: "alpha@example.com",
          source: "instagram",
          status: "lead",
          created_at: "2026-05-27T10:00:00Z",
          updated_at: "2026-05-27T10:00:00Z",
          deleted_at: null,
        },
      ],
      meta: {
        page: 1,
        size: 10,
        total: 1,
        pages: 1,
      },
    });
  });

  it("renders clients table", async () => {
    render(
      <MemoryRouter>
        <ClientsPage />
      </MemoryRouter>,
    );

    expect(screen.getByText("Загрузка клиентов...")).toBeInTheDocument();

    expect(await screen.findByText("ОсОО Альфа")).toBeInTheDocument();
    expect(screen.getByText("+996700111222")).toBeInTheDocument();
    expect(screen.getByText("alpha@example.com")).toBeInTheDocument();
    expect(screen.getByText("instagram")).toBeInTheDocument();
    const row = screen.getByRole("row", { name: /ОсОО Альфа/i });

    expect(within(row).getByText("Лид")).toBeInTheDocument();

    await waitFor(() => {
      expect(clientsApi.list).toHaveBeenCalledWith({
        search: "",
        status: "",
        page: 1,
        size: 10,
      });
    });
  });

  it("shows empty state when there are no clients", async () => {
    vi.mocked(clientsApi.list).mockResolvedValueOnce({
      items: [],
      meta: {
        page: 1,
        size: 10,
        total: 0,
        pages: 0,
      },
    });

    render(
      <MemoryRouter>
        <ClientsPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Клиентов пока нет.")).toBeInTheDocument();
  });
});