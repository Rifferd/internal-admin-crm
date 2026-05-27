export interface DashboardStats {
  clients_total: number;
  clients_active: number;

  deals_total: number;
  deals_won: number;
  deals_lost: number;
  deals_open: number;
  deals_total_amount: string;
  deals_won_amount: string;

  tasks_total: number;
  tasks_overdue: number;
}