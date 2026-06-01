<template>
  <q-layout view="lHh LpR lFf" class="main-layout-container">
    <!-- SIDEBAR (DRAWER) -->
    <q-drawer
      v-model="leftDrawerOpen"
      show-if-above
      bordered
      class="app-sidebar"
      :width="280"
    >
      <q-scroll-area class="fit">
        <div class="q-pa-lg text-center sidebar-header flex flex-center">
            <img src="~assets/trucar-logo-white.png" class="logo-dark-theme transition-generic" style="height: 38px;" alt="TruCar Logo">
            <img src="~assets/trucar-logo-dark.png" class="logo-light-theme transition-generic" style="height: 38px;" alt="TruCar Logo">
        </div>
        
        <q-list class="q-px-sm q-pb-md">
          <template v-for="category in menuStructure" :key="category.label">
            <div class="category-label q-mt-md q-mb-xs q-px-md text-overline text-uppercase text-weight-bolder letter-spacing-1">
              {{ category.label }}
            </div>
            
            <q-item
                v-for="link in category.children"
                :key="link.title"
                clickable
                :to="link.to"
                exact
                v-ripple
                class="nav-link"
                active-class="nav-link--active"
              >
                <q-item-section avatar class="min-w-0 q-pr-sm">
                  <q-icon :name="link.icon" size="22px" class="nav-icon transition-generic" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-medium nav-text">{{ link.title }}</q-item-label>
                </q-item-section>
            </q-item>
          </template>

          <!-- ADMIN SECTION -->
          <div v-if="authStore.isSuperuser" class="q-mt-lg">
            <q-separator class="q-my-md opacity-50" />
            <div class="category-label q-mb-xs q-px-md text-overline text-uppercase text-weight-bolder letter-spacing-1">
              Sistema
            </div>
            <q-item clickable to="/admin" exact v-ripple class="nav-link admin-link" active-class="nav-link--active">
              <q-item-section avatar class="min-w-0 q-pr-sm"><q-icon name="admin_panel_settings" size="22px" class="nav-icon" /></q-item-section>
              <q-item-section><q-item-label class="text-weight-medium nav-text">Painel Admin</q-item-label></q-item-section>
            </q-item>
          </div>
        </q-list>
      </q-scroll-area>
    </q-drawer>

    <!-- HEADER -->
    <q-header class="main-header q-py-xs">
      <q-toolbar>
        <q-btn flat dense round icon="menu_open" aria-label="Menu" @click="toggleLeftDrawer" class="lt-md menu-btn q-mr-sm" />
        <q-space />

        <!-- DEMO CHIP -->
        <q-chip
          v-if="isDemo"
          clickable @click="showUpgradeDialog"
          color="amber-2" text-color="amber-9"
          icon="workspace_premium" label="Plano Demo"
          class="demo-chip q-mr-md cursor-pointer text-weight-bold transition-generic" size="sm"
        >
          <q-tooltip class="modern-tooltip bg-dark text-body2" :offset="[10, 10]">
            <div class="q-pa-sm">
              <div class="text-weight-bold text-amber-4 q-mb-sm">Limites do Plano de Demonstração</div>
              <q-list dense class="limits-list">
                <q-item class="q-pl-none"><q-item-section avatar style="min-width: 30px"><q-icon name="local_shipping" color="grey-4"/></q-item-section><q-item-section>Veículos: {{ stats?.vehicle_count ?? 0 }} / {{ formatLimit(authStore.user?.organization?.vehicle_limit) }}</q-item-section></q-item>
                <q-item class="q-pl-none"><q-item-section avatar style="min-width: 30px"><q-icon name="engineering" color="grey-4"/></q-item-section><q-item-section>Motoristas: {{ stats?.driver_count ?? 0 }} / {{ formatLimit(authStore.user?.organization?.driver_limit) }}</q-item-section></q-item>
                <q-item class="q-pl-none"><q-item-section avatar style="min-width: 30px"><q-icon name="route" color="grey-4"/></q-item-section><q-item-section>Jornadas este mês: {{ stats?.journey_count ?? 0 }} / {{ formatLimit(authStore.user?.organization?.freight_order_limit) }}</q-item-section></q-item>
              </q-list>
              <div class="q-mt-sm text-grey-4 text-caption">Clique para saber mais sobre o plano completo.</div>
            </div>
          </q-tooltip>
        </q-chip>

        <!-- CONFIGS -->
        <q-btn flat round dense icon="settings" to="/settings" class="q-mr-sm toolbar-icon-btn text-grey-7">
          <q-tooltip class="modern-tooltip bg-dark">Configurações</q-tooltip>
        </q-btn>
        
        <!-- NOTIFICAÇÕES -->
        <q-btn v-if="authStore.isManager" flat round dense icon="notifications_none" class="q-mr-sm toolbar-icon-btn text-grey-7">
          <q-badge v-if="notificationStore.unreadCount > 0" color="negative" floating rounded class="notification-badge shadow-1">{{ notificationStore.unreadCount }}</q-badge>
          <q-menu @show="notificationStore.fetchNotifications()" class="modern-menu" style="width: 380px; max-height: 500px;">
            <q-list separator class="q-py-sm">
              <q-item-label header class="flex justify-between items-center text-weight-bold text-subtitle1 q-pb-md">
                <span class="text-dark-dynamic">Notificações</span>
                <q-spinner v-if="notificationStore.isLoading" color="primary" size="1.2em" />
              </q-item-label>

              <q-scroll-area style="height: 350px;">
                <div v-if="!notificationStore.isLoading && notificationStore.notifications.length === 0" class="text-center text-grey-5 q-pa-xl column items-center">
                  <q-icon name="notifications_paused" size="3.5em" class="q-mb-md opacity-50" />
                  <div class="text-weight-medium">Nenhuma notificação por aqui.</div>
                  <div class="text-caption">Tudo limpo!</div>
                </div>
                
                <q-item
                  v-for="notification in notificationStore.notifications"
                  :key="notification.id"
                  clickable
                  v-ripple
                  :class="['notification-item transition-generic', { 'unread-notification': !notification.is_read }]"
                  @click="handleNotificationClick(notification)"
                >
                  <q-item-section avatar>
                    <q-avatar :icon="getNotificationIcon(notification.notification_type)" :color="notification.is_read ? 'grey-2' : 'primary-light'" :text-color="notification.is_read ? 'grey-6' : 'primary'" size="md" />
                  </q-item-section>

                  <q-item-section>
                    <q-item-label lines="2" :class="{'text-weight-medium text-dark-dynamic': !notification.is_read, 'text-grey-7': notification.is_read}">{{ notification.message }}</q-item-label>
                    <q-item-label caption class="q-mt-xs text-grey-5 flex items-center">
                      <q-icon name="schedule" size="12px" class="q-mr-xs"/> {{ formatNotificationDate(notification.created_at) }}
                    </q-item-label>
                  </q-item-section>

                  <q-item-section side top v-if="!notification.is_read">
                    <div class="unread-dot bg-primary"></div>
                  </q-item-section>
                </q-item>
              </q-scroll-area>
            </q-list>
          </q-menu>
        </q-btn>

        <q-separator vertical class="q-mx-sm opacity-30 gt-xs" inset />

        <!-- USER PROFILE -->
        <q-btn-dropdown flat no-caps class="user-dropdown-btn q-ml-xs">
          <template v-slot:label>
            <div class="row items-center no-wrap">
              <q-avatar size="32px" color="primary" text-color="white" class="shadow-1">
                {{ authStore.user?.full_name ? authStore.user.full_name.charAt(0).toUpperCase() : 'U' }}
              </q-avatar>
              <div class="column items-start q-ml-sm gt-sm">
                <span class="text-weight-bold text-dark-dynamic" style="line-height: 1.2;">{{ authStore.user?.full_name || 'Usuário' }}</span>
                <span class="text-caption text-grey-6" style="line-height: 1;">{{ authStore.isManager ? 'Gestor' : 'Motorista' }}</span>
              </div>
            </div>
          </template>
          <q-list class="modern-menu q-py-sm" style="min-width: 220px">
            <q-item clickable v-close-popup :to="`/users/${authStore.user?.id}/stats`" v-if="authStore.isDriver" class="menu-item-hover">
                <q-item-section avatar class="min-w-0 q-pr-sm"><q-icon name="query_stats" color="primary" size="20px"/></q-item-section>
                <q-item-section class="text-weight-medium">Minhas Estatísticas</q-item-section>
            </q-item>
            <q-separator class="q-my-xs opacity-50" v-if="authStore.isDriver" />
            <q-item clickable v-close-popup @click="handleLogout" class="menu-item-hover text-negative">
              <q-item-section avatar class="min-w-0 q-pr-sm"><q-icon name="logout" color="negative" size="20px"/></q-item-section>
              <q-item-section class="text-weight-medium">Sair da conta</q-item-section>
            </q-item>
          </q-list>
        </q-btn-dropdown>
      </q-toolbar>
      
      <!-- IMPERSONATION BANNER -->
      <q-banner v-if="authStore.isImpersonating" inline-actions class="impersonation-banner text-white shadow-2">
         <template v-slot:avatar>
           <q-icon name="admin_panel_settings" color="white" size="md" />
         </template>
         <div class="text-weight-medium text-subtitle1">
           Sessão de Impersonação Ativa
         </div>
         <div class="text-body2 opacity-80">
           A visualizar o sistema como <strong>{{ authStore.user?.full_name }}</strong>.
         </div>
         <template v-slot:action>
           <q-btn outline rounded color="white" label="Encerrar Sessão" @click="authStore.stopImpersonation()" class="q-px-md text-weight-bold" />
         </template>
      </q-banner>
    </q-header>

    <!-- PAGE CONTAINER -->
    <q-page-container class="app-page-container">
      <router-view v-slot="{ Component }">
        <transition name="page-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import { storeToRefs } from 'pinia';
import { useAuthStore } from 'stores/auth-store';
import { useNotificationStore } from 'stores/notification-store';
import { useTerminologyStore } from 'stores/terminology-store';
import { useDemoStore } from 'stores/demo-store';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import type { Notification } from 'src/models/notification-models';

const leftDrawerOpen = ref(false);
const router = useRouter();
const $q = useQuasar();
const authStore = useAuthStore();
const notificationStore = useNotificationStore();
const terminologyStore = useTerminologyStore();
const demoStore = useDemoStore();

const { stats } = storeToRefs(demoStore);
let pollTimer: number;

interface MenuItem {
  title: string;
  icon: string;
  to: string;
} 

interface MenuCategory {
    label: string;
    icon: string;
    children: MenuItem[];
}

function toggleLeftDrawer() { leftDrawerOpen.value = !leftDrawerOpen.value; }
function handleLogout() {
  if (authStore.isImpersonating) {
    authStore.stopImpersonation();
  } else {
    authStore.logout();
    void router.push('/auth/login');
  }
}

const isDemo = computed(() => authStore.isDemo);

function showUpgradeDialog() {
  $q.dialog({
    title: 'Desbloqueie o Potencial Máximo',
    message: 'Para liberar recursos avançados como relatórios detalhados e cadastro ilimitado de veículos e motoristas, entre em contato com nossa equipe comercial.',
    ok: { label: 'Entendido', color: 'primary', rounded: true, unelevated: true },
    class: 'modern-dialog',
    persistent: false
  });
}

function formatLimit(limit: number | undefined | null): string {
  if (limit === undefined || limit === null) return '--';
  if (limit < 0) return 'Ilimitado';
  return limit.toString();
}

function formatNotificationDate(date: string) {
  return formatDistanceToNow(new Date(date), { addSuffix: true, locale: ptBR });
}

function getNotificationIcon(type: string): string {
  const iconMap: Record<string, string> = {
    'maintenance_due_date': 'event_busy',
    'maintenance_due_km': 'speed',
    'maintenance_request_new': 'build',
    'new_fine_registered': 'receipt_long',
    'document_expiring': 'badge',
    'low_stock': 'inventory_2',
    'journey_started': 'play_arrow',
    'journey_ended': 'stop',
  };
  return iconMap[type] || 'notifications';
}

async function handleNotificationClick(notification: Notification) {
  if (!notification.is_read) {
    await notificationStore.markAsRead(notification.id);
  }
  if (notification.related_entity_type === 'maintenance_request') {
    void router.push('/maintenance');
  }
}

const menuStructure = computed(() => {
    if (authStore.isManager) return getManagerMenu();
    if (authStore.isDriver) return getDriverMenu();
    return [];
});

function getDriverMenu(): MenuCategory[] {
    const sector = authStore.userSector;
    const menu: MenuCategory[] = [];

    const general: MenuCategory = {
        label: 'Principal',
        icon: 'dashboard',
        children: [
            { title: 'Dashboard', icon: 'dashboard', to: '/dashboard' },
        ],
    };
    if (sector === 'frete') {
        general.children.push({ title: 'Minha Rota', icon: 'explore', to: '/driver-cockpit' });
    }
    menu.push(general);

    const operations: MenuCategory = {
        label: 'Minhas Atividades',
        icon: 'work_history',
        children: [
            { title: terminologyStore.journeyPageTitle, icon: 'route', to: '/journeys' },
            { title: 'Abastecimentos', icon: 'local_gas_station', to: '/fuel-logs' },
            { title: 'Minhas Multas', icon: 'receipt_long', to: '/fines' },
            { title: 'Manutenções', icon: 'build', to: '/maintenance' },
        ],
    };
    menu.push(operations);

    const fleet: MenuCategory = {
        label: 'Frota',
        icon: 'local_shipping',
        children: [
            { title: terminologyStore.vehiclePageTitle, icon: 'local_shipping', to: '/vehicles' }
        ]
    };
    menu.push(fleet);

    return menu;
}

function getManagerMenu(): MenuCategory[] {
  const sector = authStore.userSector;
  const menu: MenuCategory[] = [];

  const general: MenuCategory = {
    label: 'Visão Geral', icon: 'dashboard',
    children: [
      { title: 'Dashboard', icon: 'grid_view', to: '/dashboard' },
    ]
  };
  menu.push(general);

  const operations: MenuCategory = { label: 'Operações', icon: 'alt_route', children: [] as MenuItem[] };
  if (sector === 'agronegocio' || sector === 'servicos') {
    operations.children.push({ title: terminologyStore.journeyPageTitle, icon: 'route', to: '/journeys' });
  }
  if (sector === 'frete') {
    operations.children.push({ title: 'Ordens de Frete', icon: 'list_alt', to: '/freight-orders' });
  }
  if (operations.children.length > 0) menu.push(operations);

  const management: MenuCategory = { label: 'Administração', icon: 'settings_suggest', children: [] as MenuItem[] };
  if (sector === 'agronegocio' || sector === 'servicos' || sector === 'frete') {
    management.children.push({ title: terminologyStore.vehiclePageTitle, icon: 'directions_car', to: '/vehicles' });
  }
  if (sector === 'agronegocio') {
    management.children.push({ title: 'Implementos', icon: 'precision_manufacturing', to: '/implements' });
  }
  if (sector === 'frete') {
    management.children.push({ title: 'Clientes', icon: 'groups', to: '/clients' });
  }
  management.children.push({ title: 'Equipe', icon: 'manage_accounts', to: '/users' }); 
  management.children.push({ title: 'Inventário', icon: 'inventory_2', to: '/parts' });
  management.children.push({ title: 'Rastreabilidade', icon: 'manage_search', to: '/inventory-items' });
  management.children.push({ title: 'Custos', icon: 'account_balance_wallet', to: '/costs' });
  management.children.push({ title: 'Abastecimentos', icon: 'local_gas_station', to: '/fuel-logs' });
  management.children.push({ title: 'Documentos', icon: 'folder_shared', to: '/documents' });
  
  if (management.children.length > 0) menu.push(management);

  const analysis: MenuCategory = {
    label: 'Inteligência', icon: 'analytics',
    children: [
      { title: 'Relatórios', icon: 'insert_chart_outlined', to: '/reports' },
      { title: 'Manutenções', icon: 'build_circle', to: '/maintenance' },
      { title: 'Gestão de Multas', icon: 'receipt_long', to: '/fines' },
    ]
  };
  menu.push(analysis);

  return menu;
}

onMounted(() => {
  if (isDemo.value) {
    void demoStore.fetchDemoStats();
  }
  if (authStore.isManager) {
    void notificationStore.fetchUnreadCount();
    pollTimer = window.setInterval(() => { void notificationStore.fetchUnreadCount(); }, 60000);
  }
});

onUnmounted(() => { clearInterval(pollTimer); });
</script>

<style lang="scss">
/* Estilos Globais para Dropdowns e Menus injetados no body */
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

.modern-tooltip {
  border-radius: 8px !important;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
}

.menu-item-hover {
  transition: background-color 0.2s ease;
  border-radius: 8px;
  margin: 2px 8px;
}
</style>

<style lang="scss" scoped>
/* CORES E VARIÁVEIS BASE */
.transition-generic {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.min-w-0 {
  min-width: 0 !important;
}

.text-dark-dynamic {
  color: #111827;
  .body--dark & { color: #f3f4f6; }
}

.opacity-50 { opacity: 0.5; }
.opacity-80 { opacity: 0.8; }
.opacity-30 { opacity: 0.3; }

/* CONTAINERS PRINCIPAIS */
.main-layout-container {
  background-color: #f8fafc; /* Slate-50 */
  .body--dark & { background-color: #0d0d0d; }
}

.app-page-container {
  background-color: #f8fafc;
  .body--dark & { background-color: #0d0d0d; }
}

/* SIDEBAR (DRAWER) */
.app-sidebar {
  background-color: #ffffff;
  border-right: 1px solid rgba(0, 0, 0, 0.06);

  .sidebar-header {
    height: 80px;
    .logo-dark-theme { display: none; }
    .logo-light-theme { display: block; }
  }

  .category-label {
    color: #94a3b8; /* Slate-400 */
    font-size: 0.7rem;
    letter-spacing: 0.05em;
  }

  .nav-link {
    color: #475569; /* Slate-600 */
    margin: 4px 12px;
    border-radius: 10px;
    transition: all 0.2s ease;

    .nav-icon { color: #64748b; } /* Slate-500 */

    &--active {
      background-color: rgba($primary, 0.08);
      color: $primary;
      
      .nav-icon { color: $primary; }
      .nav-text { font-weight: 700; }
    }

    &:hover:not(.nav-link--active) {
      background-color: #f1f5f9; /* Slate-100 */
      color: #0f172a;
      .nav-icon { color: #0f172a; }
    }
  }

  .admin-link {
    &--active {
      background-color: rgba($negative, 0.08);
      color: $negative;
      .nav-icon { color: $negative; }
    }
  }
}

/* SIDEBAR DARK MODE */
.body--dark .app-sidebar {
  background-color: #141414;
  border-right: 1px solid rgba(255, 255, 255, 0.05);

  .sidebar-header {
    .logo-dark-theme { display: block; }
    .logo-light-theme { display: none; }
  }

  .category-label { color: #6b7280; }

  .nav-link {
    color: #9ca3af;

    .nav-icon { color: #6b7280; }

    &--active {
      background-color: rgba($primary, 0.15);
      color: $primary;
      border-left: 3px solid $primary;
      border-radius: 4px 10px 10px 4px;
      
      .nav-icon { color: $primary; }
    }

    &:hover:not(.nav-link--active) {
      background-color: rgba(255, 255, 255, 0.04);
      color: #f3f4f6;
      .nav-icon { color: #f3f4f6; }
    }
  }
  
  .admin-link--active {
    background-color: rgba($negative, 0.15);
    color: $negative;
    border-left: 3px solid $negative;
    .nav-icon { color: $negative; }
  }
}

/* CABEÇALHO (HEADER GLASSMORPHISM) */
.main-header {
  background-color: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  color: #111827;
  
  .toolbar-icon-btn {
    transition: background-color 0.2s ease, color 0.2s ease;
    &:hover { background-color: rgba(0, 0, 0, 0.04); color: $primary !important; }
  }

  .demo-chip:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
  }

  .body--dark & {
    background-color: rgba(20, 20, 20, 0.85);
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    color: #f3f4f6;
    
    .toolbar-icon-btn:hover { background-color: rgba(255, 255, 255, 0.05); }
    .demo-chip { background-color: rgba(245, 158, 11, 0.15) !important; color: #fbbf24 !important; }
  }
}

.user-dropdown-btn {
  border-radius: 8px;
  padding: 4px 8px;
  &:hover { background-color: rgba(0, 0, 0, 0.03); }
  .body--dark &:hover { background-color: rgba(255, 255, 255, 0.04); }
}

/* NOTIFICAÇÕES */
.notification-badge {
  font-weight: bold;
  border: 2px solid white;
  .body--dark & { border-color: #1a1a1a; }
}

.bg-primary-light { background-color: rgba($primary, 0.15); }

.notification-item {
  border-radius: 12px;
  margin: 4px 12px;
  padding: 12px;
  
  &.unread-notification { background-color: rgba($primary, 0.03); }
  &:hover { background-color: rgba(0, 0, 0, 0.02); }
  
  .body--dark & {
    &.unread-notification { background-color: rgba($primary, 0.1); }
    &:hover { background-color: rgba(255, 255, 255, 0.03); }
  }
}

.unread-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  box-shadow: 0 0 8px rgba($primary, 0.6);
}

/* IMPERSONATION BANNER */
.impersonation-banner {
  background: linear-gradient(135deg, $deep-orange-8 0%, $deep-orange-6 100%);
  border-bottom: 1px solid rgba(0,0,0,0.1);
}

/* TRANSIÇÕES DE ROTA SUAVES */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.page-fade-enter-from {
  opacity: 0;
  transform: translateY(15px);
}
.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-15px);
}
</style>