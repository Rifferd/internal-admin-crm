from decimal import Decimal

from pydantic import BaseModel


class DashboardStatsResponse(BaseModel):
    clients_total: int
    clients_active: int

    deals_total: int
    deals_won: int
    deals_lost: int
    deals_open: int
    deals_total_amount: Decimal
    deals_won_amount: Decimal

    tasks_total: int
    tasks_overdue: int