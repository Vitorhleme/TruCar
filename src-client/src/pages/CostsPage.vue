<template>
  <q-page padding class="modern-page">
    <div class="page-content-container">
      
      <div class="flex items-center justify-between q-mb-xl">
        <div>
          <h1 class="text-h4 text-weight-bolder q-my-none">Análise de Custos</h1>
          <div class="text-subtitle1 text-grey-6 q-mt-xs">Visão detalhada das despesas operacionais da sua frota</div>
        </div>
        <q-btn 
          flat 
          round 
          dense 
          icon="refresh" 
          color="primary" 
          class="transition-generic hover-rotate" 
          @click="applyFilters"
        >
          <q-tooltip class="modern-tooltip bg-dark">Atualizar Dados</q-tooltip>
        </q-btn>
      </div>

      <q-card class="dashboard-card q-mb-lg">
        <q-card-section class="row q-col-gutter-lg items-center">
          <div class="col-12 col-md-5 col-lg-4">
            <q-input 
              outlined 
              rounded
              v-model="dateRangeText" 
              label="Filtrar por Período" 
              readonly 
              dense
              class="modern-input cursor-pointer"
            >
              <template v-slot:prepend><q-icon name="date_range" color="primary" /></template>
              <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                <q-date v-model="dateRange" range mask="YYYY-MM-DD" @update:model-value="applyFilters" color="primary">
                  <div class="row items-center justify-end q-pa-sm">
                    <q-btn v-close-popup label="Fechar" color="primary" flat />
                  </div>
                </q-date>
              </q-popup-proxy>
              <template v-slot:append v-if="dateRange">
                <q-icon name="close" @click.stop="clearDate" class="cursor-pointer" />
              </template>
            </q-input>
          </div>
          
          <div class="col-12 col-md-5 col-lg-4">
            <q-select
              outlined
              rounded
              v-model="categoryFilter"
              :options="costCategoryOptions"
              label="Filtrar por Categoria"
              dense
              clearable
              behavior="menu"
              class="modern-input"
              @update:model-value="applyFilters"
            >
              <template v-slot:prepend><q-icon name="category" color="primary" /></template>
            </q-select>
          </div>
        </q-card-section>
      </q-card>

      <div class="row q-col-gutter-lg q-mb-xl">
        <div class="col-12 col-xl-8 col-lg-7">
          <q-card class="dashboard-card full-height">
            <q-card-section class="q-pb-none">
              <div class="text-h6 text-weight-bold">Distribuição por Categoria</div>
              <div class="text-subtitle2 text-grey-6">Período atual</div>
            </q-card-section>
            <q-card-section class="flex flex-center" style="min-height: 350px;">
              <CostsPieChart v-if="filteredCosts.length > 0" :costs="filteredCosts" class="full-width" style="height: 320px;" />
              <div v-else class="text-center text-grey-5 column items-center">
                <q-icon name="pie_chart_outline" size="4em" class="q-mb-md opacity-30" />
                <div class="text-weight-medium">Nenhum dado financeiro para exibir no gráfico.</div>
              </div>
            </q-card-section>
          </q-card>
        </div>

        <div class="col-12 col-xl-4 col-lg-5">
          <div class="column q-gutter-y-lg full-height">
            
            <q-card class="dashboard-card hover-lift col">
              <q-card-section class="row items-center no-wrap full-height">
                <q-avatar size="56px" color="primary-light" text-color="primary" icon="account_balance_wallet" class="q-mr-md shadow-1" />
                <div>
                  <div class="text-caption text-uppercase text-weight-bold text-grey-6 letter-spacing-1">Custo Total (Filtrado)</div>
                  <div class="text-h4 text-weight-bolder text-dark-dynamic q-mt-xs">{{ formatCurrency(totalCost) }}</div>
                </div>
              </q-card-section>
            </q-card>

            <q-card class="dashboard-card hover-lift col">
              <q-card-section class="row items-center no-wrap full-height">
                <q-avatar size="56px" color="teal-1" text-color="teal-8" icon="receipt_long" class="q-mr-md shadow-1">
                  <div class="body--dark &">
                     <q-icon name="receipt_long" color="teal-4" />
                  </div>
                </q-avatar>
                <div>
                  <div class="text-caption text-uppercase text-weight-bold text-grey-6 letter-spacing-1">Média por Lançamento</div>
                  <div class="text-h5 text-weight-bold text-dark-dynamic q-mt-xs">{{ formatCurrency(averageCost) }}</div>
                </div>
              </q-card-section>
            </q-card>
            
            <q-card class="dashboard-card hover-lift col">
              <q-card-section class="row items-center no-wrap full-height">
                <q-avatar size="56px" color="amber-2" text-color="amber-9" icon="emoji_events" class="q-mr-md shadow-1">
                   <div class="body--dark &">
                     <q-icon name="emoji_events" color="amber-5" />
                  </div>
                </q-avatar>
                <div class="min-w-0">
                  <div class="text-caption text-uppercase text-weight-bold text-grey-6 letter-spacing-1">Maior Custo</div>
                  <div class="text-h6 text-weight-bold text-dark-dynamic q-mt-xs ellipsis">{{ topCostCategory }}</div>
                </div>
              </q-card-section>
            </q-card>

          </div>
        </div>
      </div>

      <q-card class="dashboard-card overflow-hidden">
        <q-table
          class="modern-table"
          title="Extrato de Despesas"
          :rows="filteredCosts"
          :columns="columns"
          row-key="id"
          :loading="costStore.isLoading"
          no-data-label="Nenhum custo encontrado para os filtros aplicados."
          flat
          :rows-per-page-options="[10, 25, 50]"
          :table-header-class="$q.dark.isActive ? 'bg-dark text-white' : 'bg-grey-1 text-grey-9'"
        >
          <template v-slot:body-cell-cost_type="props">
            <q-td :props="props">
              <q-badge 
                :color="getCategoryColor(props.value)" 
                class="text-weight-bold q-px-sm q-py-xs shadow-1" 
                rounded
              >
                {{ props.value }}
              </q-badge>
            </q-td>
          </template>

          <template v-slot:body-cell-description="props">
            <q-td :props="props">
              <span class="text-weight-medium text-dark-dynamic">{{ props.value }}</span>
            </q-td>
          </template>

          <template v-slot:body-cell-vehicle="props">
            <q-td :props="props">
              <router-link v-if="props.row.vehicle" :to="`/vehicles/${props.row.vehicle_id}`" class="text-primary text-weight-medium transition-generic hover-opacity" style="text-decoration: none;">
                <q-icon name="directions_car" size="xs" class="q-mr-xs" />
                {{ props.row.vehicle.brand }} {{ props.row.vehicle.model }}
                <span class="text-grey-6 text-caption q-ml-xs">({{ props.row.vehicle.license_plate || props.row.vehicle.identifier }})</span>
              </router-link>
              <span v-else class="text-grey-5 flex items-center">
                <q-icon name="remove" size="xs" class="q-mr-xs" /> N/A
              </span>
            </q-td>
          </template>
          
          <template v-slot:body-cell-amount="props">
            <q-td :props="props" class="text-weight-bold text-negative">
              {{ formatCurrency(props.value) }}
            </q-td>
          </template>
        </q-table>
      </q-card>

    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useVehicleCostStore } from 'stores/vehicle-cost-store';
import { format, parseISO } from 'date-fns';
import type { QTableColumn } from 'quasar';
import { useQuasar } from 'quasar';
import CostsPieChart from 'components/CostsPieChart.vue';

const costStore = useVehicleCostStore();
const $q = useQuasar();

// O Quasar date range pode retornar null, string, ou objeto com from/to.
type QuasarDateRange = { from: string, to: string } | string | null;
const dateRange = ref<QuasarDateRange>(null);
const categoryFilter = ref<string | null>(null);
const costCategoryOptions = ["Manutenção", "Combustível", "Pedágio", "Seguro", "Pneu", "Peças e Componentes", "Outros"];

// Dados Computados para a UI
const filteredCosts = computed(() => {
  if (!categoryFilter.value) {
    return costStore.costs;
  }
  return costStore.costs.filter(cost => cost.cost_type === categoryFilter.value);
});

const totalCost = computed(() => filteredCosts.value.reduce((sum, cost) => sum + cost.amount, 0));
const averageCost = computed(() => totalCost.value / (filteredCosts.value.length || 1));

const topCostCategory = computed(() => {
  if (filteredCosts.value.length === 0) return 'N/A';
  
  const costsByCategory: Record<string, number> = {};
  for (const cost of filteredCosts.value) {
    costsByCategory[cost.cost_type] = (costsByCategory[cost.cost_type] || 0) + cost.amount;
  }
  
  const sortedCategories = Object.entries(costsByCategory).sort((a, b) => b[1] - a[1]);

  if (sortedCategories.length > 0 && sortedCategories[0]) {
    return sortedCategories[0][0];
  }

  return 'N/A';
});

const dateRangeText = computed(() => {
  if (!dateRange.value) return 'Todo o período';
  
  // Trata o caso em que o Quasar devolve uma string única (se o user clicar no mesmo dia)
  if (typeof dateRange.value === 'string') {
    return format(parseISO(dateRange.value), 'dd/MM/yyyy');
  }

  const from = format(parseISO(dateRange.value.from), 'dd/MM/yyyy');
  const to = format(parseISO(dateRange.value.to), 'dd/MM/yyyy');
  return `${from} - ${to}`;
});

// Colunas da Tabela
const columns: QTableColumn[] = [
  { name: 'date', label: 'Data', field: 'date', format: (val) => format(parseISO(val), 'dd/MM/yyyy'), align: 'left', sortable: true },
  { name: 'cost_type', label: 'Categoria', field: 'cost_type', align: 'left', sortable: true },
  { name: 'description', label: 'Descrição da Despesa', field: 'description', align: 'left', style: 'max-width: 250px; white-space: normal;' },
  { name: 'vehicle', label: 'Veículo Associado', field: 'vehicle', align: 'left', sortable: true },
  { name: 'amount', label: 'Valor', field: 'amount', align: 'right', sortable: true },
];

function getCategoryColor(category: string): string {
  const map: Record<string, string> = {
    'Combustível': 'orange-8',
    'Manutenção': 'negative',
    'Pedágio': 'teal',
    'Seguro': 'blue-8',
    'Pneu': 'indigo',
    'Peças e Componentes': 'purple-6',
    'Outros': 'grey-7'
  };
  return map[category] || 'grey';
}

function clearDate() {
  dateRange.value = null;
  applyFilters();
}

function applyFilters() {
  let startDate = null;
  let endDate = null;

  if (dateRange.value) {
    if (typeof dateRange.value === 'string') {
      startDate = new Date(dateRange.value);
      endDate = new Date(dateRange.value);
    } else {
      startDate = new Date(dateRange.value.from);
      endDate = new Date(dateRange.value.to);
    }
  }

  void costStore.fetchAllCosts({ startDate, endDate });
}

const formatCurrency = (value: number) => value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

onMounted(() => {
  applyFilters();
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

/* INPUTS E UTILITÁRIOS */
.modern-input {
  :deep(.q-field__control) {
    background-color: white;
    .body--dark & { background-color: #1a1a1a; }
  }
}

.bg-primary-light { background-color: rgba($primary, 0.15); }

.text-dark-dynamic {
  color: #111827;
  .body--dark & { color: #f3f4f6; }
}

.min-w-0 { min-width: 0; }
.opacity-30 { opacity: 0.3; }
.letter-spacing-1 { letter-spacing: 1px; }

.transition-generic { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.hover-rotate:hover { transform: rotate(45deg); }
.hover-opacity:hover { opacity: 0.8; }

.modern-tooltip {
  border-radius: 8px !important;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
}

/* Fix específico para os avatares escuros */
.body--dark .bg-teal-1 { background-color: rgba(#009688, 0.15) !important; }
.body--dark .bg-amber-2 { background-color: rgba(#FFC107, 0.15) !important; }
</style>