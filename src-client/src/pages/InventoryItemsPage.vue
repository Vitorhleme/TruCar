<template>
  <q-page padding class="modern-page">
    <div class="page-content-container">
      
      <!-- HEADER -->
      <div class="flex items-center justify-between q-mb-xl">
        <div>
          <h1 class="text-h4 text-weight-bolder q-my-none">Rastreabilidade de Itens</h1>
          <div class="text-subtitle1 text-grey-6 q-mt-xs">Pesquise e audite todos os itens individuais do seu inventário</div>
        </div>
        <!-- Espaço reservado para ações globais futuras, ex: Exportar -->
        <q-btn 
          flat 
          round 
          dense 
          icon="refresh" 
          color="primary" 
          class="transition-generic hover-rotate" 
          @click="refreshTable"
        >
          <q-tooltip class="modern-tooltip bg-dark">Atualizar Dados</q-tooltip>
        </q-btn>
      </div>

      <!-- FILTROS -->
      <q-card class="dashboard-card q-mb-lg">
        <q-card-section class="row q-col-gutter-md items-center">
          <div class="col-12 col-sm-5 col-md-4">
            <q-input
              v-model="filters.search"
              placeholder="Buscar por nome da peça..."
              dense outlined rounded
              class="modern-input"
              clearable
            >
              <template v-slot:prepend>
                <q-icon name="search" color="grey-6" />
              </template>
            </q-input>
          </div>
          
          <div class="col-12 col-sm-4 col-md-3">
            <q-select
              v-model="filters.status"
              label="Filtrar por Status"
              :options="statusOptions"
              emit-value map-options
              dense outlined rounded
              class="modern-input"
              clearable
              behavior="menu"
            >
              <template v-slot:prepend>
                <q-icon name="filter_list" color="grey-6" />
              </template>
            </q-select>
          </div>

          <div class="col-12 col-sm-3 col-md-5 flex justify-end">
            <q-btn label="Limpar Filtros" flat rounded color="grey-7" class="text-weight-bold" @click="resetFilters" />
          </div>
        </q-card-section>
      </q-card>

      <!-- TABELA -->
      <q-card class="dashboard-card overflow-hidden">
        <q-table
          class="modern-table"
          :rows="partStore.masterItemList"
          :columns="columns"
          row-key="id"
          :loading="partStore.isMasterListLoading"
          no-data-label="Nenhum item encontrado na rastreabilidade."
          flat
          :rows-per-page-options="[10, 20, 50]"
          v-model:pagination="pagination"
          @request="onTableRequest"
          :rows-number="pagination.rowsNumber"
          binary-state-sort
          :table-header-class="$q.dark.isActive ? 'bg-dark text-white' : 'bg-grey-1 text-grey-9'"
        >
          <template v-slot:body-cell-item_identifier="props">
            <q-td :props="props">
              <span class="text-weight-bold text-dark-dynamic font-monospace">{{ props.value }}</span>
            </q-td>
          </template>

          <template v-slot:body-cell-part_name="props">
            <q-td :props="props">
              <span class="text-weight-medium">{{ props.value }}</span>
            </q-td>
          </template>

          <template v-slot:body-cell-status="props">
            <q-td :props="props">
              <q-badge :color="statusColor(props.value)" class="text-weight-bold q-px-sm q-py-xs shadow-1" rounded>
                {{ props.value }}
              </q-badge>
            </q-td>
          </template>
          
          <template v-slot:body-cell-vehicle="props">
            <q-td :props="props">
              <router-link v-if="props.value" :to="{ name: 'vehicle-details', params: { id: props.value.id } }" class="text-primary text-weight-medium transition-generic hover-opacity" style="text-decoration: none;">
                <q-icon name="directions_car" size="xs" class="q-mr-xs" />
                {{ props.value.brand }} {{ props.value.model }} 
                <span class="text-grey-6 text-caption q-ml-xs">({{ props.value.license_plate || props.value.identifier }})</span>
              </router-link>
              <span v-else class="text-grey-5 flex items-center justify-start">
                <q-icon name="remove" size="xs" class="q-mr-xs" /> N/A
              </span>
            </q-td>
          </template>

          <template v-slot:body-cell-actions="props">
            <q-td :props="props">
              <q-btn
                label="Detalhes"
                icon="visibility"
                color="primary"
                outline rounded dense
                class="text-weight-bold q-px-sm"
                :to="{ name: 'item-details', params: { id: props.row.id } }"
              >
                <q-tooltip class="modern-tooltip bg-dark">Ver linha do tempo completa</q-tooltip>
              </q-btn>
            </q-td>
          </template>
        </q-table>
      </q-card>

    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { usePartStore } from 'stores/part-store';
import { InventoryItemStatus } from 'src/models/inventory-item-models';
import type { QTableProps } from 'quasar';
import { useQuasar } from 'quasar';
const $q = useQuasar();
const partStore = usePartStore();

// Filtros
const filters = ref({
  search: null as string | null,
  status: null as InventoryItemStatus | null,
  partId: null as number | null,
  vehicleId: null as number | null
});

const statusOptions: { label: string, value: InventoryItemStatus }[] = [
  { label: 'Disponível', value: InventoryItemStatus.DISPONIVEL },
  { label: 'Em Uso', value: InventoryItemStatus.EM_USO },
  { label: 'Fim de Vida', value: InventoryItemStatus.FIM_DE_VIDA },
];

// Paginação (controlada pelo servidor)
const pagination = ref({
  page: 1,
  rowsPerPage: 15,
  rowsNumber: 0,
  sortBy: 'part_id',
  descending: false,
});

// Colunas da Tabela
const columns: QTableProps['columns'] = [
  { name: 'item_identifier', label: 'Cód. Item', field: 'item_identifier', align: 'left', sortable: true },
  { name: 'part_name', label: 'Nome da Peça', field: (row) => row.part.name, align: 'left', sortable: true },
  { name: 'status', label: 'Status', field: 'status', align: 'left', sortable: true },
  { name: 'vehicle', label: 'Veículo Instalado', field: 'installed_on_vehicle', align: 'left', sortable: false },
  { name: 'created_at', label: 'Data de Entrada', field: 'created_at', align: 'left', sortable: true, format: (val: string) => new Date(val).toLocaleDateString('pt-BR') },
  { name: 'actions', label: 'Ações', field: 'id', align: 'right' },
];

// Função para carregar os dados
async function fetchTableData() {
  await partStore.fetchMasterItems({
    page: pagination.value.page,
    rowsPerPage: pagination.value.rowsPerPage,
    status: filters.value.status,
    partId: filters.value.partId,
    vehicleId: filters.value.vehicleId,
    search: filters.value.search,
  });
  pagination.value.rowsNumber = partStore.masterListTotal;
}

const onTableRequest: QTableProps['onRequest'] = (props) => {
  pagination.value.page = props.pagination.page;
  pagination.value.rowsPerPage = props.pagination.rowsPerPage;
  pagination.value.sortBy = props.pagination.sortBy;
  pagination.value.descending = props.pagination.descending;
  void fetchTableData();
};

function refreshTable() {
  pagination.value.page = 1;
  void fetchTableData();
}

function resetFilters() {
  filters.value = { search: null, status: null, partId: null, vehicleId: null };
}

// O Watcher já dispara a busca, não é necessário chamar no resetFilters
watch(filters, refreshTable, { deep: true });

onMounted(() => {
  void fetchTableData();
});

function statusColor(status: InventoryItemStatus): string {
  const map: Record<InventoryItemStatus, string> = {
    'Disponível': 'positive',
    'Em Uso': 'primary',
    'Fim de Vida': 'negative'
  };
  return map[status] || 'grey';
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

.font-monospace {
  font-family: 'JetBrains Mono', 'Courier New', Courier, monospace;
}

.transition-generic { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.hover-rotate:hover { transform: rotate(45deg); }
.hover-opacity:hover { opacity: 0.8; }

.modern-tooltip {
  border-radius: 8px !important;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
}
</style>