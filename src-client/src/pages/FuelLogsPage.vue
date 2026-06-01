<template>
  <q-page padding class="modern-page">
    <div class="page-content-container">

      <!-- HEADER -->
      <div class="flex items-center justify-between q-mb-xl">
        <div>
          <h1 class="text-h4 text-weight-bolder q-my-none">Registros de Abastecimento</h1>
          <div class="text-subtitle1 text-grey-6 q-mt-xs">Gerencie abastecimentos manuais e integrados</div>
        </div>
        <div class="row items-center q-gutter-md">
          <q-btn
            @click="handleSync"
            color="white"
            text-color="primary"
            icon="sync"
            label="Sincronizar"
            :loading="fuelLogStore.isLoading"
            unelevated
            rounded
            class="text-weight-bold q-px-md transition-generic hover-rotate shadow-1"
          >
            <q-tooltip class="modern-tooltip bg-dark">Buscar novos abastecimentos do provedor</q-tooltip>
          </q-btn>
          <q-btn
            @click="openCreateDialog"
            color="primary"
            icon="add"
            label="Registrar Manualmente"
            unelevated
            rounded
            class="text-weight-bold q-px-md transition-generic hover-scale"
          />
        </div>
      </div>

      <!-- TABELA -->
      <q-card class="dashboard-card overflow-hidden">
        <q-table
          class="modern-table"
          :rows="fuelLogStore.fuelLogs"
          :columns="columns"
          row-key="id"
          :loading="fuelLogStore.isLoading"
          no-data-label="Nenhum abastecimento registrado"
          flat
          :rows-per-page-options="[10, 25, 50]"
          :table-header-class="$q.dark.isActive ? 'bg-dark text-white' : 'bg-grey-1 text-grey-9'"
        >
          <!-- STATUS DE VERIFICAÇÃO -->
          <template v-slot:body-cell-verification_status="props">
            <q-td :props="props" class="text-center">
              <q-badge
                :color="getVerificationStatusProps(props.row.verification_status).color"
                class="text-weight-bold q-px-sm q-py-xs shadow-1"
                rounded
              >
                <q-icon :name="getVerificationStatusProps(props.row.verification_status).icon" size="14px" class="q-mr-xs" />
                {{ getVerificationStatusProps(props.row.verification_status).label }}
              </q-badge>
            </q-td>
          </template>

          <!-- FONTE (INTEGRAÇÃO / MANUAL) -->
          <template v-slot:body-cell-source="props">
            <q-td :props="props" class="text-center">
              <q-badge
                :color="props.row.source === 'INTEGRATION' ? 'blue-1' : 'grey-2'"
                :text-color="props.row.source === 'INTEGRATION' ? 'blue-8' : 'grey-8'"
                class="text-weight-bold q-px-sm q-py-xs"
                rounded
              >
                <q-icon :name="props.row.source === 'INTEGRATION' ? 'cloud_sync' : 'edit'" size="14px" class="q-mr-xs" />
                {{ props.row.source === 'INTEGRATION' ? 'Integração' : 'Manual' }}
              </q-badge>
            </q-td>
          </template>

          <template v-slot:body-cell-vehicle="props">
            <q-td :props="props">
              <router-link v-if="props.row.vehicle" :to="{ name: 'vehicle-details', params: { id: props.row.vehicle.id } }" class="text-primary text-weight-medium transition-generic hover-opacity" style="text-decoration: none;">
                <q-icon name="directions_car" size="xs" class="q-mr-xs" />
                {{ props.row.vehicle.brand }} {{ props.row.vehicle.model }}
              </router-link>
              <span v-else class="text-grey-5 flex items-center">
                <q-icon name="remove" size="xs" class="q-mr-xs" /> N/A
              </span>
            </q-td>
          </template>

          <template v-slot:body-cell-cost="props">
            <q-td :props="props" class="text-weight-bold text-negative">
              {{ props.value }}
            </q-td>
          </template>
          
          <template v-slot:body-cell-actions="props">
            <q-td :props="props" class="text-center">
              <div v-if="isManager" class="row justify-center q-gutter-x-sm">
                <q-btn
                  icon="edit"
                  color="grey-6"
                  dense
                  flat
                  round
                  class="action-btn"
                  @click="onEditLog(props.row)"
                >
                  <q-tooltip class="modern-tooltip bg-dark">Editar Registro</q-tooltip>
                </q-btn>
                <q-btn
                  icon="delete_outline"
                  color="negative"
                  dense
                  flat
                  round
                  class="action-btn"
                  @click="onDeleteLog(props.row.id)"
                >
                  <q-tooltip class="modern-tooltip bg-negative">Excluir Registro</q-tooltip>
                </q-btn>
              </div>
              <span v-else class="text-grey-5">N/A</span>
            </q-td>
          </template>
          
        </q-table>
      </q-card>

      <!-- FORM DIALOG -->
      <q-dialog v-model="isCreateDialogOpen" transition-show="scale" transition-hide="scale">
        <q-card class="modern-dialog-card" style="width: 550px; max-width: 95vw;">
          <q-card-section class="dialog-header bg-primary text-white">
            <div class="text-h6 text-weight-bold flex items-center">
              <q-icon :name="editingLogId ? 'edit' : 'local_gas_station'" size="sm" class="q-mr-sm" />
              {{ editingLogId ? 'Editar Registro' : 'Novo Registro de Abastecimento' }}
            </div>
          </q-card-section>
          
          <q-form @submit.prevent="handleSubmit">
            <q-card-section class="q-gutter-y-md q-pa-lg">
              
              <div class="text-subtitle2 text-uppercase text-grey-6 text-weight-bold letter-spacing-1">Seleção do Veículo</div>
              <q-select
                outlined
                v-model="formData.vehicle_id"
                :options="vehicleOptions"
                :label="`${terminologyStore.vehicleNoun} *`" emit-value map-options
                :rules="[val => val > 0 || 'Selecione um veículo']"
                @update:model-value="handleVehicleSelect"
                behavior="menu"
                class="modern-input"
              >
                <template v-slot:prepend><q-icon name="directions_car" color="primary" /></template>
              </q-select>

              <q-separator class="q-my-md opacity-30" />
              <div class="text-subtitle2 text-uppercase text-grey-6 text-weight-bold letter-spacing-1">Detalhes do Abastecimento</div>
              
              <q-input
                outlined
                v-model.number="formData.odometer"
                type="number"
                :label="`${terminologyStore.odometerLabel} no momento *`"
                :rules="[val => (val !== null && val !== undefined && val >= 0) || 'Valor inválido']"
                class="modern-input"
              >
                <template v-slot:prepend><q-icon :name="terminologyStore.distanceUnit.toLowerCase() === 'km' ? 'speed' : 'timer'" color="grey-6" /></template>
              </q-input>
              
              <div class="row q-col-gutter-md">
                <div class="col-12 col-sm-6">
                  <q-input 
                    outlined 
                    v-model.number="formData.liters" 
                    type="number" 
                    label="Volume (Litros) *" 
                    step="0.01" 
                    :rules="[val => val > 0 || 'Deve ser maior que 0']" 
                    class="modern-input"
                  >
                    <template v-slot:prepend><q-icon name="water_drop" color="blue-5" /></template>
                  </q-input>
                </div>
                <div class="col-12 col-sm-6">
                  <q-input 
                    outlined 
                    v-model.number="formData.total_cost" 
                    type="number" 
                    label="Custo Total *" 
                    prefix="R$" 
                    step="0.01" 
                    :rules="[val => val > 0 || 'Deve ser maior que 0']" 
                    class="modern-input"
                  >
                    <template v-slot:prepend><q-icon name="payments" color="positive" /></template>
                  </q-input>
                </div>
              </div>
            </q-card-section>
            
            <q-card-actions align="right" class="q-pa-md bg-grey-1 dialog-footer">
              <q-btn flat label="Cancelar" color="grey-7" v-close-popup class="text-weight-bold" />
              <q-btn
                type="submit"
                unelevated
                rounded
                color="primary"
                :label="editingLogId ? 'Atualizar Registro' : 'Salvar Registro'" 
                :loading="fuelLogStore.isLoading"
                class="text-weight-bold q-px-md"
              />
            </q-card-actions>
          </q-form>
        </q-card>
      </q-dialog>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useQuasar } from 'quasar';
import { useFuelLogStore } from 'stores/fuel-log-store';
import { useVehicleStore } from 'stores/vehicle-store';
import { useAuthStore } from 'stores/auth-store';
import { useTerminologyStore } from 'stores/terminology-store';
import type { QTableProps } from 'quasar';
import type { FuelLog, FuelLogCreate, FuelLogUpdate } from 'src/models/fuel-log-models';

const fuelLogStore = useFuelLogStore();
const vehicleStore = useVehicleStore();
const authStore = useAuthStore();
const terminologyStore = useTerminologyStore();
const $q = useQuasar();

const isCreateDialogOpen = ref(false);
const editingLogId = ref<number | null>(null);

const formData = ref<FuelLogCreate>({
  vehicle_id: 0,
  odometer: 0,
  liters: 0,
  total_cost: 0,
});

const vehicleOptions = computed(() => vehicleStore.vehicles.map(v => ({
  label: `${v.brand} ${v.model} (${v.license_plate || v.identifier})`,
  value: v.id
})));

const isManager = computed(() => {
  if (!authStore.user) return false;
  return ['cliente_ativo', 'cliente_demo'].includes(authStore.user.role);
});

const columns: QTableProps['columns'] = [
  { name: 'verification_status', label: 'Status', field: 'verification_status', align: 'center', sortable: true },
  { name: 'date', label: 'Data', field: 'timestamp', format: (val) => new Date(val).toLocaleDateString('pt-BR'), align: 'left', sortable: true },
  { name: 'vehicle', label: 'Veículo', field: (row: FuelLog) => `${row.vehicle.brand} ${row.vehicle.model}`, align: 'left', sortable: true },
  { name: 'liters', label: 'Litros', field: 'liters', align: 'right', format: (val) => val.toFixed(2), sortable: true },
  { name: 'cost', label: 'Custo Total', field: 'total_cost', align: 'right', format: (val) => `R$ ${val.toFixed(2)}`, sortable: true },
  { name: 'user', label: 'Registrado por', field: (row: FuelLog) => row.user.full_name, align: 'left', sortable: true },
  { name: 'source', label: 'Fonte', field: 'source', align: 'center', sortable: true },
  { name: 'actions', label: 'Ações', field: '', align: 'center' },
];

function getVerificationStatusProps(status: FuelLog['verification_status']) {
  switch (status) {
    case 'VERIFIED':
      return { color: 'positive', icon: 'check_circle', label: 'Verificado' };
    case 'SUSPICIOUS':
      return { color: 'negative', icon: 'warning', label: 'Suspeito' };
    case 'PENDING':
      return { color: 'warning', icon: 'hourglass_empty', label: 'Pendente' };
    case 'UNVERIFIED':
      return { color: 'grey-6', icon: 'info', label: 'Não Verificado' };
    default:
      return { color: 'grey', icon: 'help', label: 'Desconhecido' };
  }
}

function handleVehicleSelect(vehicleId: number) {
  if (!vehicleId || editingLogId.value) return;

  const selectedVehicle = vehicleStore.vehicles.find(v => v.id === vehicleId);
  
  if (selectedVehicle) {
    if (authStore.userSector === 'agronegocio') {
      formData.value.odometer = selectedVehicle.current_engine_hours ?? 0;
    } else {
      formData.value.odometer = selectedVehicle.current_km ?? 0;
    }
  }
}

function openCreateDialog() {
  editingLogId.value = null; 
  formData.value = { vehicle_id: 0, odometer: 0, liters: 0, total_cost: 0 };
  isCreateDialogOpen.value = true;
}

function onEditLog(log: FuelLog) {
  editingLogId.value = log.id;
  
  formData.value = {
    vehicle_id: log.vehicle.id,
    odometer: log.odometer,
    liters: log.liters,
    total_cost: log.total_cost,
  };
  
  isCreateDialogOpen.value = true;
}

async function handleSubmit() {
  try {
    if (editingLogId.value) {
      await fuelLogStore.updateFuelLog(editingLogId.value, formData.value as FuelLogUpdate);
    } else {
      await fuelLogStore.createFuelLog(formData.value);
    }
    isCreateDialogOpen.value = false;
    editingLogId.value = null;
    
  } catch (error) {
    console.error('Erro ao salvar o registro de abastecimento:', error);
  }
}

async function handleSync() {
  await fuelLogStore.syncWithProvider();
}

function onDeleteLog(logId: number) {
  $q.dialog({
    title: 'Confirmar Exclusão',
    message: 'Tem certeza que deseja excluir este registro de abastecimento? Esta ação não pode ser desfeita.',
    html: true,
    cancel: { label: 'Cancelar', flat: true, color: 'grey-7' },
    ok: { label: 'Excluir', color: 'negative', rounded: true, unelevated: true },
    class: 'modern-dialog',
    persistent: false,
  }).onOk(() => {
    void fuelLogStore.deleteFuelLog(logId);
  });
}

onMounted(() => {
  void fuelLogStore.fetchFuelLogs();
  if (vehicleStore.vehicles.length === 0) {
    void vehicleStore.fetchAllVehicles();
  }
});
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

  .body--dark & {
    background: #1a1a1a;
    border: 1px solid rgba(255, 255, 255, 0.05);
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
  }
}

/* TABELAS MODERNAS */
.modern-table {
  :deep(.q-table__container) {
    border-radius: 16px;
  }
  
  :deep(.q-table tbody tr) {
    transition: background-color 0.2s ease;
    
    &:hover {
      background-color: rgba(0,0,0,0.02);
      .body--dark & { background-color: rgba(255,255,255,0.03); }
    }
  }

  :deep(.q-table th) {
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-size: 0.75rem;
  }
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

.action-btn {
  transition: all 0.2s;
  &:hover { background-color: rgba(0,0,0,0.05); }
  .body--dark &:hover { background-color: rgba(255,255,255,0.05); }
}

.opacity-30 { opacity: 0.3; }
.letter-spacing-1 { letter-spacing: 1px; }

.transition-generic { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.hover-rotate:hover { transform: rotate(180deg); }
.hover-scale:hover { transform: scale(1.02); }
.hover-opacity:hover { opacity: 0.8; }

.modern-tooltip {
  border-radius: 8px !important;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
}
</style>