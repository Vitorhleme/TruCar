<template>
  <q-page padding class="modern-page">
    <div class="page-content-container">

      <!-- MÓDULO: FRETE -->
      <div v-if="authStore.userSector === 'frete'" class="row q-col-gutter-xl">
        
        <!-- MURAL DE FRETES -->
        <div class="col-12 col-lg-6">
          <div class="flex items-center justify-between q-mb-md">
            <div>
              <h1 class="text-h5 text-weight-bold q-my-none">Mural de Fretes Abertos</h1>
              <div class="text-caption text-grey-6 q-mt-xs">Encontre e aceite novas viagens</div>
            </div>
            <q-btn flat round dense icon="refresh" color="primary" class="transition-generic hover-rotate" :loading="freightOrderStore.isLoading" @click="refreshFreightData">
              <q-tooltip class="modern-tooltip bg-dark">Atualizar</q-tooltip>
            </q-btn>
          </div>
          
          <q-card class="dashboard-card">
            <q-list class="q-pa-sm">
              <q-item v-if="freightOrderStore.isLoading && freightOrderStore.openOrders.length === 0" class="q-pa-md">
                <q-item-section avatar><q-skeleton type="QAvatar" size="40px" /></q-item-section>
                <q-item-section><q-skeleton type="text" width="80%" /><q-skeleton type="text" width="50%" /></q-item-section>
              </q-item>
              
              <div v-if="!freightOrderStore.isLoading && freightOrderStore.openOrders.length === 0" class="text-center text-grey-5 q-pa-xl column items-center">
                <q-icon name="inbox" size="3.5em" class="q-mb-md opacity-50" />
                <div class="text-weight-medium">Nenhum frete aberto no momento.</div>
              </div>
              
              <q-item 
                v-else 
                v-for="order in freightOrderStore.openOrders" 
                :key="order.id" 
                clickable 
                v-ripple
                class="modern-list-item transition-generic"
                @click="openClaimDialog(order)"
              >
                <q-item-section avatar>
                  <q-avatar color="primary-light" text-color="primary" icon="add_shopping_cart" rounded />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold text-dark-dynamic">{{ order.description || 'Frete sem descrição' }}</q-item-label>
                  <q-item-label caption class="q-mt-xs flex items-center text-grey-7">
                    <q-icon name="place" size="xs" class="q-mr-xs"/> {{ order.stop_points.length }} paradas 
                    <q-icon name="person" size="xs" class="q-ml-sm q-mr-xs"/> Cliente: <span class="text-weight-medium q-ml-xs">{{ order.client.name }}</span>
                  </q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-btn flat round dense icon="chevron_right" color="grey-5" />
                </q-item-section>
              </q-item>
            </q-list>
          </q-card>
        </div>

        <!-- MINHAS TAREFAS -->
        <div class="col-12 col-lg-6">
          <div class="flex items-center justify-between q-mb-md">
            <div>
              <h1 class="text-h5 text-weight-bold q-my-none">Minhas Tarefas</h1>
              <div class="text-caption text-grey-6 q-mt-xs">Acompanhe seus fretes em andamento</div>
            </div>
            <q-btn flat round dense icon="refresh" color="primary" class="transition-generic hover-rotate" :loading="freightOrderStore.isLoading" @click="refreshFreightData">
               <q-tooltip class="modern-tooltip bg-dark">Atualizar</q-tooltip>
            </q-btn>
          </div>
          
          <q-card class="dashboard-card">
            <q-list class="q-pa-sm">
              <q-item v-if="freightOrderStore.isLoading && freightOrderStore.myPendingOrders.length === 0" class="q-pa-md">
                <q-item-section avatar><q-skeleton type="QAvatar" size="40px" /></q-item-section>
                <q-item-section><q-skeleton type="text" width="80%" /><q-skeleton type="text" width="50%" /></q-item-section>
              </q-item>
              
              <div v-if="!freightOrderStore.isLoading && freightOrderStore.myPendingOrders.length === 0" class="text-center text-grey-5 q-pa-xl column items-center">
                <q-icon name="assignment_turned_in" size="3.5em" class="q-mb-md opacity-50" />
                <div class="text-weight-medium">Você não tem tarefas ativas.</div>
              </div>
              
              <q-item 
                v-else 
                v-for="order in freightOrderStore.myPendingOrders" 
                :key="order.id" 
                clickable 
                v-ripple
                :class="['modern-list-item transition-generic', { 'active-task': order.status === 'Em Trânsito' }]"
                @click="openDriverDialog(order)"
              >
                <q-item-section avatar>
                  <q-avatar 
                    :color="order.status === 'Em Trânsito' ? 'primary' : 'grey-2'" 
                    :text-color="order.status === 'Em Trânsito' ? 'white' : 'grey-7'" 
                    :icon="order.status === 'Em Trânsito' ? 'local_shipping' : 'assignment'" 
                    rounded 
                  />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold text-dark-dynamic">{{ order.description || 'Frete sem descrição' }}</q-item-label>
                  <q-item-label caption class="q-mt-xs">
                    <q-badge :color="order.status === 'Em Trânsito' ? 'primary' : 'grey-6'" outline class="text-weight-bold">
                      {{ order.status }}
                    </q-badge>
                  </q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-btn flat round dense icon="chevron_right" color="grey-5" />
                </q-item-section>
              </q-item>
            </q-list>
          </q-card>
        </div>
      </div>

      <!-- MÓDULO: GERAL (AGRONEGÓCIO / SERVIÇOS / ETC) -->
      <div v-else>
        <!-- HEADER -->
        <div class="flex items-center justify-between q-mb-xl">
          <div>
            <h1 class="text-h4 text-weight-bolder q-my-none">{{ terminologyStore.journeyPageTitle }}</h1>
            <div class="text-subtitle1 text-grey-6 q-mt-xs">Gerencie e acompanhe as operações da frota.</div>
          </div>
          <q-btn 
            v-if="!journeyStore.currentUserActiveJourney" 
            @click="openStartDialog" 
            color="primary" 
            icon="add_road" 
            :label="terminologyStore.startJourneyButtonLabel" 
            unelevated
            rounded
            class="text-weight-bold q-px-md" 
          />
        </div>

        <!-- DEMO BANNER -->
        <q-banner v-if="isDemo" rounded class="premium-banner q-mb-xl shadow-2">
          <template v-slot:avatar>
            <q-icon name="history_toggle_off" color="amber-8" size="md" />
          </template>
          <div class="text-weight-medium text-dark-dynamic text-subtitle1">
            No Plano Demo, o histórico é limitado aos últimos 7 dias.
          </div>
          <div class="text-body2 text-grey-7">Faça o upgrade para acessar todos os dados retroativos.</div>
          <template v-slot:action>
            <q-btn unelevated rounded color="amber-8" text-color="white" label="Fazer Upgrade" @click="showHistoryUpgradeDialog" class="text-weight-bold q-px-md" />
          </template>
        </q-banner>

        <!-- ACTIVE JOURNEY CARD -->
        <q-card v-if="journeyStore.currentUserActiveJourney" class="active-journey-card q-mb-xl text-white shadow-3">
          <q-card-section class="q-pa-lg">
            <div class="row items-center justify-between">
              <div class="row items-center">
                <q-avatar color="white" text-color="primary" icon="sensors" size="lg" class="q-mr-md shadow-1" />
                <div>
                  <div class="text-h6 text-weight-bold">Você tem uma {{ terminologyStore.journeyNoun.toLowerCase() }} em andamento</div>
                  <div class="text-subtitle2 opacity-80" v-if="journeyStore.currentUserActiveJourney.vehicle">
                    {{ terminologyStore.vehicleNoun }}: <strong>{{ journeyStore.currentUserActiveJourney.vehicle.brand }} {{ journeyStore.currentUserActiveJourney.vehicle.model }}</strong>
                  </div>
                </div>
              </div>
              <q-btn 
                @click="openEndDialog()" 
                color="white" 
                text-color="primary"
                icon="stop_circle"
                :label="`Finalizar ${terminologyStore.journeyNoun}`" 
                unelevated 
                rounded
                class="text-weight-bold q-px-md" 
              />
            </div>
          </q-card-section>
        </q-card>
        
        <!-- HISTÓRICO (TABLE) -->
        <q-table
          :title="terminologyStore.journeyHistoryTitle"
          :rows="journeyStore.journeys"
          :columns="columns"
          row-key="id"
          :loading="journeyStore.isLoading"
          no-data-label="Nenhuma operação encontrada"
          card-class="dashboard-card"
          flat
          :table-header-class="$q.dark.isActive ? 'bg-dark text-white' : 'bg-grey-1 text-grey-9'"
        >
          <template v-slot:body-cell-status="props">
            <q-td :props="props">
              <q-badge :color="props.row.is_active ? 'positive' : 'grey-5'" class="text-weight-bold q-pa-xs">
                {{ props.row.is_active ? 'Ativa' : 'Finalizada' }}
              </q-badge>
            </q-td>
          </template>

          <template v-slot:body-cell-actions="props">
            <q-td :props="props">
              <div class="row justify-end q-gutter-x-sm">
                <q-btn v-if="props.row.is_active" @click="openEndDialog(props.row)" flat round dense icon="event_busy" color="primary" :title="`Finalizar ${terminologyStore.journeyNoun}`">
                  <q-tooltip class="modern-tooltip bg-dark">Finalizar</q-tooltip>
                </q-btn>
                <q-btn v-if="authStore.isManager" @click="promptToDeleteJourney(props.row)" flat round dense icon="delete_outline" color="negative" :title="`Excluir ${terminologyStore.journeyNoun}`">
                  <q-tooltip class="modern-tooltip bg-negative">Excluir</q-tooltip>
                </q-btn>
              </div>
            </q-td>
          </template>
        </q-table>
      </div>
      
      <!-- DIALOGS -->
      <q-dialog v-model="isClaimDialogOpen" @hide="onClaimDialogClose">
        <ClaimFreightDialog v-if="selectedOrderForAction" :order="selectedOrderForAction" @close="isClaimDialogOpen = false" />
      </q-dialog>

      <q-dialog v-model="isDriverDialogOpen">
        <DriverFreightDialog :order="freightOrderStore.activeOrderDetails" @close="isDriverDialogOpen = false" />
      </q-dialog>

      <q-dialog v-model="isStartDialogOpen" transition-show="scale" transition-hide="scale">
        <q-card class="modern-dialog-card" style="width: 500px; max-width: 90vw;">
          <q-card-section class="dialog-header bg-primary text-white">
            <div class="text-h6 text-weight-bold flex items-center">
              <q-icon name="play_arrow" size="sm" class="q-mr-sm" />
              Iniciar Nova {{ terminologyStore.journeyNoun }}
            </div>
          </q-card-section>
          
          <q-form @submit.prevent="handleStartJourney">
            <q-card-section class="q-gutter-y-md q-pa-md">
              <q-select outlined v-model="startForm.vehicle_id" :options="vehicleOptions" :label="`${terminologyStore.vehicleNoun} *`" emit-value map-options :rules="[val => !!val || 'Selecione um item']" behavior="menu" />
              <q-select v-if="authStore.userSector === 'agronegocio'" outlined v-model="startForm.implement_id" :options="implementOptions" label="Implemento (Opcional)" emit-value map-options clearable :loading="implementStore.isLoading" behavior="menu" />
              
              <q-input v-if="authStore.userSector === 'agronegocio'" outlined v-model.number="startForm.start_engine_hours" type="number" label="Horas Iniciais *" :rules="[val => val !== null && val !== undefined && val >= 0 || 'Valor deve ser positivo']" />
              <q-input v-else outlined v-model.number="startForm.start_mileage" type="number" label="KM Inicial *" :rules="[val => val !== null && val !== undefined && val >= 0 || 'Valor deve ser positivo']" />
              
              <q-input outlined v-model="startForm.trip_description" :label="`Descrição da ${terminologyStore.journeyNoun} (Opcional)`" autogrow />
              
              <q-separator class="q-my-md opacity-30" />
              <div class="text-subtitle2 text-uppercase text-grey-6 text-weight-bold letter-spacing-1">Destino (Opcional)</div>

              <q-input 
                outlined 
                v-model="startForm.destination_cep" 
                label="CEP do Destino" 
                mask="#####-###"
                unmasked-value
                :loading="isCepLoading"
                @blur="handleJourneyCepBlur"
              >
                <template v-slot:prepend><q-icon name="location_on" color="primary" /></template>
              </q-input>

              <q-input outlined v-model="startForm.destination_street" label="Rua / Logradouro" />

              <div class="row q-col-gutter-md">
                  <div class="col-8"><q-input outlined v-model="startForm.destination_neighborhood" label="Bairro" /></div>
                  <div class="col-4"><q-input outlined v-model="startForm.destination_number" label="Nº" /></div>
              </div>
              <div class="row q-col-gutter-md">
                  <div class="col-8"><q-input outlined v-model="startForm.destination_city" label="Cidade" /></div>
                  <div class="col-4"><q-input outlined v-model="startForm.destination_state" label="UF" /></div>
                </div>
            </q-card-section>
            
            <q-card-actions align="right" class="q-pa-md bg-grey-1 dialog-footer">
              <q-btn flat label="Cancelar" color="grey-7" v-close-popup class="text-weight-bold" />
              <q-btn type="submit" unelevated rounded color="primary" label="Iniciar Operação" :loading="isSubmitting" class="text-weight-bold q-px-md" />
            </q-card-actions>
          </q-form>
        </q-card>
      </q-dialog>

      <q-dialog v-model="isEndDialogOpen" transition-show="scale" transition-hide="scale">
        <q-card class="modern-dialog-card" style="width: 400px; max-width: 90vw;">
          <q-card-section class="dialog-header bg-negative text-white">
            <div class="text-h6 text-weight-bold flex items-center">
              <q-icon name="stop_circle" size="sm" class="q-mr-sm" />
              Finalizar {{ terminologyStore.journeyNoun }}
            </div>
          </q-card-section>
          
          <q-form @submit.prevent="handleEndJourney">
            <q-card-section class="q-pa-lg">
              <div class="text-body2 text-grey-7 q-mb-md">Insira os dados finais para encerrar a operação em segurança.</div>
              <q-input v-if="authStore.userSector === 'agronegocio'" autofocus outlined v-model.number="endForm.end_engine_hours" type="number" label="Horas Finais *" :rules="[val => val !== null && val !== undefined && val >= (editingJourney?.start_engine_hours || 0) || 'Valor final inválido']" />
              <q-input v-else autofocus outlined v-model.number="endForm.end_mileage" type="number" label="KM Final *" :rules="[val => val !== null && val !== undefined && val >= (editingJourney?.start_mileage || 0) || 'Valor final inválido']" />
            </q-card-section>
            <q-card-actions align="right" class="q-pa-md bg-grey-1 dialog-footer">
              <q-btn flat label="Cancelar" color="grey-7" v-close-popup class="text-weight-bold" />
              <q-btn type="submit" unelevated rounded color="negative" label="Finalizar Agora" :loading="isSubmitting" class="text-weight-bold q-px-md" />
            </q-card-actions>
          </q-form>
        </q-card>
      </q-dialog>

    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useQuasar, type QTableColumn } from 'quasar';
import { isAxiosError } from 'axios';
import { useAuthStore } from 'stores/auth-store';
import { useTerminologyStore } from 'stores/terminology-store';
import { useJourneyStore } from 'stores/journey-store';
import { useVehicleStore } from 'stores/vehicle-store';
import { useImplementStore } from 'stores/implement-store';
import { useFreightOrderStore } from 'stores/freight-order-store';
import { useDemoStore } from 'stores/demo-store';
import { JourneyType, type Journey, type JourneyCreate, type JourneyUpdate } from 'src/models/journey-models';
import type { FreightOrder } from 'src/models/freight-order-models';
import ClaimFreightDialog from 'components/ClaimFreightDialog.vue';
import DriverFreightDialog from 'components/DriverFreightDialog.vue';
import { useCepApi } from 'src/composables/useCepApi';

const $q = useQuasar();
const authStore = useAuthStore();
const terminologyStore = useTerminologyStore();
const journeyStore = useJourneyStore();
const vehicleStore = useVehicleStore();
const implementStore = useImplementStore();
const freightOrderStore = useFreightOrderStore();
const demoStore = useDemoStore();
const { isCepLoading, fetchAddressByCep } = useCepApi();

const isDemo = computed(() => authStore.user?.role === 'cliente_demo');

function showHistoryUpgradeDialog() {
  $q.dialog({
    title: 'Desbloqueie o Potencial Máximo',
    message: 'Para aceder ao histórico completo e outras funcionalidades premium, entre em contato com nossa equipe comercial.',
    ok: { label: 'Entendido', color: 'primary', rounded: true, unelevated: true },
    class: 'modern-dialog',
    persistent: false
  });
}

const isJourneyLimitReached = computed(() => {
  if (!authStore.isDemo) return false;
  const limit = authStore.user?.organization?.freight_order_limit;
  if (limit === undefined || limit === null || limit < 0) return false;
  const currentCount = demoStore.stats?.journey_count ?? 0;
  return currentCount >= limit;
});

function showLimitUpgradeDialog() {
  $q.dialog({
    title: 'Limite Atingido',
    message: `Você atingiu o limite de ${authStore.user?.organization?.freight_order_limit} ${terminologyStore.journeyNounPlural.toLowerCase()} permitidas no plano de demonstração. Entre em contato para atualizar seu plano.`,
    ok: { label: 'Entendido', color: 'primary', rounded: true, unelevated: true },
    class: 'modern-dialog',
    persistent: false
  });
}


const isSubmitting = ref(false);
const isStartDialogOpen = ref(false);
const isEndDialogOpen = ref(false);
const editingJourney = ref<Journey | null>(null);
const startForm = ref<Partial<JourneyCreate>>({});
const endForm = ref<Partial<JourneyUpdate>>({});

const isClaimDialogOpen = ref(false);
const isDriverDialogOpen = ref(false);
const selectedOrderForAction = ref<FreightOrder | null>(null);

function openClaimDialog(order: FreightOrder) {
  if (isJourneyLimitReached.value) {
    showLimitUpgradeDialog();
    return;
  }
  selectedOrderForAction.value = order;
  isClaimDialogOpen.value = true;
}

function onClaimDialogClose() {
  if (authStore.isDemo) void demoStore.fetchDemoStats();
  void freightOrderStore.fetchMyPendingOrders();
}

function openDriverDialog(order: FreightOrder) {
  void freightOrderStore.fetchOrderDetails(order.id);
  isDriverDialogOpen.value = true;
}

function refreshFreightData() {
  void freightOrderStore.fetchOpenOrders();
  void freightOrderStore.fetchMyPendingOrders();
}

const vehicleOptions = computed(() => vehicleStore.availableVehicles.map(v => ({ label: `${v.brand} ${v.model} (${v.license_plate || v.identifier})`, value: v.id })));
const implementOptions = computed(() => implementStore.availableImplements.map(i => ({ label: `${i.name} (${i.brand} ${i.model})`, value: i.id })));

const columns = computed<QTableColumn[]>(() => {
  const baseColumns: QTableColumn[] = [
    { name: 'status', label: 'Status', field: (row: Journey) => row.is_active ? 'Ativa' : 'Finalizada', align: 'left', sortable: true },
    { name: 'vehicle', label: terminologyStore.vehicleNoun, field: (row: Journey) => `${row.vehicle?.brand || ''} ${row.vehicle?.model || ''}`, align: 'left', sortable: true },
    { name: 'driver', label: 'Motorista', field: (row: Journey) => row.driver?.full_name || '', align: 'left', sortable: true },
    { name: 'startTime', label: 'Início', field: 'start_time', align: 'center', format: (val: string) => new Date(val).toLocaleString('pt-BR'), sortable: true },
    { name: 'endTime', label: 'Fim', field: 'end_time', align: 'center', format: (val: string | null) => val ? new Date(val).toLocaleString('pt-BR') : '---', sortable: true },
    { name: 'distance', label: `${terminologyStore.distanceUnit} Rodados`, align: 'center', field: (row: Journey) => {
        if (authStore.userSector === 'agronegocio' && row.end_engine_hours != null && row.start_engine_hours != null) return (row.end_engine_hours - row.start_engine_hours).toFixed(1);
        if (row.end_mileage != null && row.start_mileage != null) return row.end_mileage - row.start_mileage;
        return '---';
      }, sortable: true
    },
    { name: 'implement', label: 'Implemento', align: 'left', field: (row: Journey) => row.implement ? `${row.implement.name} (${row.implement.model})` : '---', sortable: true },
  ];
  if (authStore.isManager) {
    baseColumns.push({ name: 'actions', label: 'Ações', field: 'actions', align: 'right' });
  }
  return baseColumns;
});

watch(() => startForm.value.vehicle_id, (newVehicleId) => {
  if (!newVehicleId) return;
  const selectedVehicle = vehicleStore.availableVehicles.find(v => v.id === newVehicleId);
  if (selectedVehicle) {
    if (authStore.userSector === 'agronegocio') startForm.value.start_engine_hours = selectedVehicle.current_engine_hours ?? 0;
    else startForm.value.start_mileage = selectedVehicle.current_km ?? 0;
  }
});

async function openStartDialog() {
  if (isJourneyLimitReached.value) {
    showLimitUpgradeDialog();
    return;
  }

  const promisesToFetch = [vehicleStore.fetchAllVehicles()];
  if (authStore.userSector === 'agronegocio') promisesToFetch.push(implementStore.fetchAvailableImplements());
  await Promise.all(promisesToFetch);
  startForm.value = { 
    vehicle_id: null, 
    trip_type: JourneyType.FREE_ROAM, 
    trip_description: '', 
    implement_id: null,
    destination_cep: '',
    destination_street: '',
    destination_number: '',
    destination_neighborhood: '',
    destination_city: '',
    destination_state: '',
  };
  isStartDialogOpen.value = true;
}

function openEndDialog(journey?: Journey) {
  const journeyToEnd = journey || journeyStore.currentUserActiveJourney;
  if (!journeyToEnd) return;
  editingJourney.value = journeyToEnd;
  endForm.value = {};
  if (authStore.userSector === 'agronegocio') endForm.value.end_engine_hours = journeyToEnd.vehicle?.current_engine_hours ?? journeyToEnd.start_engine_hours ?? 0;
  else endForm.value.end_mileage = journeyToEnd.vehicle?.current_km ?? journeyToEnd.start_mileage ?? 0;
  isEndDialogOpen.value = true;
}

async function handleStartJourney() {
  isSubmitting.value = true;
  try {
    if (startForm.value.destination_street) {
        startForm.value.destination_address = [
            startForm.value.destination_street,
            startForm.value.destination_number,
            startForm.value.destination_neighborhood,
            startForm.value.destination_city,
            startForm.value.destination_state
        ].filter(Boolean).join(', ');
    }

    await journeyStore.startJourney(startForm.value as JourneyCreate);
    $q.notify({ type: 'positive', message: terminologyStore.journeyStartSuccessMessage });
    isStartDialogOpen.value = false;
    if (isDemo.value) void demoStore.fetchDemoStats();
  } catch (error) {
    let message = 'Erro ao iniciar operação.';
    if (isAxiosError(error) && error.response?.data?.detail) { message = error.response.data.detail as string; }
    $q.notify({ type: 'negative', message });
  } finally {
    isSubmitting.value = false;
  }
}

async function handleEndJourney() {
  if (!editingJourney.value) return;
  isSubmitting.value = true;
  try {
    await journeyStore.endJourney(editingJourney.value.id, endForm.value);
    $q.notify({ type: 'positive', message: terminologyStore.journeyEndSuccessMessage });
    isEndDialogOpen.value = false;
    await journeyStore.fetchAllJourneys();
    await vehicleStore.fetchAllVehicles();
  } catch (error) {
    let message = 'Erro ao finalizar operação.';
    if (isAxiosError(error) && error.response?.data?.detail) { message = error.response.data.detail as string; }
    $q.notify({ type: 'negative', message });
  } finally {
    isSubmitting.value = false;
    editingJourney.value = null;
  }
}

function promptToDeleteJourney(journey: Journey) {
  $q.dialog({
    title: 'Confirmar Exclusão', 
    message: `Tem certeza que deseja excluir esta ${terminologyStore.journeyNoun.toLowerCase()}? Esta ação é irreversível.`,
    cancel: { label: 'Cancelar', flat: true, color: 'grey-7' }, 
    persistent: false,
    ok: { label: 'Excluir', color: 'negative', rounded: true, unelevated: true },
    class: 'modern-dialog'
  }).onOk(() => {
    void journeyStore.deleteJourney(journey.id);
  });
}

async function handleJourneyCepBlur() {
  if (startForm.value.destination_cep) {
    const address = await fetchAddressByCep(startForm.value.destination_cep);
    if (address) {
      startForm.value.destination_street = address.street;
      startForm.value.destination_neighborhood = address.neighborhood;
      startForm.value.destination_city = address.city;
      startForm.value.destination_state = address.state;
    }
  }
}

onMounted(() => {
  if (authStore.userSector === 'frete') {
    refreshFreightData();
  } else {
    void journeyStore.fetchAllJourneys();
  }
  if (isDemo.value) {
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
  transition: all 0.3s ease;
  overflow: hidden;

  .body--dark & {
    background: #1a1a1a;
    border: 1px solid rgba(255, 255, 255, 0.05);
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
  }
}

/* LISTAS MODERNAS */
.modern-list-item {
  border-radius: 12px;
  margin: 6px 8px;
  border: 1px solid transparent;
  
  &:hover {
    background-color: rgba(0, 0, 0, 0.02);
    border-color: rgba(0, 0, 0, 0.05);
    transform: translateX(4px);
  }

  &.active-task {
    background-color: rgba($primary, 0.05);
    border-color: rgba($primary, 0.2);
  }

  .body--dark & {
    &:hover {
      background-color: rgba(255, 255, 255, 0.03);
      border-color: rgba(255, 255, 255, 0.05);
    }
    &.active-task {
      background-color: rgba($primary, 0.15);
      border-color: rgba($primary, 0.3);
    }
  }
}

/* BANNERS E DESTAQUES */
.premium-banner {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border: 1px solid #fcd34d;
  
  .body--dark & {
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(245, 158, 11, 0.05) 100%);
    border-color: rgba(245, 158, 11, 0.2);
    color: #f3f4f6 !important;
  }
}

.active-journey-card {
  background: linear-gradient(135deg, $primary 0%, color-mix(in srgb, $primary 80%, black) 100%);
  border-radius: 16px;
  border: none;
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
.opacity-80 { opacity: 0.8; }
.opacity-50 { opacity: 0.5; }
.opacity-30 { opacity: 0.3; }
.letter-spacing-1 { letter-spacing: 1px; }

.transition-generic { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.hover-rotate:hover { transform: rotate(45deg); }

.modern-tooltip {
  border-radius: 8px !important;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
}
</style>