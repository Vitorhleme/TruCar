from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import date, datetime

from .vehicle_cost_schema import VehicleCostPublic
from .fuel_log_schema import FuelLogPublic
from .maintenance_schema import MaintenanceRequestPublic

# Mantém o schema do dashboard existente
class DashboardSummary(BaseModel):
    total_vehicles: int
    active_journeys: int
    total_costs_last_30_days: float
    maintenance_open_requests: int

# --- NOVOS SCHEMAS PARA O RELATÓRIO CONSOLIDADO DE VEÍCULO ---

class VehicleReportPerformanceSummary(BaseModel):
    """Resumo de performance para o relatório."""
    total_distance_km: float = 0.0
    total_fuel_liters: float = 0.0
    average_consumption: float = 0.0 # KM/L ou L/Hora, dependendo do setor

class VehicleReportFinancialSummary(BaseModel):
    """Resumo financeiro para o relatório."""
    total_costs: float = 0.0
    cost_per_km: float = 0.0
    costs_by_category: Dict[str, float] = {}

class VehicleConsolidatedReport(BaseModel):
    """Schema principal para o Relatório Consolidado de Veículo."""
    # --- Dados de Cabeçalho ---
    vehicle_id: int
    vehicle_identifier: str # Placa ou Identificador
    vehicle_model: str
    report_period_start: date
    report_period_end: date
    generated_at: datetime

    # --- Seções de Dados ---
    performance_summary: VehicleReportPerformanceSummary
    financial_summary: VehicleReportFinancialSummary
    
    # --- Dados Detalhados ---
    costs_detailed: List[VehicleCostPublic]
    fuel_logs_detailed: List[FuelLogPublic]
    maintenance_detailed: List[MaintenanceRequestPublic]
    
    class Config:
        from_attributes = True

class DriverPerformanceEntry(BaseModel):
    """Representa a linha de dados para um único motorista no relatório."""
    driver_id: int
    driver_name: str
    total_journeys: int = 0
    total_distance_km: float = 0.0
    total_fuel_liters: float = 0.0
    average_consumption: float = 0.0
    total_fuel_cost: float = 0.0
    cost_per_km: float = 0.0
    maintenance_requests: int = 0

class DriverPerformanceReport(BaseModel):
    """Schema principal para o Relatório de Desempenho de Motoristas."""
    report_period_start: date
    report_period_end: date
    generated_at: datetime
    drivers_performance: List[DriverPerformanceEntry]

    class Config:
        from_attributes = True

class FleetReportSummary(BaseModel):
    """Resumo geral da frota no período."""
    total_cost: float = 0.0
    total_distance_km: float = 0.0
    overall_cost_per_km: float = 0.0
    
class VehicleRankingEntry(BaseModel):
    """Entrada para os rankings de veículos."""
    vehicle_id: int
    vehicle_identifier: str
    value: float
    unit: str

class FleetManagementReport(BaseModel):
    """Schema principal para o Relatório Gerencial da Frota."""
    report_period_start: date
    report_period_end: date
    generated_at: datetime
    
    summary: FleetReportSummary
    costs_by_category: Dict[str, float] = {}
    
    # Rankings
    top_5_most_expensive_vehicles: List[VehicleRankingEntry]
    top_5_highest_cost_per_km_vehicles: List[VehicleRankingEntry]
    top_5_most_efficient_vehicles: List[VehicleRankingEntry]
    top_5_least_efficient_vehicles: List[VehicleRankingEntry]

    class Config:
        from_attributes = True
