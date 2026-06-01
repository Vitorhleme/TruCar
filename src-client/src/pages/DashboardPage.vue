<template>
  <q-page padding class="dashboard-page">
    <div class="page-content-container">

      <template v-if="isManager">
        <div class="header-section flex items-center justify-between q-mb-xl">
          <div>
            <h1 class="text-h4 text-weight-bolder q-my-none">Dashboard de Gestão</h1>
            <div class="text-subtitle1 text-grey-7 q-mt-xs">Bem-vindo(a), {{ authStore.user?.full_name }}.</div>
          </div>
          <div class="flex items-center q-gutter-md">
            <q-select
              v-model="selectedPeriod"
              :options="periodOptions"
              label="Período"
              dense
              outlined
              class="gt-xs period-select"
              behavior="menu"
            />
            <q-btn-dropdown
              color="primary" 
              icon="add" 
              label="Ações Rápidas"
              unelevated 
              class="gt-xs action-btn"
            >
              <q-list dense class="q-py-sm">
                <q-item clickable v-close-popup @click="router.push('/vehicles')">
                  <q-item-section avatar><q-icon name="local_shipping" color="primary" /></q-item-section>
                  <q-item-section>Adicionar Veículo</q-item-section>
                </q-item>
                <q-item clickable v-close-popup @click="router.push('/users')">
                  <q-item-section avatar><q-icon name="person_add" color="secondary" /></q-item-section>
                  <q-item-section>Adicionar Motorista</q-item-section>
                </q-item>
                <q-item clickable v-close-popup @click="router.push('/journeys')">
                  <q-item-section avatar><q-icon name="route" color="accent" /></q-item-section>
                  <q-item-section>Iniciar Jornada</q-item-section>
                </q-item>
              </q-list>
            </q-btn-dropdown>
          </div>
        </div>

        <div class="stats-grid q-mb-xl">
          <StatCard
            label="Total de Veículos"
            :value="kpis?.total_vehicles ?? 0"
            :limit="authStore.isDemo ? (authStore.user?.organization?.vehicle_limit ?? -1) : -1"
            icon="local_shipping"
            color="primary"
            :loading="dashboardStore.isLoading"
            to="/vehicles"
            class="hover-lift"
          />
          <StatCard label="Disponíveis" :value="kpis?.available_vehicles ?? 0" icon="check_circle_outline" color="positive" :loading="dashboardStore.isLoading" to="/vehicles?status=available" class="hover-lift"/>
          <StatCard :label="journeyNounInProgress" :value="kpis?.in_use_vehicles ?? 0" icon="alt_route" color="warning" :loading="dashboardStore.isLoading" to="/vehicles?status=in_use" class="hover-lift"/>
          <StatCard label="Em Manutenção" :value="kpis?.maintenance_vehicles ?? 0" icon="build" color="negative" :loading="dashboardStore.isLoading" to="/maintenance" class="hover-lift"/>
          <StatCard label="Custo por KM" :value="`R$ ${efficiencyKpis?.cost_per_km.toFixed(2) ?? '0.00'}`" icon="paid" color="deep-purple" :loading="dashboardStore.isLoading" class="hover-lift"/>
          <StatCard label="Gasto Combustível" :value="`R$ ${fuelCostTotal.toFixed(2)}`" icon="local_gas_station" color="orange-9" :loading="dashboardStore.isLoading" class="hover-lift"/>
          <StatCard label="Taxa de Utilização" :value="`${efficiencyKpis?.utilization_rate.toFixed(1) ?? '0.0'}%`" icon="pie_chart" color="teal" :loading="dashboardStore.isLoading" class="hover-lift"/>
        </div>

        <div class="row q-col-gutter-xl" v-if="dashboardStore.managerDashboard">
          <div class="col-12 col-xl-8 col-lg-7">
            <div class="column q-gutter-y-xl">
              
              <q-card class="dashboard-card overflow-hidden">
                <q-card-section class="q-pb-none">
                  <div class="text-h6 text-weight-bold">Operação em Tempo Real</div>
                  <div class="text-caption text-grey-6 q-mb-md">Visão atualizada da frota</div>
                </q-card-section>
                <q-separator />
                <q-card-section class="q-pa-none">
                  <div class="map-container">
                    <l-map ref="mapRef" v-model:zoom="zoom" :center="center" :use-global-leaflet="false">
                      <l-tile-layer
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        layer-type="base"
                        name="OpenStreetMap"
                        attribution="&copy; <a href='http://www.openstreetmap.org/copyright'>OpenStreetMap</a>"
                      ></l-tile-layer>
                      <l-marker
                        v-for="vehicle in dashboardStore.vehiclePositions"
                        :key="vehicle.id"
                        :lat-lng="[vehicle.latitude, vehicle.longitude]"
                      >
                        <l-icon :icon-url="getVehicleIcon(vehicle.status)" :icon-size="[38, 48]" />
                        <l-popup class="modern-popup">
                          <strong>{{ vehicle.license_plate || vehicle.identifier }}</strong><br>
                          Status: <q-badge :color="vehicle.status === 'Disponível' ? 'positive' : (vehicle.status === 'Em uso' ? 'warning' : 'negative')">{{ vehicle.status }}</q-badge>
                        </l-popup>
                      </l-marker>
                    </l-map>
                  </div>
                </q-card-section>
              </q-card>

              <div class="row q-col-gutter-lg">
                <div class="col-12 col-md-6 flex">
                  <PremiumWidget class="full-width hover-lift" title="Análise de Custos" :icon="`insights`" :description="`Análise de custos do período de ${selectedPeriod.label}`">
                    <ApexChart type="bar" height="280" :options="costAnalysisChart.options" :series="costAnalysisChart.series" />
                  </PremiumWidget>
                </div>
                <div class="col-12 col-md-6 flex">
                  <PremiumWidget class="full-width hover-lift" title="Análise de Atividade" :icon="`show_chart`" :description="`Análise de atividade do período de ${selectedPeriod.label}`">
                    <ApexChart type="area" height="280" :options="lineChart.options" :series="lineChart.series" />
                  </PremiumWidget>
                </div>
              </div>
            </div>
          </div>

          <div class="col-12 col-xl-4 col-lg-5">
            <div class="column q-gutter-y-lg">
              
              <q-card class="dashboard-card">
                <q-card-section class="flex justify-between items-center">
                  <div class="text-h6 text-weight-bold">Alertas Recentes</div>
                  <q-icon name="notifications_active" size="sm" color="warning" />
                </q-card-section>
                <q-list separator class="q-px-sm">
                  <q-item v-for="alert in recentAlerts" :key="alert.id" class="q-py-md">
                    <q-item-section avatar>
                      <q-avatar :color="`${alert.color}-1`" :text-color="alert.color" rounded>
                        <q-icon :name="alert.icon" />
                      </q-avatar>
                    </q-item-section>
                    <q-item-section>
                      <q-item-label class="text-weight-medium">{{ alert.title }}</q-item-label>
                      <q-item-label caption lines="2">{{ alert.subtitle }}</q-item-label>
                    </q-item-section>
                    <q-item-section side top>
                      <q-item-label caption>{{ alert.time }}</q-item-label>
                    </q-item-section>
                  </q-item>
                  <q-item v-if="!recentAlerts?.length">
                    <q-item-section class="text-center text-grey-6 q-py-lg">Nenhum alerta recente.</q-item-section>
                  </q-item>
                </q-list>
              </q-card>

              <q-card class="dashboard-card">
                <q-card-section class="flex justify-between items-center">
                  <div class="text-h6 text-weight-bold">Próximas Manutenções</div>
                  <q-icon name="build_circle" size="sm" color="negative" />
                </q-card-section>
                <q-list separator class="q-px-sm">
                  <q-item v-for="maint in upcomingMaintenances" :key="maint.vehicle_info" class="q-py-md">
                    <q-item-section>
                      <q-item-label class="text-weight-medium">{{ maint.vehicle_info }}</q-item-label>
                      <q-item-label caption>
                        <q-icon name="schedule" size="xs" class="q-mr-xs"/>
                        Vence em <span class="text-weight-bold">{{ maint.due_date ? new Date(maint.due_date).toLocaleDateString() : `${maint.due_km} km` }}</span>
                      </q-item-label>
                    </q-item-section>
                    <q-item-section side>
                      <q-btn dense outline rounded color="primary" icon="event" label="Agendar" @click="scheduleMaintenance(maint.vehicle_info)" class="q-px-sm" />
                    </q-item-section>
                  </q-item>
                  <q-item v-if="!upcomingMaintenances?.length">
                    <q-item-section class="text-center text-grey-6 q-py-lg">Nenhuma manutenção próxima.</q-item-section>
                  </q-item>
                </q-list>
              </q-card>
              
              <q-card class="dashboard-card goal-card" v-if="activeGoal">
                  <q-card-section>
                    <div class="row items-center justify-between q-mb-sm">
                      <div class="text-h6 text-weight-bold">Meta: {{ activeGoal.title }}</div>
                      <q-icon name="emoji_events" color="amber" size="md" />
                    </div>
                    <div class="text-subtitle2 text-grey-7 q-mb-md">
                      Progresso: <span class="text-weight-bold text-primary">{{ activeGoal.current_value.toFixed(2) }}</span> / {{ activeGoal.target_value }} ({{ activeGoal.unit }})
                    </div>
                    <q-linear-progress rounded size="20px" :value="goalProgress" color="positive" track-color="grey-3">
                      <div class="absolute-full flex flex-center">
                        <q-badge color="transparent" text-color="white" class="text-weight-bold" :label="`${(goalProgress * 100).toFixed(1)}%`" />
                      </div>
                    </q-linear-progress>
                  </q-card-section>
              </q-card>

              <PremiumWidget class="full-width hover-lift" title="Top 3 Motoristas do Mês" icon="workspace_premium" description="Reconheça a melhor performance.">
                <div class="row items-end justify-center q-pa-md" style="min-height: 252px;">
                  <PodiumDriverCard v-for="(driver, index) in podiumDrivers" :key="driver.full_name" :driver="driver" :rank="index + 1" :unit="terminologyStore.distanceUnit" />
                  <div v-if="!podiumDrivers?.length" class="text-grey-6 text-center full-width">Dados insuficientes para gerar o pódio.</div>
                </div>
              </PremiumWidget>

            </div>
          </div>
        </div>
      </template>

      <template v-else-if="isDriver">
        <div class="header-section q-mb-xl">
          <h1 class="text-h4 text-weight-bolder q-my-none">Meu Desempenho</h1>
          <div class="text-subtitle1 text-grey-7 q-mt-xs">Olá, {{ authStore.user?.full_name }}. Aqui está o seu resumo.</div>
        </div>

        <div class="row q-col-gutter-xl" v-if="dashboardStore.driverDashboard">
          <div class="col-12 col-lg-7">
            <div class="column q-gutter-y-xl">
              <q-card class="dashboard-card">
                <q-card-section>
                  <div class="text-h6 text-weight-bold">Minhas Métricas (Este Mês)</div>
                </q-card-section>
                <q-card-section>
                  <div class="stats-grid-small">
                    <StatCard label="Distância Percorrida" :value="`${driverMetrics?.distance.toFixed(0) ?? 0} ${terminologyStore.distanceUnit}`" icon="route" color="primary" :loading="false" class="no-shadow border-light"/>
                    <StatCard label="Horas em Viagem" :value="`${driverMetrics?.hours.toFixed(1) ?? 0}h`" icon="timer" color="teal" :loading="false" class="no-shadow border-light"/>
                    <StatCard label="Consumo Médio" :value="`${driverMetrics?.fuel_efficiency.toFixed(1) ?? 0} km/l`" icon="local_gas_station" color="amber" :loading="false" class="no-shadow border-light"/>
                    <StatCard label="Alertas Recebidos" :value="driverMetrics?.alerts ?? 0" icon="warning" color="negative" :loading="false" class="no-shadow border-light"/>
                  </div>
                </q-card-section>
              </q-card>

              <q-card class="dashboard-card">
                <q-card-section>
                  <div class="text-h6 text-weight-bold">Minha Posição no Ranking</div>
                </q-card-section>
                <q-list separator class="q-px-sm">
                    <q-item v-for="entry in driverRanking" :key="entry.rank" :active="entry.is_current_user" active-class="bg-primary text-white rounded-borders q-my-xs shadow-2" class="q-py-md rounded-borders transition-generic">
                      <q-item-section avatar>
                        <q-avatar :color="entry.is_current_user ? 'white' : 'grey-2'" :text-color="entry.is_current_user ? 'primary' : 'black'" size="md" font-size="16px" class="text-weight-bold">
                          {{ entry.rank }}º
                        </q-avatar>
                      </q-item-section>
                      <q-item-section>
                        <q-item-label class="text-weight-medium">{{ entry.name }}</q-item-label>
                      </q-item-section>
                      <q-item-section side :class="entry.is_current_user ? 'text-white' : 'text-black'">
                        <span class="text-weight-bold">{{ entry.metric.toFixed(0) }} {{ terminologyStore.distanceUnit }}</span>
                      </q-item-section>
                    </q-item>
                </q-list>
              </q-card>
            </div>
          </div>

          <div class="col-12 col-lg-5">
              <div class="column q-gutter-y-xl">
                <q-card class="dashboard-card">
                  <q-card-section>
                    <div class="text-h6 text-weight-bold">Minhas Conquistas</div>
                  </q-card-section>
                  <q-card-section class="flex q-gutter-md justify-center">
                      <div v-for="achiev in driverAchievements" :key="achiev.title" class="text-center">
                        <q-avatar :icon="achiev.icon" :color="achiev.unlocked ? 'amber' : 'grey-3'" :text-color="achiev.unlocked ? 'white' : 'grey-5'" size="60px" class="shadow-1 transition-generic hover-scale" />
                        <div class="text-caption q-mt-sm text-weight-medium" style="max-width: 70px; line-height: 1.1;">{{ achiev.title }}</div>
                        <q-tooltip class="bg-dark text-body2">{{ achiev.title }} - {{ achiev.unlocked ? 'Desbloqueado!' : 'Bloqueado' }}</q-tooltip>
                      </div>
                  </q-card-section>
                </q-card>

                <q-card class="dashboard-card">
                    <q-card-section>
                    <div class="text-h6 text-weight-bold">Minhas Próximas Jornadas</div>
                  </q-card-section>
                  <q-list separator>
                    <q-item>
                      <q-item-section class="text-center text-grey-6 q-py-lg">
                        <q-icon name="event_busy" size="md" color="grey-4" class="q-mb-sm" />
                        <div>Nenhuma jornada agendada no momento.</div>
                      </q-item-section>
                    </q-item>
                  </q-list>
                </q-card>
              </div>
          </div>
        </div>
      </template>

      <template v-else-if="dashboardStore.isLoading">
        <div class="flex flex-center" style="height: 80vh">
          <q-spinner-grid color="primary" size="4em"/>
        </div>
      </template>

    </div>
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, computed, ref, watch, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar, colors } from 'quasar';
import { useDashboardStore } from 'stores/dashboard-store';
import { useAuthStore } from 'stores/auth-store';
import { useTerminologyStore } from 'stores/terminology-store';
import type { KmPerDay, CostByCategory } from 'src/models/report-models';
import ApexChart from 'vue3-apexcharts';
import StatCard from 'components/StatCard.vue';
import PremiumWidget from 'components/PremiumWidget.vue';
import PodiumDriverCard from 'components/PodiumDriverCard.vue';

// --- Importações do Leaflet ---
import "leaflet/dist/leaflet.css";
import {
  LMap,
  LTileLayer,
  LMarker,
  LPopup,
  LIcon,
} from "@vue-leaflet/vue-leaflet";

// --- LÓGICA DOS ÍCONES DO MAPA ---
function createQuasarIconPin(pinColor: string, iconPath: string): string {
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 42" width="38" height="48">
      <path fill="${pinColor}" stroke="#fff" stroke-width="2"
        d="M16 2C9.925 2 5 6.925 5 13c0 7.75 11 18 11 18s11-10.25 11-18C27 6.925 22.075 2 16 2z"/>
      <path fill="white" transform="translate(8, 8) scale(0.7)"
        d="${iconPath}"/>
    </svg>
  `;
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}

const iconPaths = {
  checkCircle: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z',
  altRoute: 'M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-4 14h-2v-4H9V9h4V5h2v4h2v4h-2v4z',
  build: 'M22.7 19l-9.1-9.1c.9-2.3.4-5-1.5-6.9-2-2-5-2.4-7.4-1.3L9 6 6 9 1.6 4.7C.4 7.1.9 10.1 2.9 12.1c1.9 1.9 4.6 2.4 6.9 1.5l9.1 9.1c.4.4 1 .4 1.4 0l2.3-2.3c.5-.4.5-1.1.1-1.4z',
};

const iconAvailable = createQuasarIconPin('#21BA45', iconPaths.checkCircle);
const iconInUse = createQuasarIconPin('#F2C037', iconPaths.altRoute);
const iconMaintenance = createQuasarIconPin('#C10015', iconPaths.build);

const dashboardStore = useDashboardStore();
const authStore = useAuthStore();
const terminologyStore = useTerminologyStore();
const $q = useQuasar();
const router = useRouter();

const isManager = computed(() => authStore.isManager);
const isDriver = computed(() => authStore.isDriver);

const selectedPeriod = ref({ label: 'Últimos 30 dias', value: 'last_30_days' });
const periodOptions = [
  { label: 'Últimos 7 dias', value: 'last_7_days' },
  { label: 'Últimos 30 dias', value: 'last_30_days' },
  { label: 'Este Mês', value: 'this_month' },
];
let positionInterval: ReturnType<typeof setInterval> | null = null;

const mapRef = ref<typeof LMap | null>(null);
const zoom = ref(4);
const center = ref<[number, number]>([-15.793889, -47.882778]); 

function getVehicleIcon(status: string) {
  if (status === 'Disponível') return iconAvailable;
  if (status === 'Em uso') return iconInUse;
  if (status === 'Em manutenção') return iconMaintenance;
  return iconAvailable;
}

const managerData = computed(() => dashboardStore.managerDashboard);
const kpis = computed(() => managerData.value?.kpis);
const efficiencyKpis = computed(() => managerData.value?.efficiency_kpis);
const recentAlerts = computed(() => managerData.value?.recent_alerts);
const upcomingMaintenances = computed(() => managerData.value?.upcoming_maintenances);
const activeGoal = computed(() => managerData.value?.active_goal);
const podiumDrivers = computed(() => managerData.value?.podium_drivers);

const fuelCostTotal = computed(() => {
  const costs = managerData.value?.costs_by_category || [];
  const fuel = costs.find((cost: CostByCategory) => cost.cost_type.toLowerCase() === 'combustível');
  return fuel ? fuel.total_amount : 0;
});

const goalProgress = computed(() => {
  if (!activeGoal.value) return 0;
  if (activeGoal.value.current_value > activeGoal.value.target_value) {
      const progress = activeGoal.value.target_value / activeGoal.value.current_value;
      return Math.min(progress, 1);
  }
  const progress = activeGoal.value.current_value / activeGoal.value.target_value;
  return Math.min(progress, 1);
});

const driverData = computed(() => dashboardStore.driverDashboard);
const driverMetrics = computed(() => driverData.value?.metrics);
const driverRanking = computed(() => driverData.value?.ranking_context);
const driverAchievements = computed(() => driverData.value?.achievements);

watch(() => dashboardStore.vehiclePositions, (newPositions) => {
  if (newPositions && newPositions.length > 0 && mapRef.value?.leafletObject) {
    const bounds = newPositions.map(p => [p.latitude, p.longitude] as [number, number]);
    void nextTick(() => {
      mapRef.value?.leafletObject.fitBounds(bounds);
    });
  }
}, { deep: true });

watch(selectedPeriod, (newPeriod) => {
  if (isManager.value && newPeriod) {
    void dashboardStore.fetchManagerDashboard(newPeriod.value);
  }
});

onMounted(async () => {
  if (isManager.value) {
    await dashboardStore.fetchManagerDashboard(selectedPeriod.value.value);
    await dashboardStore.fetchVehiclePositions();
    positionInterval = setInterval(() => {
      void dashboardStore.fetchVehiclePositions();
    }, 30000);
  } else if (isDriver.value) {
    await dashboardStore.fetchDriverDashboard();
  }
});

onUnmounted(() => {
  if (positionInterval) clearInterval(positionInterval);
  dashboardStore.clearDashboardData();
});

function scheduleMaintenance(vehicleInfo: string) {
  $q.notify({
    color: 'primary',
    icon: 'event',
    message: `Ação para agendar manutenção para ${vehicleInfo} foi disparada.`,
  });
}

const journeyNounInProgress = computed(() => `Em ${terminologyStore.journeyNoun}`);

const costAnalysisChart = computed(() => {
  const data = managerData.value?.costs_by_category || [];
  const series = [{ name: 'Custo Total', data: data.map((item: CostByCategory) => parseFloat(item.total_amount.toFixed(2))) }];
  const options = {
    chart: { type: 'bar', toolbar: { show: false }, fontFamily: 'inherit' },
    xaxis: { categories: data.map((item: CostByCategory) => item.cost_type), labels: { style: { colors: $q.dark.isActive ? '#BDBDBD' : '#757575' } } },
    yaxis: { labels: { style: { colors: $q.dark.isActive ? '#BDBDBD' : '#757575' }, formatter: (val: number) => `R$ ${val.toLocaleString('pt-BR')}` } },
    plotOptions: { bar: { borderRadius: 6, horizontal: false, columnWidth: '45%', distributed: true } },
    colors: [colors.getPaletteColor('primary'), colors.getPaletteColor('secondary'), colors.getPaletteColor('accent'), colors.getPaletteColor('teal'), colors.getPaletteColor('orange')],
    dataLabels: { enabled: false },
    legend: { show: false },
    grid: { borderColor: $q.dark.isActive ? '#333' : '#f1f1f1', strokeDashArray: 4 },
    tooltip: { theme: $q.dark.isActive ? 'dark' : 'light', y: { formatter: (val: number) => `R$ ${val.toFixed(2)}` } }
  };
  return { series, options };
});

const lineChart = computed(() => {
  const data = managerData.value?.km_per_day_last_30_days || [];
  const series = [{ name: `${terminologyStore.distanceUnit} Rodados`, data: data.map((item: KmPerDay) => item.total_km) }];
  const options = {
    chart: { id: 'km-per-day-chart', toolbar: { show: false }, zoom: { enabled: false }, fontFamily: 'inherit' },
    xaxis: { categories: data.map((item: KmPerDay) => new Date(item.date).toLocaleDateString('pt-BR', { timeZone: 'UTC' })), labels: { style: { colors: $q.dark.isActive ? '#BDBDBD' : '#757575' } } },
    yaxis: { labels: { style: { colors: $q.dark.isActive ? '#BDBDBD' : '#757575' } } },
    stroke: { curve: 'smooth', width: 3 },
    fill: { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.4, opacityTo: 0.05, stops: [0, 100] } },
    colors: [colors.getPaletteColor('primary')],
    dataLabels: { enabled: false },
    grid: { borderColor: $q.dark.isActive ? '#333' : '#f1f1f1', strokeDashArray: 4 },
    tooltip: { theme: $q.dark.isActive ? 'dark' : 'light', x: { format: 'dd/MM/yy' } }
  };
  return { series, options };
});
</script>

<style scoped lang="scss">
/* FUNDO DA PÁGINA */
.dashboard-page {
  background-color: #f8f9fa; /* Fundo super leve e moderno */
  min-height: 100vh;
  
  .body--dark & {
    background-color: #0d0d0d; /* Fundo extra escuro para contraste OLED */
  }
}

.page-content-container {
  max-width: 1600px;
  margin: 0 auto;
}

/* CSS GRID MÁGICO PARA RESPONSIVIDADE DOS CARDS SEM SOBREPOSIÇÃO */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  align-items: stretch; /* Faz todos os cards terem a mesma altura */
}

.stats-grid-small {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
}

/* ESTILIZAÇÃO DOS CARTÕES PRINCIPAIS */
.dashboard-card {
  border-radius: 16px; /* Borda bem redonda estilo Apple/Stripe */
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.04);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03); /* Sombra super suave */
  transition: all 0.3s ease;
  height: 100%;
  display: flex;
  flex-direction: column;

  .body--dark & {
    background: #1a1a1a; /* Cinza escuro profundo, não totalmente preto */
    border: 1px solid rgba(255, 255, 255, 0.05);
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
  }
}

/* EFEITOS DE HOVER (LEVANTAR CARTÃO) */
.hover-lift {
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.3s ease;
  will-change: transform;
  
  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.08);
  }

  .body--dark &:hover {
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.4);
  }
}

.hover-scale {
  &:hover {
    transform: scale(1.1);
  }
}

.transition-generic {
  transition: all 0.2s ease-in-out;
}

.border-light {
  border: 1px solid rgba(0,0,0,0.05);
  .body--dark & { border: 1px solid rgba(255,255,255,0.05); }
}

/* HEADER E BOTÕES */
.period-select {
  min-width: 220px;
  border-radius: 8px;
}

.action-btn {
  border-radius: 8px;
  padding: 8px 16px;
  font-weight: 600;
}

/* MAPA */
.map-container {
  height: 45vh; /* Altura responsiva baseada na janela */
  min-height: 400px;
  width: 100%;
  border-radius: 0 0 16px 16px;
  overflow: hidden;
  z-index: 1; /* Previne sobreposição estranha do Leaflet */
}

/* PROGRESS BAR META */
.goal-card {
  background: linear-gradient(145deg, #ffffff, #fcfcfc);
  .body--dark & {
    background: linear-gradient(145deg, #1e1e1e, #1a1a1a);
  }
}
</style>