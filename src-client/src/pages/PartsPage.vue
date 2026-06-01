<template>
  <q-page padding class="modern-page">
    <div class="page-content-container">

      <!-- HEADER -->
      <div class="flex items-center justify-between q-mb-xl">
        <div>
          <h1 class="text-h4 text-weight-bolder q-my-none">Inventário</h1>
          <div class="text-subtitle1 text-grey-6 q-mt-xs">Controle o seu estoque de peças, fluídos e consumíveis</div>
        </div>
        <q-btn 
          @click="openDialog()" 
          color="primary" 
          icon="add" 
          label="Adicionar Novo Item" 
          unelevated 
          rounded
          class="text-weight-bold q-px-md transition-generic hover-scale" 
        />
      </div>

      <!-- TABLE CARD -->
      <q-card class="dashboard-card overflow-hidden">
        <q-table
          class="modern-table"
          :rows="partStore.parts"
          :columns="columns"
          row-key="id"
          :loading="partStore.isLoading"
          no-data-label="Nenhum item encontrado no inventário."
          flat
          :rows-per-page-options="[10, 20, 50]"
          :table-header-class="$q.dark.isActive ? 'bg-dark text-white' : 'bg-grey-1 text-grey-9'"
        >
          <template v-slot:top>
            <div class="full-width flex items-center q-pb-sm">
              <q-input 
                outlined rounded dense debounce="300" v-model="searchQuery" 
                placeholder="Procurar por nome, marca ou código..." 
                class="modern-input"
                style="width: 320px; max-width: 100%;"
              >
                <template v-slot:append> <q-icon name="search" color="grey-6" /> </template>
              </q-input>
            </div>
          </template>
          
          <!-- AVATAR SLOT -->
          <template v-slot:body-cell-photo_url="props">
            <q-td :props="props">
              <q-avatar 
                rounded 
                size="50px" 
                font-size="28px" 
                :color="props.value ? 'transparent' : 'primary-light'" 
                :text-color="props.value ? '' : 'primary'"
                :icon="props.value ? undefined : getCategoryIcon(props.row.category)"
                class="shadow-1"
              >
                <img 
                  v-if="props.value" 
                  :src="getImageUrl(props.value)" 
                  alt="Foto do item"
                  style="object-fit: cover; width: 100%; height: 100%;"
                >
              </q-avatar>
            </q-td>
          </template>

          <template v-slot:body-cell-name="props">
            <q-td :props="props">
              <div class="text-weight-bold text-dark-dynamic">{{ props.value }}</div>
            </q-td>
          </template>

          <template v-slot:body-cell-stock="props">
            <q-td :props="props">
              <q-badge 
                :color="getStockColor(props.row.stock, props.row.minimum_stock)" 
                class="text-weight-bold q-px-sm q-py-xs shadow-1" 
                rounded
              >
                {{ props.row.stock }} / {{ props.row.minimum_stock }}
              </q-badge>
            </q-td>
          </template>

          <template v-slot:body-cell-value="props">
            <q-td :props="props" class="text-weight-medium">
              {{ props.value ? props.value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }) : 'N/A' }}
            </q-td>
          </template>

          <template v-slot:body-cell-actions="props">
            <q-td :props="props" class="text-right">
              <q-btn-dropdown 
                outline 
                rounded 
                color="primary" 
                label="Ações" 
                dense 
                class="text-weight-bold action-dropdown-btn"
                dropdown-icon="expand_more"
              >
                <q-list class="modern-menu q-py-sm" style="min-width: 200px">
                  <q-item clickable v-close-popup @click="openStockDialog(props.row)" class="menu-item-hover">
                    <q-item-section avatar class="min-w-0 q-pr-sm"><q-icon name="sync_alt" color="primary" size="20px" /></q-item-section>
                    <q-item-section class="text-weight-medium">Gerenciar Estoque</q-item-section>
                  </q-item>
                  <q-item clickable v-close-popup @click="openHistoryDialog(props.row)" class="menu-item-hover">
                    <q-item-section avatar class="min-w-0 q-pr-sm"><q-icon name="history" color="teal" size="20px" /></q-item-section>
                    <q-item-section class="text-weight-medium">Ver Histórico</q-item-section>
                  </q-item>
                  <q-separator class="q-my-xs opacity-30" />
                  <q-item clickable v-close-popup @click="openDialog(props.row)" class="menu-item-hover">
                    <q-item-section avatar class="min-w-0 q-pr-sm"><q-icon name="edit" color="grey-7" size="20px" /></q-item-section>
                    <q-item-section class="text-weight-medium">Editar Template</q-item-section>
                  </q-item>
                  <q-item clickable v-close-popup @click="confirmDelete(props.row)" class="menu-item-hover text-negative">
                    <q-item-section avatar class="min-w-0 q-pr-sm"><q-icon name="delete_outline" color="negative" size="20px" /></q-item-section>
                    <q-item-section class="text-weight-medium">Excluir Item</q-item-section>
                  </q-item>
                </q-list>
              </q-btn-dropdown>
            </q-td>
          </template>
        </q-table>
      </q-card>

      <!-- FORM DIALOG -->
      <q-dialog v-model="isDialogOpen" transition-show="scale" transition-hide="scale">
        <q-card class="modern-dialog-card" style="width: 800px; max-width: 95vw;">
          <q-card-section class="dialog-header bg-primary text-white">
            <div class="text-h6 text-weight-bold flex items-center">
              <q-icon :name="isEditing ? 'edit' : 'inventory_2'" size="sm" class="q-mr-sm" />
              {{ isEditing ? 'Editar Template de Item' : 'Adicionar Novo Item' }}
            </div>
          </q-card-section>

          <q-form @submit.prevent="handleSubmit">
            <q-card-section class="row q-col-gutter-xl q-pa-lg">
              
              <!-- COLUNA ESQUERDA: INFOS BÁSICAS -->
              <div class="col-12 col-md-7 q-gutter-y-md">
                <div class="text-subtitle2 text-uppercase text-grey-6 text-weight-bold letter-spacing-1">Informações Básicas</div>
                
                <q-input outlined v-model="formData.name" label="Nome do Item *" :rules="[val => !!val || 'Campo obrigatório']" />
                
                <div class="row q-col-gutter-md">
                  <div class="col-12 col-sm-6">
                    <q-select outlined v-model="formData.category" :options="categoryOptions" label="Categoria *" :rules="[val => !!val || 'Campo obrigatório']" behavior="menu" />
                  </div>
                  <div class="col-12 col-sm-6">
                    <q-input outlined v-model="formData.brand" label="Marca" />
                  </div>
                </div>
                
                <div class="row q-col-gutter-md">
                  <div class="col-12 col-sm-6">
                    <q-input outlined v-model="formData.part_number" label="Part Number / Código" />
                  </div>
                  <div class="col-12 col-sm-6">
                    <q-input outlined v-model="formData.location" label="Localização (Ex: Corredor B)" />
                  </div>
                </div>

                <!-- DADOS PNEU (DINÂMICO) -->
                <template v-if="formData.category === 'Pneu'">
                  <q-separator class="q-my-md opacity-30" />
                  <div class="text-subtitle2 text-uppercase text-grey-6 text-weight-bold letter-spacing-1">Dados Específicos do Pneu</div>
                  <div class="row q-col-gutter-md">
                    <div class="col-12 col-sm-6">
                      <q-input outlined v-model="formData.serial_number" label="Nº de Série / Fogo *" :rules="[val => !!val || 'Obrigatório para pneus']" />
                    </div>
                    <div class="col-12 col-sm-6">
                      <q-input 
                        outlined 
                        v-model.number="formData.lifespan_km" 
                        type="number" 
                        :label="lifespanLabel" 
                        hint="Unidade esperada (ex: km)" 
                        clearable 
                      />
                    </div>
                  </div>
                </template>
              </div>
              
              <!-- COLUNA DIREITA: MÍDIA, VALORES E ESTOQUE -->
              <div class="col-12 col-md-5 q-gutter-y-md">
                <div class="text-subtitle2 text-uppercase text-grey-6 text-weight-bold letter-spacing-1">Valores & Mídia</div>
                
                <q-input outlined v-model.number="formData.value" type="number" label="Custo Unitário" prefix="R$" step="0.01" />
                
                <q-file v-model="photoFile" label="Foto (Opcional)" outlined clearable accept=".jpg, .jpeg, .png, .webp, .avif">
                  <template v-slot:prepend><q-icon name="add_a_photo" color="primary" /></template>
                </q-file>
                <q-img v-if="!photoFile && formData.photo_url" :src="getImageUrl(formData.photo_url)" class="rounded-borders shadow-1" style="height: 120px; width: 100%" fit="cover" />
                
                <q-file v-model="invoiceFile" label="Nota Fiscal (Opcional)" outlined clearable accept=".pdf">
                  <template v-slot:prepend><q-icon name="picture_as_pdf" color="negative" /></template>
                </q-file>

                <q-separator class="q-my-sm opacity-30" />
                <div class="text-subtitle2 text-uppercase text-grey-6 text-weight-bold letter-spacing-1">Estoque</div>
                
                <div class="row q-col-gutter-md">
                  <div class="col-12 col-sm-6">
                    <q-input 
                      outlined 
                      v-model.number="formData.initial_quantity" 
                      type="number" 
                      label="Qtd. Inicial *" 
                      :disable="isEditing" 
                      :hint="isEditing ? 'Use Gerenciar Estoque' : 'Nº de itens'" 
                      :rules="[val => val >= 0 || 'Valor inválido']" 
                    />
                  </div>
                  <div class="col-12 col-sm-6">
                    <q-input outlined v-model.number="formData.minimum_stock" type="number" label="Mínimo Alerta *" :rules="[val => val >= 0 || 'Valor inválido']" />
                  </div>
                </div>
              </div>

              <!-- NOTAS -->
              <div class="col-12">
                 <q-input outlined v-model="formData.notes" type="textarea" label="Anotações Gerais (Opcional)" autogrow rows="2" />
              </div>

            </q-card-section>
            
            <q-card-actions align="right" class="q-pa-md bg-grey-1 dialog-footer">
              <q-btn label="Cancelar" color="grey-7" flat @click="resetForm" v-close-popup class="text-weight-bold" />
              <q-btn :label="isEditing ? 'Salvar Alterações' : 'Adicionar Item'" type="submit" color="primary" unelevated rounded class="text-weight-bold q-px-md" :loading="partStore.isLoading" />
            </q-card-actions>
          </q-form>
        </q-card>
      </q-dialog>

      <!-- COMPONENTS DIALOGS -->
      <ManageStockDialog v-model="isStockDialogOpen" :part="selectedPart" />
      <PartHistoryDialog v-model="isHistoryDialogOpen" :part="selectedPart" />
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useQuasar, type QTableProps } from 'quasar';
import { usePartStore, type PartCreatePayload } from 'stores/part-store';
import { useTerminologyStore } from 'stores/terminology-store';
import type { Part, PartCategory } from 'src/models/part-models';
import ManageStockDialog from 'components/ManageStockDialog.vue';
import PartHistoryDialog from 'components/PartHistoryDialog.vue';
import api from 'src/services/api';

const $q = useQuasar();
const partStore = usePartStore();
const terminologyStore = useTerminologyStore();

const isDialogOpen = ref(false);
const isStockDialogOpen = ref(false);
const isHistoryDialogOpen = ref(false);
const selectedPart = ref<Part | null>(null);

const editingPart = ref<Part | null>(null);
const isEditing = computed(() => !!editingPart.value);
const searchQuery = ref('');
const photoFile = ref<File | null>(null);
const invoiceFile = ref<File | null>(null);

const categoryOptions: PartCategory[] = ["Peça", "Pneu", "Fluído", "Consumível", "Outro"];

const lifespanLabel = computed(() => {
  const unit = terminologyStore.distanceUnit.toUpperCase();
  return `Vida Útil em ${unit} (Opcional)`;
});

const initialFormData: PartCreatePayload = {
  name: '',
  category: 'Peça' as PartCategory,
  part_number: '',
  brand: '',
  initial_quantity: 0,
  minimum_stock: 0,
  location: '',
  notes: '',
  photo_url: null,
  value: null,
  invoice_url: null,
  serial_number: null,
  lifespan_km: null,
};
const formData = ref({ ...initialFormData });

const columns: QTableProps['columns'] = [
  { name: 'photo_url', label: 'Mídia', field: 'photo_url', align: 'center' },
  { name: 'name', label: 'Item (Template)', field: 'name', align: 'left', sortable: true },
  { name: 'category', label: 'Categoria', field: 'category', align: 'left', sortable: true },
  { name: 'value', label: 'Custo Unit.', field: 'value', align: 'right', sortable: true },
  { name: 'stock', label: 'Estoque (Disp.)', field: 'stock', align: 'center', sortable: true },
  { name: 'location', label: 'Local', field: 'location', align: 'left' },
  { name: 'actions', label: 'Ações', field: 'actions', align: 'right' },
];

function getImageUrl(path: string | null): string {
  if (!path) return '';
  const baseUrl = api.defaults.baseURL || '';
  const cleanPath = path.startsWith('/') ? path.substring(1) : path;
  const cleanBaseUrl = baseUrl.endsWith('/') ? baseUrl : `${baseUrl}/`;
  return `${cleanBaseUrl}${cleanPath}`;
}

watch(searchQuery, () => {
  void partStore.fetchParts(searchQuery.value);
});

function getStockColor(current: number, min: number): string {
  if (current <= 0) return 'negative';
  if (current <= min) return 'warning';
  return 'positive';
}

function getCategoryIcon(category: PartCategory): string {
  const iconMap: Record<PartCategory, string> = {
    'Peça': 'settings', 'Fluído': 'opacity', 'Consumível': 'inbox', 'Outro': 'category', 'Pneu': 'album',
  };
  return iconMap[category] || 'inventory_2';
}

function resetForm() {
  editingPart.value = null;
  formData.value = { ...initialFormData };
  photoFile.value = null;
  invoiceFile.value = null;
}

function openDialog(part: Part | null = null) {
  if (part) {
    editingPart.value = { ...part };
    formData.value = {
      ...initialFormData,
      ...part,
      initial_quantity: 0, 
    };
  } else {
    resetForm();
  }
  isDialogOpen.value = true;
}

function openStockDialog(part: Part) {
  selectedPart.value = part;
  isStockDialogOpen.value = true;
}

function openHistoryDialog(part: Part) {
  selectedPart.value = part;
  void partStore.fetchHistory(part.id);
  isHistoryDialogOpen.value = true;
}

async function handleSubmit() {
  const payload: PartCreatePayload = { ...formData.value };
  if (photoFile.value) {
    payload.photo_file = photoFile.value;
  }
  if (invoiceFile.value) {
    payload.invoice_file = invoiceFile.value;
  }
  
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  delete (payload as any).stock; 
  
  const success = isEditing.value && editingPart.value
    ? await partStore.updatePart(editingPart.value.id, payload)
    : await partStore.createPart(payload); 
  
  if (success) {
    isDialogOpen.value = false;
    resetForm();
  }
}

function confirmDelete(part: Part) {
  $q.dialog({
    title: 'Confirmar Exclusão',
    message: `Tem certeza que deseja remover o template <strong>"${part.name}"</strong>? <br><br>Todos os <strong>${part.stock} itens</strong> associados e o seu histórico serão perdidos de forma irreversível.`,
    html: true,
    cancel: { label: 'Cancelar', flat: true, color: 'grey-7' },
    ok: { label: 'Excluir', color: 'negative', rounded: true, unelevated: true },
    class: 'modern-dialog',
    persistent: false,
  }).onOk(() => {
    void partStore.deletePart(part.id);
  });
}

onMounted(() => {
  void partStore.fetchParts();
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
    transition: background-color 0.2s ease, transform 0.2s ease;
    
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

.action-dropdown-btn {
  :deep(.q-btn__content) {
    font-weight: 600;
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
.hover-scale:hover { transform: scale(1.02); }
</style>

<style lang="scss">
/* MENUS GLOBAIS DE DROPDOWN */
.modern-menu {
  border-radius: 12px !important;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08) !important;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.body--dark .modern-menu {
  background: #1a1a1a !important;
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5) !important;
}

.menu-item-hover {
  transition: background-color 0.2s ease;
  border-radius: 8px;
  margin: 2px 8px;
}
</style>