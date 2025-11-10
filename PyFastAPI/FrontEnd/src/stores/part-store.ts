import { defineStore } from 'pinia';
import { api } from 'boot/axios';
import { Notify } from 'quasar';
import { isAxiosError } from 'axios';
// --- 1. IMPORTAR 'PartCreate' ---
import type { Part, PartCreate } from 'src/models/part-models';
import type { InventoryTransaction } from 'src/models/inventory-transaction-models';
import type { InventoryItem, InventoryItemStatus } from 'src/models/inventory-item-models';

// --- 2. BASEAR O PAYLOAD EM 'PartCreate' ---
export interface PartCreatePayload extends PartCreate {
  photo_file?: File | null;
  invoice_file?: File | null;
}

export const usePartStore = defineStore('part', {
  state: () => ({
    parts: [] as Part[],
    selectedPartHistory: [] as InventoryTransaction[],
    availableItems: [] as InventoryItem[], 
    
    isLoading: false,
    isHistoryLoading: false,
    isItemsLoading: false,
  }),

  actions: {
    // ... (fetchParts, createPart, updatePart, deletePart... sem mudanças) ...
    async fetchParts(searchQuery: string | null = null) {
      this.isLoading = true;
      try {
        const params = searchQuery ? { search: searchQuery } : {};
        const response = await api.get<Part[]>('/parts/', { params });
        this.parts = response.data;
      } catch {
        Notify.create({ type: 'negative', message: 'Falha ao carregar as peças do inventário.' });
      } finally {
        this.isLoading = false;
      }
    },

    async createPart(payload: PartCreatePayload): Promise<boolean> {
      this.isLoading = true;
      try {
          const formData = new FormData();
          Object.entries(payload).forEach(([key, value]) => {
              if (key !== 'photo_file' && key !== 'invoice_file' && key !== 'stock' && value !== null && value !== undefined) {
                  formData.append(key, String(value));
              }
          });
          if (payload.photo_file) {
              formData.append('file', payload.photo_file);
          }
          if (payload.invoice_file) {
              formData.append('invoice_file', payload.invoice_file);
          }
          
          await api.post('/parts/', formData, {
              headers: { 'Content-Type': 'multipart/form-data' },
          });
          Notify.create({ type: 'positive', message: 'Peça adicionada com sucesso!' });
          await this.fetchParts();
          return true;
      } catch (error) {
          const message = isAxiosError(error) ? error.response?.data?.detail : 'Erro ao adicionar peça.';
          Notify.create({ type: 'negative', message: message as string });
          return false;
      } finally {
          this.isLoading = false;
      }
    },

    async updatePart(id: number, payload: PartCreatePayload): Promise<boolean> {
      this.isLoading = true;
      try {
          const formData = new FormData();
          Object.entries(payload).forEach(([key, value]) => {
              if (key !== 'photo_file' && key !== 'invoice_file' && key !== 'stock' && value !== null && value !== undefined) {
                  formData.append(key, String(value));
              }
          });
          if (payload.photo_file) {
              formData.append('file', payload.photo_file);
          }
          if (payload.invoice_file) {
              formData.append('invoice_file', payload.invoice_file);
          }
          
          await api.put(`/parts/${id}`, formData, {
              headers: { 'Content-Type': 'multipart/form-data' },
          });
          Notify.create({ type: 'positive', message: 'Peça atualizada com sucesso!' });
          await this.fetchParts();
          return true;
      } catch (error) {
          const message = isAxiosError(error) ? error.response?.data?.detail : 'Erro ao atualizar peça.';
          Notify.create({ type: 'negative', message: message as string });
          return false;
      } finally {
          this.isLoading = false;
      }
    },

    async deletePart(id: number) {
      this.isLoading = true;
      try {
        await api.delete(`/parts/${id}`);
        Notify.create({ type: 'positive', message: 'Peça removida com sucesso.' });
        await this.fetchParts();
      } catch {
        Notify.create({ type: 'negative', message: 'Erro ao remover a peça.' });
      } finally {
        this.isLoading = false;
      }
    },

    async addItems(partId: number, quantity: number, notes?: string): Promise<boolean> {
      this.isLoading = true;
      try {
        const payload = { quantity, notes };
        const response = await api.post<Part>(`/parts/${partId}/add-items`, payload);
        
        const index = this.parts.findIndex(p => p.id === partId);
        if (index !== -1) {
          // --- 3. CORREÇÃO DO ERRO 'possibly 'undefined'' ---
          this.parts[index]!.stock = response.data.stock;
        }
        
        Notify.create({ type: 'positive', message: `${quantity} itens adicionados com sucesso!` });
        return true;
      } catch (error) {
        const message = isAxiosError(error) ? error.response?.data?.detail : 'Erro ao adicionar itens.';
        Notify.create({ type: 'negative', message: message as string });
        return false;
      } finally {
        this.isLoading = false;
      }
    },

    async setItemStatus(partId: number, itemId: number, newStatus: InventoryItemStatus, vehicleId?: number, notes?: string): Promise<boolean> {
      this.isLoading = true;
      try {
        const payload = { new_status: newStatus, related_vehicle_id: vehicleId, notes };
        // --- 4. CORREÇÃO NA URL (estava '/parts/items/...') ---
        await api.put(`/parts/items/${itemId}/set-status`, payload);

        const index = this.parts.findIndex(p => p.id === partId);
        if (index !== -1) {
          // --- 5. CORREÇÃO DO ERRO 'possibly 'undefined'' ---
          this.parts[index]!.stock -= 1; // Decrementa o estoque local para reatividade
        }
        
        Notify.create({ type: 'positive', message: 'Status do item atualizado com sucesso!' });
        return true;
      } catch (error) {
        const message = isAxiosError(error) ? error.response?.data?.detail : 'Erro ao mudar status do item.';
        Notify.create({ type: 'negative', message: message as string });
        return false;
      } finally {
        this.isLoading = false;
      }
    },

    async fetchAvailableItems(partId: number) {
      this.isItemsLoading = true;
      this.availableItems = [];
      try {
        const response = await api.get<InventoryItem[]>(`/parts/${partId}/items`, {
          params: { status: 'Disponível' }
        });
        this.availableItems = response.data;
      } catch {
        Notify.create({ type: 'negative', message: 'Falha ao carregar itens disponíveis.' });
      } finally {
        this.isItemsLoading = false;
      }
    },

    async fetchHistory(partId: number) {
      this.isHistoryLoading = true;
      this.selectedPartHistory = [];
      try {
        const response = await api.get<InventoryTransaction[]>(`/parts/${partId}/history`);
        this.selectedPartHistory = response.data;
      } catch {
        Notify.create({ type: 'negative', message: 'Falha ao carregar o histórico do item.' });
      } finally {
        this.isHistoryLoading = false;
      }
    },
  },
});