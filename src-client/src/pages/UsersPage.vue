<template>
  <q-page padding class="modern-page">
    <div class="page-content-container">
      
      <div class="flex items-center justify-between q-mb-xl">
        <div>
          <h1 class="text-h4 text-weight-bolder q-my-none">Gestão de Equipe</h1>
          <div class="text-subtitle1 text-grey-6 q-mt-xs">Gerencie motoristas e administradores do sistema</div>
        </div>
        <q-btn 
          @click="openCreateDialog" 
          color="primary" 
          icon="person_add" 
          label="Adicionar Usuário" 
          unelevated 
          rounded 
          class="text-weight-bold q-px-md transition-generic hover-scale" 
        />
      </div>

      <q-table
        @row-click="goToUserDetails"
        class="modern-table cursor-pointer"
        card-class="dashboard-card"
        :rows="userStore.users"
        :columns="columns"
        row-key="id"
        :loading="userStore.isLoading"
        no-data-label="Nenhum usuário cadastrado"
        flat
        :table-header-class="$q.dark.isActive ? 'bg-dark text-white' : 'bg-grey-1 text-grey-9'"
      >
        <template v-slot:body-cell-user_info="props">
          <q-td :props="props">
            <div class="row items-center no-wrap">
              <q-avatar size="40px" :color="props.row.avatar_url ? 'transparent' : 'primary-light'" :text-color="props.row.avatar_url ? '' : 'primary'" class="q-mr-md shadow-1">
                <img v-if="props.row.avatar_url" :src="props.row.avatar_url" />
                <span v-else class="text-weight-bold">{{ props.row.full_name ? props.row.full_name.charAt(0).toUpperCase() : 'U' }}</span>
              </q-avatar>
              <div class="column">
                <span class="text-weight-bold text-dark-dynamic" style="line-height: 1.2;">{{ props.row.full_name }}</span>
                <span class="text-caption text-grey-5">{{ props.row.email }}</span>
              </div>
            </div>
          </q-td>
        </template>

        <template v-slot:body-cell-role="props">
          <q-td :props="props">
            <q-badge 
              :color="getRoleColor(props.value)" 
              :text-color="getRoleTextColor(props.value)"
              class="text-weight-bold q-px-sm q-py-xs"
              rounded
            >
              {{ getRoleLabel(props.value) }}
            </q-badge>
          </q-td>
        </template>

        <template v-slot:body-cell-is_active="props">
          <q-td :props="props">
            <q-badge :color="props.value ? 'positive' : 'grey-5'" class="text-weight-bold q-pa-xs">
              {{ props.value ? 'Ativo' : 'Inativo' }}
            </q-badge>
          </q-td>
        </template>

        <template v-slot:body-cell-actions="props">
          <q-td :props="props">
            <div class="row justify-end q-gutter-x-sm">
              <q-btn @click.stop="openEditDialog(props.row)" flat round dense icon="edit" color="grey-6" class="action-btn">
                <q-tooltip class="modern-tooltip bg-dark">Editar Usuário</q-tooltip>
              </q-btn>
              <q-btn @click.stop="promptToDelete(props.row)" flat round dense icon="delete_outline" color="negative" class="action-btn">
                <q-tooltip class="modern-tooltip bg-negative">Excluir Usuário</q-tooltip>
              </q-btn>
            </div>
          </q-td>
        </template>
      </q-table>

      <q-dialog v-model="isFormDialogOpen" transition-show="scale" transition-hide="scale">
        <q-card class="modern-dialog-card" style="width: 600px; max-width: 95vw;">
          <q-card-section class="dialog-header bg-primary text-white">
            <div class="text-h6 text-weight-bold flex items-center">
              <q-icon :name="isEditing ? 'manage_accounts' : 'person_add'" size="sm" class="q-mr-sm" />
              {{ isEditing ? 'Editar Usuário' : 'Novo Usuário' }}
            </div>
          </q-card-section>

          <q-form @submit.prevent="onFormSubmit">
            <q-card-section class="q-gutter-y-md q-pa-lg">
              
              <div class="row q-col-gutter-md">
                <div class="col-12 col-sm-7">
                  <q-input outlined v-model="formData.full_name" label="Nome Completo *" :rules="[val => !!val || 'Campo obrigatório']" />
                </div>
                <div class="col-12 col-sm-5">
                  <q-input outlined v-model="formData.employee_id" label="ID Func. (Opcional)" hint="Ex: TRC-001" />
                </div>
              </div>

              <q-input outlined v-model="formData.email" type="email" label="E-mail *" :rules="[val => !!val || 'Campo obrigatório']">
                <template v-slot:prepend><q-icon name="mail" color="grey-6" /></template>
              </q-input>
              
              <q-input outlined v-model="formData.avatar_url" label="URL da Foto (Opcional)">
                <template v-slot:prepend><q-icon name="link" color="grey-6" /></template>
              </q-input>
              
              <q-separator class="q-my-md opacity-30" />
              <div class="text-subtitle2 text-uppercase text-grey-6 text-weight-bold letter-spacing-1">Acesso e Permissões</div>

              <div class="row q-col-gutter-md">
                <div class="col-12 col-sm-6">
                  <q-select
                    outlined
                    v-model="formData.role"
                    :options="roleOptions"
                    label="Função no Sistema *"
                    emit-value
                    map-options
                    :disable="isRoleSelectorDisabled"
                    behavior="menu"
                  >
                    <template v-if="isRoleSelectorDisabled" v-slot:append>
                      <q-icon name="admin_panel_settings" color="amber-8">
                        <q-tooltip class="modern-tooltip bg-dark">Apenas Super Admins podem alterar funções.</q-tooltip>
                      </q-icon>
                    </template>
                  </q-select>
                </div>
                <div class="col-12 col-sm-6">
                  <q-input 
                    outlined 
                    v-model="formData.password" 
                    type="password" 
                    :label="isEditing ? 'Nova Senha (Opcional)' : 'Senha Inicial *'" 
                    :rules="isEditing ? [] : [val => !!val || 'Campo obrigatório']" 
                  >
                    <template v-slot:prepend><q-icon name="lock" color="grey-6" /></template>
                  </q-input>
                </div>
              </div>

              <q-toggle 
                v-if="isEditing" 
                v-model="formData.is_active" 
                color="positive"
                :label="formData.is_active ? 'Conta Ativada' : 'Conta Suspensa'" 
                class="text-weight-medium q-mt-md"
              />
              
            </q-card-section>
            
            <q-card-actions align="right" class="q-pa-md bg-grey-1 dialog-footer">
              <q-btn flat label="Cancelar" color="grey-7" v-close-popup class="text-weight-bold" />
              <q-btn type="submit" unelevated rounded color="primary" label="Salvar Usuário" :loading="isSubmitting" class="text-weight-bold q-px-md" />
            </q-card-actions>
          </q-form>
        </q-card>
      </q-dialog>

    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useQuasar, type QTableColumn } from 'quasar';
import { useUserStore } from 'stores/user-store';
import { useAuthStore } from 'stores/auth-store';
import { useDemoStore } from 'stores/demo-store';
import { useRouter } from 'vue-router';
import { isAxiosError } from 'axios';
import type { User } from 'src/models/auth-models';
import type { UserCreate, UserUpdate } from 'src/models/user-models';

const demoStore = useDemoStore();
const $q = useQuasar();
const userStore = useUserStore();
const authStore = useAuthStore();
const router = useRouter();
const isFormDialogOpen = ref(false);
const isSubmitting = ref(false);
const editingUserId = ref<number | null>(null);

const isEditing = computed(() => editingUserId.value !== null);

const roleOptions = [
  { label: 'Gestor (Administrador)', value: 'cliente_ativo' },
  { label: 'Gestor Limitado (Demo)', value: 'cliente_demo' },
  { label: 'Motorista', value: 'driver' }
];

const formData = ref<Partial<UserCreate & UserUpdate>>({});

const isRoleSelectorDisabled = computed(() => {
  return !authStore.isSuperuser;
});

const isDriverLimitReached = computed(() => {
  if (!authStore.isDemo) {
    return false;
  }
  const limit = authStore.user?.organization?.driver_limit;
  if (limit === undefined || limit === null || limit < 0) {
    return false;
  }
  const currentCount = demoStore.stats?.driver_count ?? 0;
  return currentCount >= limit;
});

function showUpgradeDialog() {
  $q.dialog({
    title: 'Limite do Plano Demo Atingido',
    message: `Você atingiu o limite de ${authStore.user?.organization?.driver_limit} motoristas permitidos no plano de demonstração. Entre em contato com a equipe comercial para atualizar seu plano e liberar registros ilimitados.`,
    ok: { label: 'Entendido', color: 'primary', rounded: true, unelevated: true },
    class: 'modern-dialog',
    persistent: false
  });
}

const columns: QTableColumn[] = [
  { name: 'user_info', label: 'Usuário', field: 'full_name', align: 'left', sortable: true },
  { name: 'employee_id', label: 'ID', field: 'employee_id', align: 'left', sortable: true },
  { name: 'role', label: 'Função', field: 'role', align: 'left', sortable: true },
  { name: 'is_active', label: 'Status', field: 'is_active', align: 'center' },
  { name: 'actions', label: 'Ações', field: 'actions', align: 'right' },
];

function getRoleLabel(roleValue: string): string {
  const role = roleOptions.find(r => r.value === roleValue);
  return role ? role.label : roleValue;
}

function getRoleColor(roleValue: string): string {
  if (roleValue.includes('cliente')) return 'amber-2';
  return 'blue-1';
}

function getRoleTextColor(roleValue: string): string {
  if (roleValue.includes('cliente')) return 'amber-9';
  return 'blue-9';
}

function goToUserDetails(evt: Event, row: User) {
  void router.push({ name: 'user-stats', params: { id: row.id } });
}

function resetForm() {
  editingUserId.value = null;
  formData.value = { full_name: '', email: '', role: 'driver', password: '', is_active: true, employee_id: '' };
}

function openCreateDialog() {
  if (isDriverLimitReached.value && formData.value.role === 'driver') {
    showUpgradeDialog();
    return; 
  }
  resetForm();
  isFormDialogOpen.value = true;
}

function openEditDialog(user: User) {
  resetForm();
  editingUserId.value = user.id;
  formData.value = { 
    ...user, 
    avatar_url: user.avatar_url || '', 
    password: '' 
  };
  isFormDialogOpen.value = true;
}

async function onFormSubmit() {
  isSubmitting.value = true;
  try {
    const payload = { ...formData.value };

    if (
      !isEditing.value && 
      payload.role === 'driver' && 
      isDriverLimitReached.value 
    ) {
      showUpgradeDialog();
      isSubmitting.value = false;
      return;
    }

    if (isEditing.value && !payload.password) {
      delete payload.password;
    }

    if (isEditing.value && editingUserId.value) {
      await userStore.updateUser(editingUserId.value, payload as UserUpdate);
    } else {
      await userStore.addNewUser(payload as UserCreate);
      if (authStore.isDemo) {
        void demoStore.fetchDemoStats();
      }
    }
    isFormDialogOpen.value = false;
    $q.notify({ type: 'positive', message: 'Usuário salvo com sucesso!' });
  } catch (error) {
    let message = 'Erro ao salvar o usuário.';
    if (isAxiosError(error) && error.response?.data?.detail) {
      message = error.response.data.detail as string;
    }
    $q.notify({ type: 'negative', message });
  } finally {
    isSubmitting.value = false;
  }
}

function promptToDelete(user: User) {
  $q.dialog({
    title: 'Confirmar Exclusão',
    message: `Tem certeza que deseja excluir o usuário <strong>${user.full_name}</strong>? Todo o histórico associado será impactado.`,
    html: true,
    cancel: { label: 'Cancelar', flat: true, color: 'grey-7' },
    ok: { label: 'Excluir', color: 'negative', rounded: true, unelevated: true },
    class: 'modern-dialog',
    persistent: false,
  }).onOk(() => {
    void userStore.deleteUser(user.id);
  });
}

onMounted(async () => {
  await userStore.fetchAllUsers();
  if (authStore.isDemo) {
    void demoStore.fetchDemoStats();
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

/* UTILITÁRIOS */
.bg-primary-light { background-color: rgba($primary, 0.15); }
.text-dark-dynamic {
  color: #111827;
  .body--dark & { color: #f3f4f6; }
}

.action-btn {
  transition: all 0.2s;
  &:hover { background-color: rgba(0,0,0,0.05); }
  .body--dark &:hover { background-color: rgba(255,255,255,0.05); }
}

.opacity-30 { opacity: 0.3; }
.letter-spacing-1 { letter-spacing: 1px; }
.transition-generic { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.hover-scale:hover { transform: scale(1.02); }

.modern-tooltip {
  border-radius: 8px !important;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
}
</style>