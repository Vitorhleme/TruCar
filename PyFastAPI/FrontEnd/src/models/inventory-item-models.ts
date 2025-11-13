// --- 1. IMPORTAR O MODELO DE PEÇA ---
import type { Part } from './part-models';

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
 // --- 2. ADICIONAR A PEÇA ANINHADA ---
 part: Part | null; // A API provavelmente aninha a peça aqui
}