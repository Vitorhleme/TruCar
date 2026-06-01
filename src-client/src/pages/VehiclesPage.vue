<template>
  <q-page padding class="modern-page">
    <div class="page-content-container">
      
      <div class="flex items-center justify-between q-mb-xl">
        <div>
          <h1 class="text-h4 text-weight-bolder q-my-none">{{ terminologyStore.vehiclePageTitle }}</h1>
          <div class="text-subtitle1 text-grey-6 q-mt-xs">Gerencie os ativos da sua frota</div>
        </div>
        
        <div class="row items-center q-gutter-md">
          <q-input
            outlined dense rounded debounce="300" v-model="searchTerm"
            :placeholder="`Buscar por ${terminologyStore.plateOrIdentifierLabel.toLowerCase()}, marca...`"
            class="modern-input"
            style="width: 280px"
          >
            <template v-slot:append>
              <q-icon name="search" color="grey-6" />
            </template>
          </q-input>
          
          <q-btn
            v-if="authStore.isManager" 
            @click="openCreateDialog" 
            color="primary"
            icon="add" 
            :label="terminologyStore.addVehicleButtonLabel" 
            unelevated
            rounded
            class="text-weight-bold q-px-md transition-generic hover-scale"
          />
        </div>
      </div>

      <div v-if="vehicleStore.isLoading && vehicleStore.vehicles.length === 0" class="row q-col-gutter-lg">
        <div v-for="n in 8" :key="n" class="col-xs-12 col-sm-6 col-md-4 col-lg-3">
          <q-card class="dashboard-card overflow-hidden">
            <q-skeleton height="160px" square />
            <q-card-section class="q-pa-md">
              <q-skeleton type="text" class="text-subtitle1" width="80%" />
              <q-skeleton type="text" class="text-caption" width="50%" />
            </q-card-section>
            <q-card-section class="bg-grey-1 q-pa-md">
              <q-skeleton type="text" width="90%" />
              <q-skeleton type="text" width="60%" />
            </q-card-section>
          </q-card>
        </div>
      </div>

      <div v-else-if="vehicleStore.vehicles.length > 0" class="row q-col-gutter-lg">
        <div v-for="vehicle in vehicleStore.vehicles" :key="vehicle.id" class="col-xs-12 col-sm-6 col-md-4 col-lg-3">
          <q-card class="dashboard-card hover-lift column no-wrap full-height cursor-pointer overflow-hidden" @click="goToVehicleDetails(vehicle, 'details')">
            
            <q-img :src="vehicle.photo_url ?? undefined" height="180px" fit="cover" class="vehicle-img-container">
              <template v-slot:error>
                <div class="absolute-full flex flex-center bg-primary-gradient text-white">
                  <q-icon :name="getVehicleIcon(vehicle)" size="56px" class="opacity-80" />
                </div>
              </template>
              
              <div class="absolute-top bg-transparent text-right q-pa-sm" style="background: linear-gradient(to bottom, rgba(0,0,0,0.4) 0%, transparent 100%);">
                <q-badge :color="getStatusColor(vehicle.status)" class="text-weight-bold shadow-1 q-px-sm q-py-xs rounded-borders">
                  <q-icon :name="getStatusIcon(vehicle.status)" size="xs" class="q-mr-xs" />
                  {{ vehicle.status }}
                </q-badge>
              </div>
            </q-img>

            <q-card-section class="q-pa-md col-grow flex column justify-between">
              <div class="flex items-start no-wrap q-mb-sm">
                <div class="col min-w-0">
                  <div class="text-h6 text-weight-bold ellipsis text-dark-dynamic" style="line-height: 1.2;">{{ vehicle.brand }} {{ vehicle.model }}</div>
                  <div class="text-caption text-grey-6 q-mt-xs text-weight-medium">
                    <span class="bg-grey-2 text-grey-8 q-px-sm q-py-xs rounded-borders q-mr-sm" :class="$q.dark.isActive ? 'bg-grey-9 text-grey-4' : ''">
                      {{ vehicle.license_plate || vehicle.identifier }}
                    </span>
                    &bull; {{ vehicle.year }}
                  </div>
                </div>
                
                <div v-if="authStore.isManager" class="col-auto no-wrap row items-center q-ml-sm">
                  <q-icon v-if="vehicle.telemetry_device_id" name="sensors" color="positive" size="22px" class="q-mr-xs action-icon">
                    <q-tooltip class="modern-tooltip bg-dark">Telemetria Ativa</q-tooltip>
                  </q-icon>
                  <q-btn @click.stop="goToVehicleDetails(vehicle, 'costs')" flat round dense icon="account_balance_wallet" color="grey-6" class="action-btn">
                    <q-tooltip class="modern-tooltip bg-dark">Ver Custos</q-tooltip>
                  </q-btn>
                  <q-btn @click.stop="openEditDialog(vehicle)" flat round dense icon="edit" color="grey-6" class="action-btn">
                    <q-tooltip class="modern-tooltip bg-dark">Editar</q-tooltip>
                  </q-btn>
                  <q-btn @click.stop="promptToDelete(vehicle)" flat round dense icon="delete_outline" color="negative" class="action-btn">
                    <q-tooltip class="modern-tooltip bg-negative">Excluir</q-tooltip>
                  </q-btn>
                </div>
              </div>
            </q-card-section>

            <q-card-section class="metrics-footer q-pa-md">
              <div class="flex justify-between items-center text-caption q-mb-sm">
                <span class="text-grey-7 flex items-center">
                  <q-icon :name="terminologyStore.distanceUnit.toLowerCase() === 'km' ? 'speed' : 'timer'" size="14px" class="q-mr-xs" />
                  {{ terminologyStore.distanceUnit.toLowerCase() === 'km' ? 'Odômetro' : 'Horímetro' }}
                </span>
                <span class="text-weight-bold text-dark-dynamic text-body2">
                  {{
                    formatDistance(
                      terminologyStore.distanceUnit.toLowerCase() === 'km' ? vehicle.current_km : vehicle.current_engine_hours,
                      terminologyStore.distanceUnit as 'km' | 'Horas'
                    )
                  }}
                </span>
              </div>
              <div v-if="vehicle.next_maintenance_km || vehicle.next_maintenance_date" class="flex justify-between items-center text-caption">
                <span class="text-grey-7 flex items-center">
                  <q-icon name="build_circle" size="14px" class="q-mr-xs" /> Próx. Revisão
                </span>
                <span class="text-weight-bold text-primary ellipsis text-right" style="max-width: 60%;">
                  {{ vehicle.next_maintenance_km ? `${vehicle.next_maintenance_km.toLocaleString('pt-BR')} ${terminologyStore.distanceUnit}` : '' }}
                  {{ vehicle.next_maintenance_km && vehicle.next_maintenance_date ? ' ou ' : '' }}
                  {{ vehicle.next_maintenance_date ? (new Date(vehicle.next_maintenance_date + 'T00:00:00')).toLocaleDateString('pt-BR') : '' }}
                </span>
              </div>
              <div v-else class="text-caption text-grey-5 text-right">
                Sem revisão agendada
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <div v-else class="text-center text-grey-5 q-pa-xl column items-center justify-center" style="min-height: 50vh;">
        <q-icon name="directions_car" size="6em" class="q-mb-lg opacity-30" />
        <div class="text-h5 text-weight-bold text-dark-dynamic q-mb-sm">Nenhum {{ terminologyStore.vehicleNoun.toLowerCase() }} encontrado</div>
        <div class="text-body1 q-mb-lg max-w-md">Parece que ainda não tem veículos registados ou a sua pesquisa não encontrou resultados.</div>
        <q-btn v-if="authStore.isManager" @click="openCreateDialog" unelevated rounded color="primary" icon="add" :label="`Adicionar ${terminologyStore.vehicleNoun}`" class="text-weight-bold q-px-lg shadow-2" size="lg" />
      </div>

      <div class="flex flex-center q-mt-xl" v-if="pagination.rowsNumber > pagination.rowsPerPage">
        <q-pagination 
          v-model="pagination.page" 
          :max="Math.ceil(pagination.rowsNumber / pagination.rowsPerPage)" 
          @update:model-value="onPageChange" 
          direction-links 
          boundary-links 
          icon-first="skip_previous" 
          icon-last="skip_next" 
          icon-prev="fast_rewind" 
          icon-next="fast_forward"
          color="primary"
          active-color="primary"
          active-text-color="white"
          class="modern-pagination"
        />
      </div>

      <q-dialog v-model="isFormDialogOpen" transition-show="scale" transition-hide="scale">
        <q-card class="modern-dialog-card" style="width: 550px; max-width: 95vw;">
          <q-card-section class="dialog-header bg-primary text-white">
            <div class="text-h6 text-weight-bold flex items-center">
              <q-icon :name="isEditing ? 'edit' : 'add_circle'" size="sm" class="q-mr-sm" />
              {{ isEditing ? terminologyStore.editButtonLabel : terminologyStore.newButtonLabel }}
            </div>
          </q-card-section>
          
          <q-form @submit.prevent="onFormSubmit">
            <q-card-section class="q-gutter-y-md q-pa-lg">
              
              <div class="row q-col-gutter-md">
                <div class="col-12 col-sm-6">
                  <q-input outlined v-model="formData.brand" label="Marca *" :rules="[val => !!val || 'Campo obrigatório']" />
                </div>
                <div class="col-12 col-sm-6">
                  <q-input outlined v-model="formData.model" label="Modelo *" :rules="[val => !!val || 'Campo obrigatório']" />
                </div>
              </div>

              <div class="row q-col-gutter-md">
                <div class="col-12 col-sm-6" v-if="!isEditing">
                  <q-input outlined v-model="formData.license_plate" :label="terminologyStore.plateOrIdentifierLabel + ' *'" :mask="authStore.userSector !== 'agronegocio' ? 'AAA#A##' : ''" :rules="[val => !!val || 'Campo obrigatório']" />
                </div>
                <div :class="!isEditing ? 'col-12 col-sm-6' : 'col-12'">
                  <q-input outlined v-model.number="formData.year" type="number" label="Ano *" :rules="[val => val > 1980 || 'Ano inválido']" />
                </div>
              </div>

              <div class="row q-col-gutter-md">
                <div class="col-12 col-sm-6">
                  <q-input v-if="authStore.userSector === 'agronegocio'" outlined v-model.number="formData.current_engine_hours" type="number" label="Horas Atuais" step="0.1" />
                  <q-input v-else outlined v-model.number="formData.current_km" type="number" label="KM Inicial" />
                </div>
                <div class="col-12 col-sm-6" v-if="isEditing">
                  <q-select outlined v-model="formData.status" :options="statusOptions" label="Status" behavior="menu" />
                </div>
              </div>

              <q-file v-model="photoFile" label="Carregar Foto (Opcional)" outlined clearable accept=".jpg, image/*">
                <template v-slot:prepend><q-icon name="add_a_photo" color="primary" /></template>
                <template v-if="formData.photo_url && !photoFile" v-slot:append>
                  <q-avatar rounded size="40px" class="shadow-1"><img :src="formData.photo_url ?? undefined" alt="Foto atual" /></q-avatar>
                </template>
              </q-file>
              
              <q-separator class="q-my-md opacity-30" />
              <div class="text-subtitle2 text-uppercase text-grey-6 text-weight-bold letter-spacing-1">Integração</div>
              
              <q-input outlined v-model="formData.telemetry_device_id" label="ID da Telemetria (Opcional)" hint="Ex: TRATOR-001. Conecta o maquinário ao GPS." >
                <template v-slot:prepend><q-icon name="sensors" color="grey-6" /></template>
              </q-input>
              
              <q-separator class="q-my-md opacity-30" />
              <div class="text-subtitle2 text-uppercase text-grey-6 text-weight-bold letter-spacing-1">Manutenção Preventiva</div>
              
              <div class="row q-col-gutter-md">
                <div class="col-12 col-sm-6">
                  <q-input outlined v-model.number="formData.next_maintenance_km" type="number" :label="`Próx. Revisão (${terminologyStore.distanceUnit})`" clearable />
                </div>
                <div class="col-12 col-sm-6">
                  <q-input outlined v-model="formData.next_maintenance_date" mask="##/##/####" label="Próx. Revisão (Data)" clearable>
                    <template v-slot:append>
                      <q-icon name="event" class="cursor-pointer" color="primary">
                        <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                          <q-date v-model="formData.next_maintenance_date" mask="DD/MM/YYYY"><div class="row items-center justify-end"><q-btn v-close-popup label="Fechar" color="primary" flat /></div></q-date>
                        </q-popup-proxy>
                      </q-icon>
                    </template>
                  </q-input>
                </div>
              </div>
              
              <q-input outlined v-model="formData.maintenance_notes" type="textarea" label="Anotações Gerais" autogrow rows="2" />
            </q-card-section>
            
            <q-card-actions align="right" class="q-pa-md bg-grey-1 dialog-footer">
              <q-btn flat label="Cancelar" color="grey-7" v-close-popup class="text-weight-bold" />
              <q-btn type="submit" unelevated rounded color="primary" label="Guardar Veículo" :loading="isSubmitting" class="text-weight-bold q-px-md" />
            </q-card-actions>
          </q-form>
        </q-card>
    </q-dialog>

    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import { useVehicleStore } from 'stores/vehicle-store';
import { useAuthStore } from 'stores/auth-store';
import { useTerminologyStore } from 'stores/terminology-store';
import { useDemoStore } from 'stores/demo-store';
import { VehicleStatus, type Vehicle, type VehicleCreate, type VehicleUpdate } from 'src/models/vehicle-models';
import api from 'src/services/api';
import axios from 'axios';

const $q = useQuasar();
const vehicleStore = useVehicleStore();
const authStore = useAuthStore();
const terminologyStore = useTerminologyStore();
const router = useRouter();
const demoStore = useDemoStore();

const isFormDialogOpen = ref(false);
const isSubmitting = ref(false);
const editingVehicleId = ref<number | null>(null);
const isEditing = computed(() => editingVehicleId.value !== null);
const statusOptions = Object.values(VehicleStatus);
const formData = ref<Partial<Vehicle>>({});
const photoFile = ref<File | null>(null);

const isVehicleLimitReached = computed(() => {
  if (!authStore.isDemo) return false;
  const limit = authStore.user?.organization?.vehicle_limit;
  if (limit === undefined || limit === null || limit < 0) return false;
  const currentCount = demoStore.stats?.vehicle_count ?? 0;
  return currentCount >= limit;
});

function showUpgradeDialog() {
  $q.dialog({
    title: 'Limite do Plano Demo Atingido',
    message: `Você atingiu o limite de ${authStore.user?.organization?.vehicle_limit} ${terminologyStore.vehicleNounPlural.toLowerCase()} permitidos no plano de demonstração. Entre em contato para atualizar seu plano e liberar o cadastro ilimitado.`,
    ok: { label: 'Entendido', color: 'primary', rounded: true, unelevated: true },
    class: 'modern-dialog',
    persistent: false
  });
}

function goToVehicleDetails(vehicle: Vehicle, tab = 'details') {
  void router.push({ 
    name: 'vehicle-details', 
    params: { id: vehicle.id },
    query: { tab: tab }
  });
}

function resetForm() {
  editingVehicleId.value = null;
  formData.value = {
    brand: '', model: '', year: new Date().getFullYear(),
    license_plate: '', identifier: '', photo_url: null, status: VehicleStatus.AVAILABLE,
    current_km: 0, current_engine_hours: 0,
    next_maintenance_date: null, next_maintenance_km: null, maintenance_notes: '',
    telemetry_device_id: null,
  };
  photoFile.value = null;
}

function openCreateDialog() {
  if (isVehicleLimitReached.value) {
    showUpgradeDialog();
    return;
  }
  resetForm();
  isFormDialogOpen.value = true;
}

function openEditDialog(vehicle: Vehicle) {
  editingVehicleId.value = vehicle.id;
  formData.value = {
    ...vehicle,
    next_maintenance_date: vehicle.next_maintenance_date
      ? vehicle.next_maintenance_date.split('-').reverse().join('/')
      : null,
  };
  photoFile.value = null;
  isFormDialogOpen.value = true;
}

async function uploadPhoto(file: File): Promise<string | null> {
  try {
    const fd = new FormData();
    fd.append('file', file);
    const response = await api.post('/upload-photo', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
    return response.data.file_url;
  } catch {
    $q.notify({ type: 'negative', message: 'Falha ao carregar a foto.' });
    return null;
  }
}

async function onFormSubmit() {
  isSubmitting.value = true;
  try {
    const payload = { ...formData.value };

    if (photoFile.value) {
      const photoUrl = await uploadPhoto(photoFile.value);
      if (!photoUrl) { isSubmitting.value = false; return; }
      payload.photo_url = photoUrl;
    }

    if (payload.next_maintenance_date?.includes('/')) {
      payload.next_maintenance_date = payload.next_maintenance_date.split('/').reverse().join('-');
    }

    if (authStore.userSector === 'agronegocio' && payload.license_plate) {
      payload.identifier = payload.license_plate;
      delete payload.license_plate;
    }

    const currentFetchParams = {
      page: pagination.value.page,
      rowsPerPage: pagination.value.rowsPerPage,
      search: searchTerm.value,
    };

    if (isEditing.value && editingVehicleId.value) {
      await vehicleStore.updateVehicle(editingVehicleId.value, payload as VehicleUpdate, currentFetchParams);
    } else {
      await vehicleStore.addNewVehicle(payload as VehicleCreate, currentFetchParams);
      if (authStore.isDemo) {
        void demoStore.fetchDemoStats();
      }
    }

    isFormDialogOpen.value = false;
    $q.notify({ type: 'positive', message: 'Veículo salvo com sucesso!' });
  } catch (error) {
    let errorMessage = 'Falha ao salvar o veículo. Verifique os dados.';
    if (axios.isAxiosError(error) && error.response?.data?.detail) {
      errorMessage = error.response.data.detail;
    }
    $q.notify({ type: 'negative', message: errorMessage });
  } finally {
    isSubmitting.value = false;
  }
}

const searchTerm = ref('');
const pagination = ref({ page: 1, rowsPerPage: 12, rowsNumber: 0 }); // Aumentado para 12 para preencher melhor o grid

async function fetchFromServer(page: number, rowsPerPage: number, search: string) {
  await vehicleStore.fetchAllVehicles({ page, rowsPerPage, search });
  pagination.value.rowsNumber = vehicleStore.totalItems;
}

function onPageChange(page: number) {
  pagination.value.page = page;
  void fetchFromServer(page, pagination.value.rowsPerPage, searchTerm.value);
}

watch(searchTerm, () => {
  pagination.value.page = 1;
  void fetchFromServer(1, pagination.value.rowsPerPage, searchTerm.value);
});

onMounted(() => {
  void fetchFromServer(pagination.value.page, pagination.value.rowsPerPage, searchTerm.value);
  if (authStore.isDemo) {
    void demoStore.fetchDemoStats();
  }
});

function formatDistance(value: number | null | undefined, unit: 'km' | 'Horas'): string {
  const numValue = value ?? 0;
  const formattedValue = numValue.toLocaleString('pt-BR', {
    minimumFractionDigits: unit === 'Horas' ? 1 : 0,
    maximumFractionDigits: unit === 'Horas' ? 1 : 0,
  });
  return `${formattedValue} ${unit}`;
}

function getVehicleIcon(vehicle: Vehicle): string {
  if (authStore.userSector === 'agronegocio') return 'agriculture';
  if (authStore.userSector === 'construcao_civil') return 'construction';
  if (vehicle.model) {
    const lowerModel = vehicle.model.toLowerCase();
    if (lowerModel.includes('strada') || lowerModel.includes('fiorino') || lowerModel.includes('caminhonete') || lowerModel.includes('pickup')) return 'local_shipping';
    if (lowerModel.includes('carro') || lowerModel.includes('sedan') || lowerModel.includes('hatch')) return 'directions_car';
    if (lowerModel.includes('moto') || lowerModel.includes('motocicleta')) return 'two_wheeler';
  }
  return 'directions_car';
}

function getStatusIcon(status: VehicleStatus): string {
  const iconMap: Record<VehicleStatus, string> = {
    [VehicleStatus.AVAILABLE]: 'check_circle',
    [VehicleStatus.IN_USE]: 'play_circle',
    [VehicleStatus.MAINTENANCE]: 'build_circle'
  };
  return iconMap[status] || 'info';
}

function getStatusColor(status: VehicleStatus): string {
  const colorMap: Record<VehicleStatus, string> = {
    [VehicleStatus.AVAILABLE]: 'positive',
    [VehicleStatus.IN_USE]: 'warning',
    [VehicleStatus.MAINTENANCE]: 'negative'
  };
  return colorMap[status] || 'grey';
}

function promptToDelete(vehicle: Vehicle) {
  $q.dialog({
    title: 'Confirmar Exclusão',
    message: `Tem a certeza que deseja excluir ${terminologyStore.vehicleNoun.toLowerCase()} <strong>${vehicle.brand} ${vehicle.model}</strong>? Esta ação removerá o histórico associado.`,
    html: true,
    ok: { label: 'Excluir', color: 'negative', rounded: true, unelevated: true },
    cancel: { label: 'Cancelar', flat: true, color: 'grey-7' },
    class: 'modern-dialog'
  }).onOk(() => {
    void vehicleStore.deleteVehicle(vehicle.id, {
      page: pagination.value.page, rowsPerPage: pagination.value.rowsPerPage, search: searchTerm.value,
    });
  });
}
</script>

<style scoped lang="scss">
/* FUNDO DA PÁGINA */
.modern-page {
  background-color: #f8f9fa;
  min-height: 100vh;
  
  .body--dark & {
    background-color: #0d0d0d;
  }
}

.page-content-container {
  max-width: 1600px;
  margin: 0 auto;
}

/* CARTÕES E CONTAINERS */
.dashboard-card {
  border-radius: 16px;
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.04);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
  transition: all 0.3s ease;

  .body--dark & {
    background: #1a1a1a;
    border: 1px solid rgba(255, 255, 255, 0.05);
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
  }
}

.hover-lift {
  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.08);
  }
  .body--dark &:hover {
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.4);
  }
}

/* VEÍCULOS CARD SPECIFIC */
.vehicle-img-container {
  border-bottom: 1px solid rgba(0,0,0,0.05);
  .body--dark & { border-bottom-color: rgba(255,255,255,0.05); }
}

.bg-primary-gradient {
  background: linear-gradient(135deg, $primary 0%, color-mix(in srgb, $primary 60%, black) 100%);
}

.metrics-footer {
  background-color: #fcfcfc;
  border-top: 1px solid rgba(0, 0, 0, 0.03);
  
  .body--dark & {
    background-color: #121212;
    border-top: 1px solid rgba(255, 255, 255, 0.03);
  }
}

.action-btn {
  transition: all 0.2s;
  &:hover { background-color: rgba(0,0,0,0.05); }
  .body--dark &:hover { background-color: rgba(255,255,255,0.05); }
}

.action-icon {
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
}

/* DIALOGS E FORMULÁRIOS */
.modern-dialog-card {
  border-radius: 20px;
  overflow: hidden;
  
  .dialog-header {
    padding: 20px 24px;
  }
  
  .dialog-footer {
    border-top: 1px solid rgba(0,0,0,0.05);
    .body--dark & {
      background: #121212 !important;
      border-top: 1px solid rgba(255,255,255,0.05);
    }
  }

  .body--dark & {
    background: #1a1a1a;
  }
}

/* INPUTS E UTILITÁRIOS */
.modern-input {
  :deep(.q-field__control) {
    background-color: white;
    .body--dark & { background-color: #1a1a1a; }
  }
}

.modern-pagination {
  :deep(.q-btn) {
    border-radius: 8px;
  }
}

.text-dark-dynamic {
  color: #111827;
  .body--dark & { color: #f3f4f6; }
}

.min-w-0 { min-width: 0; }
.opacity-80 { opacity: 0.8; }
.opacity-30 { opacity: 0.3; }
.letter-spacing-1 { letter-spacing: 1px; }

.transition-generic { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.hover-scale:hover { transform: scale(1.02); }

.modern-tooltip {
  border-radius: 8px !important;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
}
</style>