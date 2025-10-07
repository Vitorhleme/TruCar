import { defineStore } from 'pinia';
import { Dark } from 'quasar';
import { ref } from 'vue';
import { api } from 'boot/axios';
import { Notify } from 'quasar';
import type { OrganizationFuelIntegrationPublic, OrganizationFuelIntegrationUpdate } from 'src/models/organization-models';

export const useSettingsStore = defineStore('settings', () => {
  // --- Dark Mode State ---
  // Lê a preferência do localStorage ou usa 'auto' como padrão
  const darkMode = ref<boolean | 'auto'>(
    JSON.parse(localStorage.getItem('darkMode') || '"auto"')
  );

  function setDarkMode(value: boolean | 'auto') {
    darkMode.value = value;
    Dark.set(value);
    // Salva a preferência no localStorage
    localStorage.setItem('darkMode', JSON.stringify(value));
  }

  // --- FUNÇÃO INIT ADICIONADA ---
  // Esta função é chamada pelo App.vue para garantir que o tema seja aplicado
  function init() {
    Dark.set(darkMode.value);
  }

  // --- Fuel Integration State ---
  const fuelIntegrationSettings = ref<OrganizationFuelIntegrationPublic | null>(null);
  const isLoadingFuelSettings = ref(false);

  // --- AÇÕES PARA INTEGRAÇÃO DE COMBUSTÍVEL ---

  async function fetchFuelIntegrationSettings() {
    isLoadingFuelSettings.value = true;
    try {
      const response = await api.get<OrganizationFuelIntegrationPublic>('/settings/fuel-integration');
      fuelIntegrationSettings.value = response.data;
    } catch (error) {
      console.error('Falha ao buscar configurações de integração:', error);
      Notify.create({ type: 'negative', message: 'Não foi possível carregar as configurações de integração.' });
    } finally {
      isLoadingFuelSettings.value = false;
    }
  }

  async function updateFuelIntegrationSettings(payload: OrganizationFuelIntegrationUpdate) {
    isLoadingFuelSettings.value = true;
    try {
      const response = await api.put<OrganizationFuelIntegrationPublic>('/settings/fuel-integration', payload);
      fuelIntegrationSettings.value = response.data;
      Notify.create({ type: 'positive', message: 'Configurações de integração salvas com sucesso!' });
    } catch (error) {
      console.error('Falha ao salvar configurações de integração:', error);
      Notify.create({ type: 'negative', message: 'Erro ao salvar as configurações.' });
    } finally {
      isLoadingFuelSettings.value = false;
    }
  }

  return {
    darkMode,
    setDarkMode,
    init, // <-- Exporta a função para ser usada pelo App.vue
    fuelIntegrationSettings,
    isLoadingFuelSettings,
    fetchFuelIntegrationSettings,
    updateFuelIntegrationSettings,
  };
});