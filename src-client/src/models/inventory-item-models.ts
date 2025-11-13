// --- 1. IMPORTAR O MODELO DE PEÇA ---
import type { Part } from './part-models';

export type InventoryItemStatus = "Disponível" | "Em Uso" | "Fim de Vida";

export interface InventoryItem {
  id: number; // Este é o "código"
  status: InventoryItemStatus;
  
  part_id: number;
  installed_on_vehicle_id: number | null;
  created_at: string;
  installed_at: string | null;
  // --- 2. ADICIONAR A PEÇA ANINHADA ---
  part: Part | null; // A API provavelmente aninha a peça aqui
}