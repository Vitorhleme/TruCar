// --- 1. IMPORTAR OS NOVOS MODELOS ---
import type { Part } from './part-models';
import type { InventoryTransaction } from './inventory-transaction-models'; // <-- Adicionado

export type InventoryItemStatus = "Disponível" | "Em Uso" | "Fim de Vida";

export interface InventoryItem {
  id: number; // Este é o "código" global (Ex: 1, 2, 3, 4...)
  
  // --- ADICIONE ESTA LINHA ---
  item_identifier: number; // Este é o "código" local (Ex: 1, 2 ... 1, 2)
  // --- FIM DA ADIÇÃO ---

  status: InventoryItemStatus;
  
  part_id: number;
  installed_on_vehicle_id: number | null;
  created_at: string;
  installed_at: string | null;
  part: Part | null; 
}

// --- 2. CRIAR A NOVA INTERFACE DE DETALHES ---
// (Corresponde ao schema InventoryItemDetails do backend)
export interface InventoryItemDetails extends InventoryItem {
  part: Part; // Em detalhes, a peça 'part' nunca será nula
  transactions: InventoryTransaction[]; // O histórico completo
}