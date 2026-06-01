<template>
  <q-page padding class="modern-page">
    <div class="page-content-container">

      <div class="flex items-center justify-between q-mb-xl">
        <div>
          <h1 class="text-h4 text-weight-bolder q-my-none">Central de Relatórios</h1>
          <div class="text-subtitle1 text-grey-6 q-mt-xs">Gere e exporte análises detalhadas da sua operação</div>
        </div>
        <q-btn 
          flat 
          round 
          dense 
          icon="refresh" 
          color="primary" 
          class="transition-generic hover-rotate" 
          @click="resetFilters"
        >
          <q-tooltip class="modern-tooltip bg-dark">Limpar Filtros</q-tooltip>
        </q-btn>
      </div>

      <q-card class="dashboard-card q-mb-xl">
        <q-card-section class="q-pa-lg">
          <div class="row q-col-gutter-lg items-start">
            
            <div class="col-12 col-md-4">
              <div class="text-subtitle2 text-uppercase text-grey-6 text-weight-bold letter-spacing-1 q-mb-sm">1. Tipo de Relatório</div>
              <q-select
                outlined
                rounded
                v-model="filters.reportType"
                :options="reportOptions"
                placeholder="Selecione o relatório..."
                emit-value
                map-options
                dense
                class="modern-input"
                behavior="menu"
              >
                <template v-slot:prepend><q-icon name="analytics" color="primary" /></template>
              </q-select>
            </div>

            <div v-if="filters.reportType === 'vehicle_consolidated'" class="col-12 col-md-4">
              <div class="text-subtitle2 text-uppercase text-grey-6 text-weight-bold letter-spacing-1 q-mb-sm">2. Veículo Alvo</div>
              <q-select
                outlined
                rounded
                v-model="filters.vehicleId"
                :options="vehicleOptions"
                placeholder="Selecione o veículo..."
                emit-value
                map-options
                dense
                use-input
                @filter="filterVehicles"
                :loading="vehicleStore.isLoading"
                class="modern-input"
                behavior="menu"
              >
                <template v-slot:prepend><q-icon name="directions_car" color="primary" /></template>
                <template v-slot:no-option>
                  <q-item><q-item-section class="text-grey-6">Nenhum veículo encontrado</q-item-section></q-item>
                </template>
              </q-select>
            </div>

            <div v-if="filters.reportType" class="col-12 col-md-4">
              <div class="text-subtitle2 text-uppercase text-grey-6 text-weight-bold letter-spacing-1 q-mb-sm">
                {{ filters.reportType === 'vehicle_consolidated' ? '3. Período' : '2. Período' }}
              </div>
              <q-input
                outlined
                rounded
                v-model="dateRangeText"
                placeholder="Selecione as datas..."
                readonly
                dense
                class="modern-input cursor-pointer"
              >
                <template v-slot:prepend><q-icon name="date_range" color="primary" /></template>
                <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                  <q-date v-model="filters.dateRange" range mask="YYYY-MM-DD" color="primary">
                    <div class="row items-center justify-end q-pa-sm">
                      <q-btn v-close-popup label="Confirmar" color="primary" flat />
                    </div>
                  </q-date>
                </q-popup-proxy>
              </q-input>
            </div>

            <div v-if="filters.reportType === 'vehicle_consolidated'" class="col-12">
              <q-separator class="q-my-sm opacity-30" />
              <div class="text-subtitle2 text-uppercase text-grey-6 text-weight-bold letter-spacing-1 q-mb-md">4. Módulos do Relatório</div>
              
              <div class="bg-grey-1 q-pa-md rounded-borders" :class="$q.dark.isActive ? 'bg-dark-module' : ''">
                <div class="row q-col-gutter-sm">
                  <div class="col-12 col-sm-4 col-md-3 col-xl-2">
                    <q-checkbox dense v-model="vehicleReportSections.performance_summary" label="Resumo de Performance" color="primary" class="text-weight-medium" />
                  </div>
                  <div class="col-12 col-sm-4 col-md-3 col-xl-2">
                    <q-checkbox dense v-model="vehicleReportSections.financial_summary" label="Resumo Financeiro" color="primary" class="text-weight-medium" />
                  </div>
                  <div class="col-12 col-sm-4 col-md-3 col-xl-2">
                    <q-checkbox dense v-model="vehicleReportSections.costs_detailed" label="Custos Detalhados" color="primary" class="text-weight-medium" />
                  </div>
                  <div class="col-12 col-sm-4 col-md-3 col-xl-2">
                    <q-checkbox dense v-model="vehicleReportSections.fuel_logs_detailed" label="Abastecimentos" color="primary" class="text-weight-medium" />
                  </div>
                  <div class="col-12 col-sm-4 col-md-3 col-xl-2">
                    <q-checkbox dense v-model="vehicleReportSections.maintenance_detailed" label="Manutenções" color="primary" class="text-weight-medium" />
                  </div>
                  <div class="col-12 col-sm-4 col-md-3 col-xl-2">
                    <q-checkbox dense v-model="vehicleReportSections.fines_detailed" label="Multas" color="primary" class="text-weight-medium" />
                  </div>
                  <div class="col-12 col-sm-4 col-md-3 col-xl-2">
                    <q-checkbox dense v-model="vehicleReportSections.journeys_detailed" label="Jornadas" color="primary" class="text-weight-medium" />
                  </div>
                  <div class="col-12 col-sm-4 col-md-3 col-xl-2">
                    <q-checkbox dense v-model="vehicleReportSections.documents_detailed" label="Documentos" color="primary" class="text-weight-medium" />
                  </div>
                  <div class="col-12 col-sm-4 col-md-3 col-xl-2">
                    <q-checkbox dense v-model="vehicleReportSections.tires_detailed" label="Pneus" color="primary" class="text-weight-medium" />
                  </div>
                </div>
              </div>
            </div>

          </div>
        </q-card-section>

        <q-card-actions class="q-pa-lg bg-grey-1 dialog-footer" align="right">
          <q-btn
            @click="generateReport"
            color="primary"
            label="Gerar Relatório"
            icon="summarize"
            unelevated
            rounded
            :loading="reportStore.isLoading"
            :disable="!isFormValid"
            class="text-weight-bold q-px-xl transition-generic hover-scale shadow-2"
            size="md"
          />
        </q-card-actions>
      </q-card>

      <div v-if="reportStore.isLoading" class="flex flex-center column q-py-xl text-primary">
        <q-spinner-grid size="4em" class="q-mb-md" />
        <div class="text-h6 text-weight-bold">Compilando dados...</div>
        <div class="text-grey-6">Isso pode levar alguns segundos dependendo do período.</div>
      </div>

      <div v-else-if="reportStore.vehicleReport" class="q-mt-xl fade-in">
        <VehicleReportDisplay :report="reportStore.vehicleReport" />
      </div>

      <div v-else-if="reportStore.driverPerformanceReport" class="q-mt-xl fade-in">
        <DriverPerformanceReportDisplay :report="reportStore.driverPerformanceReport" />
      </div>

      <div v-else-if="reportStore.fleetManagementReport" class="q-mt-xl fade-in">
        <FleetManagementReportDisplay :report="reportStore.fleetManagementReport" />
      </div>

      <div v-else class="flex flex-center column text-center q-pa-xl text-grey-5" style="min-height: 40vh;">
        <q-icon name="insert_chart_outlined" size="6em" class="q-mb-md opacity-30" />
        <h2 class="text-h5 text-weight-bold text-dark-dynamic q-my-none">Nenhum relatório gerado</h2>
        <p class="text-body1 q-mt-sm max-w-md text-grey-6">Selecione os filtros acima e clique em "Gerar Relatório" para visualizar os dados completos.</p>
      </div>

    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useQuasar } from 'quasar';
import { format } from 'date-fns';
import { useReportStore } from 'stores/report-store';
import { useVehicleStore } from 'stores/vehicle-store';
import type { Vehicle } from 'src/models/vehicle-models';

import VehicleReportDisplay from 'components/reports/VehicleReportDisplay.vue';
import DriverPerformanceReportDisplay from 'components/reports/DriverPerformanceReportDisplay.vue';
import FleetManagementReportDisplay from 'components/reports/FleetManagementReportDisplay.vue';

const $q = useQuasar();
const reportStore = useReportStore();
const vehicleStore = useVehicleStore();

type DateRangeType = { from: string, to: string } | string | null;

const filters = ref({
  reportType: null as 'vehicle_consolidated' | 'driver_performance' | 'fleet_management' | null,
  vehicleId: null as number | null,
  dateRange: null as DateRangeType,
});

const vehicleReportSections = ref({
  performance_summary: true,
  financial_summary: true,
  costs_detailed: true,
  fuel_logs_detailed: true,
  maintenance_detailed: false,
  fines_detailed: false,
  journeys_detailed: false,
  documents_detailed: false,
  tires_detailed: false,
});

watch(() => filters.value.reportType, () => {
  filters.value.vehicleId = null;
  filters.value.dateRange = null;
  reportStore.clearReports();
});

const reportOptions = [
  { label: 'Relatório Consolidado de Veículo', value: 'vehicle_consolidated' },
  { label: 'Relatório de Desempenho de Motoristas', value: 'driver_performance' },
  { label: 'Relatório Gerencial da Frota', value: 'fleet_management' },
];

const vehicleOptions = ref<{ label: string, value: number }[]>([]);

const dateRangeText = computed(() => {
  if (!filters.value.dateRange) return '';
  
  if (typeof filters.value.dateRange === 'string') {
    return format(new Date(filters.value.dateRange.replace(/-/g, '/')), 'dd/MM/yyyy');
  }

  const from = format(new Date(filters.value.dateRange.from.replace(/-/g, '/')), 'dd/MM/yyyy');
  const to = format(new Date(filters.value.dateRange.to.replace(/-/g, '/')), 'dd/MM/yyyy');
  return `${from} - ${to}`;
});

const isFormValid = computed(() => {
  if (!filters.value.reportType || !filters.value.dateRange) return false;
  if (filters.value.reportType === 'vehicle_consolidated') {
    return !!filters.value.vehicleId;
  }
  return true;
});

function filterVehicles(val: string, update: (callback: () => void) => void) {
  update(() => {
    const needle = val.toLowerCase();
    vehicleOptions.value = vehicleStore.vehicles
      .filter((v: Vehicle) =>
        (v.license_plate?.toLowerCase().includes(needle) ||
         v.identifier?.toLowerCase().includes(needle) ||
         `${v.brand} ${v.model}`.toLowerCase().includes(needle))
      )
      .map((v: Vehicle) => ({
        label: `${v.brand} ${v.model} (${v.license_plate || v.identifier})`,
        value: v.id,
      }));
  });
}

function resetFilters() {
  filters.value.reportType = null;
  filters.value.vehicleId = null;
  filters.value.dateRange = null;
  reportStore.clearReports();
}

async function generateReport() {
  if (!isFormValid.value || !filters.value.dateRange) {
    $q.notify({ type: 'warning', message: 'Por favor, preencha todos os filtros obrigatórios.' });
    return;
  }

  let from = '';
  let to = '';

  if (typeof filters.value.dateRange === 'string') {
    from = filters.value.dateRange;
    to = filters.value.dateRange;
  } else {
    from = filters.value.dateRange.from;
    to = filters.value.dateRange.to;
  }

  if (filters.value.reportType === 'vehicle_consolidated' && filters.value.vehicleId) {
    await reportStore.generateVehicleConsolidatedReport(
      filters.value.vehicleId,
      from,
      to,
      vehicleReportSections.value
    );
  } else if (filters.value.reportType === 'driver_performance') {
    await reportStore.generateDriverPerformanceReport(from, to);
  } else if (filters.value.reportType === 'fleet_management') {
    await reportStore.generateFleetManagementReport(from, to);
  }
}

onMounted(() => {
  reportStore.clearReports();
  if (vehicleStore.vehicles.length === 0) {
    void vehicleStore.fetchAllVehicles({ page: 1, rowsPerPage: 9999 });
  } else {
    filterVehicles('', (fn) => fn());
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

.dialog-footer {
  border-top: 1px solid rgba(0,0,0,0.05);
  .body--dark & {
    background: #121212 !important;
    border-top: 1px solid rgba(255,255,255,0.05);
  }
}

.bg-dark-module {
  background-color: #121212 !important;
  border: 1px solid rgba(255,255,255,0.05);
}

/* INPUTS E UTILITÁRIOS */
.modern-input {
  :deep(.q-field__control) {
    background-color: white;
    .body--dark & { background-color: #1a1a1a; }
  }
}

.text-dark-dynamic {
  color: #111827;
  .body--dark & { color: #f3f4f6; }
}

.opacity-30 { opacity: 0.3; }
.letter-spacing-1 { letter-spacing: 1px; }

.transition-generic { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.hover-rotate:hover { transform: rotate(180deg); }
.hover-scale:hover { transform: translateY(-2px); box-shadow: 0 8px 15px rgba(0,0,0,0.1); }

.modern-tooltip {
  border-radius: 8px !important;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
}

/* ANIMAÇÃO FADE-IN PARA RESULTADOS */
.fade-in {
  animation: fadeIn 0.4s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>