export type InventoryItemStatus = "Disponível" | "Em Uso" | "Fim de Vida";

export interface InventoryItem {
  id: number; // Este é o "código"
  status: InventoryItemStatus;
  part_id: number;
  installed_on_vehicle_id: number | null;
  created_at: string;
  installed_at: string | null;
}