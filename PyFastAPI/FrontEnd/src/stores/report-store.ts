// ARQUIVO: FrontEnd/src/stores/report-store.ts

import { defineStore } from 'pinia';
import { api } from 'boot/axios';
import { Notify } from 'quasar';
import type {
  VehicleConsolidatedReport,
  DriverPerformanceReport,
  FleetManagementReport,
} from 'src/models/report-models';

interface ReportState {
  isLoading: boolean;
  vehicleReport: VehicleConsolidatedReport | null;
  driverPerformanceReport: DriverPerformanceReport | null;
  fleetManagementReport: FleetManagementReport | null;
}

export const useReportStore = defineStore('report', {
  state: (): ReportState => ({
    isLoading: false,
    vehicleReport: null,
    driverPerformanceReport: null,
    fleetManagementReport: null,
  }),

  actions: {
    clearReports() {
      this.vehicleReport = null;
      this.driverPerformanceReport = null;
      this.fleetManagementReport = null;
    },

    async generateVehicleConsolidatedReport(
      vehicleId: number,
      startDate: string,
      endDate: string
    ) {
      this.clearReports();
      this.isLoading = true;
      try {
        const payload = {
          vehicle_id: vehicleId,
          start_date: startDate,
          end_date: endDate,
        };
        
        // --- CORREÇÃO AQUI ---
        // Removido o prefixo /api/v1/ para ficar igual aos outros
        const response = await api.post<VehicleConsolidatedReport>(
          '/reports/vehicle-consolidated', // <--- ESTA É A CORREÇÃO
          payload
        );
        this.vehicleReport = response.data;
        Notify.create({
          type: 'positive',
          message: 'Relatório de Veículo gerado com sucesso!',
        });
      } catch (error) {
        console.error('Erro ao gerar relatório consolidado:', error);
        Notify.create({ type: 'negative', message: 'Falha ao gerar o relatório.' });
      } finally {
        this.isLoading = false;
      }
    },

    async generateDriverPerformanceReport(startDate: string, endDate: string) {
      this.clearReports();
      this.isLoading = true;
      try {
        const payload = { start_date: startDate, end_date: endDate };
        
        // (Esta rota já estava correta, sem o prefixo)
        const response = await api.post<DriverPerformanceReport>(
          '/reports/driver-performance',
          payload
        );
        this.driverPerformanceReport = response.data;
        Notify.create({
          type: 'positive',
          message: 'Relatório de Desempenho gerado com sucesso!',
        });
      } catch (error) {
        console.error('Erro ao gerar relatório de desempenho:', error);
        Notify.create({ type: 'negative', message: 'Falha ao gerar o relatório.' });
      } finally {
        this.isLoading = false;
      }
    },

    async generateFleetManagementReport(startDate: string, endDate: string) {
      this.clearReports();
      this.isLoading = true;
      try {
        const payload = { start_date: startDate, end_date: endDate };

        // (Esta rota já estava correta, sem o prefixo)
        const response = await api.post<FleetManagementReport>(
          '/reports/fleet-management',
          payload
        );
        this.fleetManagementReport = response.data;
        Notify.create({
          type: 'positive',
          message: 'Relatório Gerencial gerado com sucesso!',
        });
      } catch (error) {
        console.error('Erro ao gerar relatório gerencial:', error);
        Notify.create({ type: 'negative', message: 'Falha ao gerar o relatório.' });
      } finally {
        this.isLoading = false;
      }
    },
  },
});