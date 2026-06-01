<template>
  <q-page padding class="modern-page">
    <div class="page-content-container">
      
      <!-- HEADER -->
      <div class="flex items-center justify-between q-mb-xl">
        <div>
          <h1 class="text-h4 text-weight-bolder q-my-none">Gestão de Documentos</h1>
          <div class="text-subtitle1 text-grey-6 q-mt-xs">Centralize e controle os vencimentos de CNHs, CRLVs e mais</div>
        </div>
        <div class="row items-center q-gutter-md">
          <q-btn 
            flat 
            round 
            dense 
            icon="refresh" 
            color="primary" 
            class="transition-generic hover-rotate" 
            @click="documentStore.fetchDocuments()"
          >
            <q-tooltip class="modern-tooltip bg-dark">Atualizar Dados</q-tooltip>
          </q-btn>
          <q-btn
            color="primary"
            icon="add"
            label="Adicionar Documento"
            unelevated
            rounded
            class="text-weight-bold q-px-md transition-generic hover-scale"
            @click="openAddDialog"
          />
        </div>
      </div>

      <!-- TABELA DE DOCUMENTOS -->
      <q-card class="dashboard-card overflow-hidden">
        <q-table
          class="modern-table"
          :rows="documentStore.documents"
          :columns="columns"
          row-key="id"
          :loading="documentStore.isLoading"
          flat
          no-data-label="Nenhum documento cadastrado."
          :rows-per-page-options="[10, 25, 50]"
          :table-header-class="$q.dark.isActive ? 'bg-dark text-white' : 'bg-grey-1 text-grey-9'"
        >
          <!-- COLUNA: TIPO DE DOCUMENTO -->
          <template v-slot:body-cell-document_type="props">
            <q-td :props="props">
              <span class="text-weight-bold text-dark-dynamic">{{ props.value }}</span>
            </q-td>
          </template>
          
          <!-- COLUNA: ASSOCIADO A -->
          <template v-slot:body-cell-owner_info="props">
            <q-td :props="props">
              <span class="text-weight-medium text-grey-8" :class="$q.dark.isActive ? 'text-grey-4' : ''">{{ props.value }}</span>
            </q-td>
          </template>

          <!-- COLUNA: VENCIMENTO -->
          <template v-slot:body-cell-expiry_date="props">
            <q-td :props="props" class="text-center">
              <q-badge
                :color="getExpiryStatusColor(props.row.expiry_date).color"
                :text-color="getExpiryStatusColor(props.row.expiry_date).textColor"
                class="text-weight-bold q-px-sm q-py-xs shadow-1"
                rounded
              >
                <q-icon name="event" size="14px" class="q-mr-xs" />
                {{ formatDate(props.row.expiry_date) }}
              </q-badge>
            </q-td>
          </template>

          <!-- COLUNA: AÇÕES -->
          <template v-slot:body-cell-actions="props">
            <q-td :props="props" class="text-right">
              <div class="row justify-end q-gutter-x-sm">
                <q-btn 
                  :href="`${backendBaseUrl}${props.row.file_url}`" 
                  target="_blank" 
                  dense flat round 
                  color="primary" 
                  icon="visibility" 
                  class="action-btn"
                >
                 <q-tooltip class="modern-tooltip bg-dark">Ver Documento</q-tooltip>
                </q-btn>
                <q-btn 
                  dense flat round 
                  color="negative" 
                  icon="delete_outline" 
                  @click="confirmDelete(props.row)" 
                  class="action-btn"
                >
                  <q-tooltip class="modern-tooltip bg-negative">Excluir Documento</q-tooltip>
                </q-btn>
              </div>
            </q-td>
          </template>
        </q-table>
      </q-card>

      <!-- DIÁLOGO PARA ADICIONAR NOVO DOCUMENTO -->
      <q-dialog v-model="isDialogOpen" transition-show="scale" transition-hide="scale">
        <q-card class="modern-dialog-card" style="width: 550px; max-width: 95vw;">
          <q-card-section class="dialog-header bg-primary text-white">
            <div class="text-h6 text-weight-bold flex items-center">
              <q-icon name="post_add" size="sm" class="q-mr-sm" />
              Novo Documento
            </div>
          </q-card-section>

          <q-form @submit="onSubmit">
            <q-card-section class="q-gutter-y-md q-pa-lg">
              
              <div class="text-subtitle2 text-uppercase text-grey-6 text-weight-bold letter-spacing-1">Classificação</div>
              <div class="row q-col-gutter-md">
                <div class="col-12 col-sm-6">
                  <q-select
                    outlined
                    v-model="newDocument.document_type"
                    :options="documentTypeOptions"
                    label="Tipo de Documento *"
                    :rules="[val => !!val || 'Campo obrigatório']"
                    behavior="menu"
                    class="modern-input"
                  >
                    <template v-slot:prepend><q-icon name="folder" color="primary" /></template>
                  </q-select>
                </div>
                <div class="col-12 col-sm-6">
                  <q-select
                    outlined
                    v-model="ownerType"
                    :options="['Veículo', 'Motorista']"
                    label="Associar a *"
                    :rules="[val => !!val || 'Campo obrigatório']"
                    behavior="menu"
                    class="modern-input"
                  >
                    <template v-slot:prepend><q-icon name="link" color="grey-6" /></template>
                  </q-select>
                </div>
              </div>

              <!-- SELECT CONDICIONAL -->
              <q-select
                v-if="ownerType === 'Veículo'"
                outlined
                v-model="newDocument.vehicle_id"
                :options="vehicleOptions"
                label="Selecione o Veículo *"
                emit-value
                map-options
                :rules="[val => !!val || 'Selecione um veículo']"
                behavior="menu"
                class="modern-input"
              >
                <template v-slot:prepend><q-icon name="directions_car" color="primary" /></template>
              </q-select>

              <q-select
                v-if="ownerType === 'Motorista'"
                outlined
                v-model="newDocument.driver_id"
                :options="driverOptions"
                label="Selecione o Motorista *"
                emit-value
                map-options
                :rules="[val => !!val || 'Selecione um motorista']"
                behavior="menu"
                class="modern-input"
              >
                <template v-slot:prepend><q-icon name="person" color="primary" /></template>
              </q-select>

              <q-separator class="q-my-md opacity-30" />
              <div class="text-subtitle2 text-uppercase text-grey-6 text-weight-bold letter-spacing-1">Dados e Arquivo</div>

              <q-input
                outlined
                v-model="newDocument.expiry_date"
                label="Data de Vencimento *"
                mask="####-##-##"
                class="modern-input"
                :rules="[
                  val => !!val || 'Campo obrigatório',
                  val => /^\d{4}-\d{2}-\d{2}$/.test(val) || 'Formato de data inválido (YYYY-MM-DD)'
                ]"
              >
                <template v-slot:append>
                  <q-icon name="event" class="cursor-pointer" color="primary">
                    <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                      <q-date v-model="newDocument.expiry_date" mask="YYYY-MM-DD" color="primary">
                        <div class="row items-center justify-end">
                          <q-btn v-close-popup label="Fechar" color="primary" flat />
                        </div>
                      </q-date>
                    </q-popup-proxy>
                  </q-icon>
                </template>
              </q-input>

              <q-file
                outlined
                v-model="newDocument.file"
                label="Anexar arquivo PDF ou Imagem *"
                accept=".pdf,.jpg,.jpeg,.png"
                class="modern-input"
                :rules="[val => !!val || 'É necessário anexar um arquivo']"
              >
                <template v-slot:prepend><q-icon name="attach_file" color="grey-6" /></template>
              </q-file>

              <q-input
                outlined
                v-model="newDocument.notes"
                label="Notas (Opcional)"
                type="textarea"
                rows="2"
                autogrow
                class="modern-input"
              />
            </q-card-section>

            <q-card-actions align="right" class="q-pa-md bg-grey-1 dialog-footer">
              <q-btn label="Cancelar" flat color="grey-7" v-close-popup class="text-weight-bold" />
              <q-btn label="Salvar Documento" type="submit" color="primary" unelevated rounded class="text-weight-bold q-px-md" :loading="documentStore.isLoading" />
            </q-card-actions>
          </q-form>
        </q-card>
      </q-dialog>

    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useQuasar, type QTableProps } from 'quasar';
import { useDocumentStore, type DocumentCreatePayload } from 'stores/document-store';
import { useVehicleStore } from 'stores/vehicle-store';
import { useUserStore } from 'stores/user-store';
import type { DocumentPublic } from 'src/models/document-models';
import type { User } from 'src/models/auth-models';
import { format, parseISO, differenceInDays } from 'date-fns';
import { api } from 'boot/axios';

const $q = useQuasar();
const baseUrl = api.defaults.baseURL || '';
const backendBaseUrl = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
const documentStore = useDocumentStore();
const vehicleStore = useVehicleStore();
const userStore = useUserStore();

// --- Lógica da Tabela ---
const columns: QTableProps['columns'] = [
  { name: 'document_type', required: true, label: 'Tipo', align: 'left', field: 'document_type', sortable: true },
  { name: 'owner_info', label: 'Associado a', field: 'owner_info', align: 'left', sortable: true },
  { name: 'expiry_date', label: 'Vencimento', field: 'expiry_date', align: 'center', sortable: true },
  { name: 'notes', label: 'Notas', field: 'notes', align: 'left', sortable: false, style: 'max-width: 300px; white-space: normal;' },
  { name: 'actions', label: 'Ações', field: 'actions', align: 'right', sortable: false },
];

function formatDate(dateString: string): string {
  if (!dateString) return 'N/A';
  return format(parseISO(dateString), 'dd/MM/yyyy');
}

function getExpiryStatusColor(dateString: string): { color: string, textColor: string } {
  const daysUntilExpiry = differenceInDays(parseISO(dateString), new Date());
  if (daysUntilExpiry < 0) return { color: 'negative', textColor: 'white' };
  if (daysUntilExpiry <= 30) return { color: 'warning', textColor: 'black' };
  return { color: 'positive', textColor: 'white' };
}

// --- Lógica do Diálogo e Formulário ---
interface NewDocumentForm {
  document_type: string;
  expiry_date: string;
  notes: string;
  vehicle_id: number | undefined;
  driver_id: number | undefined;
  file: File | null;
}

const isDialogOpen = ref(false);
const ownerType = ref<'Veículo' | 'Motorista' | null>(null);

const initialNewDocumentState: NewDocumentForm = {
  document_type: '',
  expiry_date: '',
  notes: '',
  vehicle_id: undefined,
  driver_id: undefined,
  file: null,
};

const newDocument = ref<NewDocumentForm>({ ...initialNewDocumentState });

const documentTypeOptions = ['CNH', 'CRLV', 'ANTT', 'ASO', 'Seguro', 'Outro'];
const vehicleOptions = computed(() => vehicleStore.vehicles.map(v => ({
  label: `${v.brand} ${v.model} (${v.license_plate || v.identifier})`,
  value: v.id
})));

const drivers = computed(() => userStore.users.filter(u => u.role === 'driver'));
const driverOptions = computed(() => drivers.value.map((d: User) => ({
  label: d.full_name,
  value: d.id
})));

watch(ownerType, () => {
  newDocument.value.vehicle_id = undefined;
  newDocument.value.driver_id = undefined;
});

function openAddDialog() {
  newDocument.value = { ...initialNewDocumentState };
  ownerType.value = null;
  isDialogOpen.value = true;
}

async function onSubmit() {
  if (!newDocument.value.file) return;

  const payload: DocumentCreatePayload = {
    document_type: newDocument.value.document_type,
    expiry_date: newDocument.value.expiry_date,
    notes: newDocument.value.notes,
    file: newDocument.value.file,
    ...(newDocument.value.vehicle_id !== undefined && { vehicle_id: newDocument.value.vehicle_id }),
    ...(newDocument.value.driver_id !== undefined && { driver_id: newDocument.value.driver_id }),
  };

  await documentStore.createDocument(payload);
  isDialogOpen.value = false;
}

function confirmDelete(document: DocumentPublic) {
  $q.dialog({
    title: 'Confirmar Remoção',
    message: `Tem a certeza de que deseja remover o documento <strong>"${document.document_type}"</strong> associado a <strong>"${document.owner_info}"</strong>? Esta ação não pode ser desfeita.`,
    html: true,
    cancel: { label: 'Cancelar', flat: true, color: 'grey-7' },
    persistent: false,
    ok: { label: 'Remover', color: 'negative', rounded: true, unelevated: true },
    class: 'modern-dialog'
  }).onOk(() => {
    void documentStore.deleteDocument(document.id);
  });
}

// --- Ciclo de Vida ---
onMounted(() => {
  void documentStore.fetchDocuments();
  void vehicleStore.fetchAllVehicles();
  void userStore.fetchAllUsers(); 
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

.text-dark-dynamic {
  color: #111827;
  .body--dark & { color: #f3f4f6; }
}

.opacity-30 { opacity: 0.3; }
.letter-spacing-1 { letter-spacing: 1px; }

.transition-generic { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.hover-rotate:hover { transform: rotate(180deg); }
.hover-scale:hover { transform: scale(1.02); }

.modern-tooltip {
  border-radius: 8px !important;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
}
</style>r