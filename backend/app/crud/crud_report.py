from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from datetime import datetime, timedelta, date
from typing import List, Optional

from app import crud
# --- NOVOS IMPORTS ---
from app.models.user_model import User
from app.models.alert_model import Alert, AlertLevel
from app.models.goal_model import Goal
from app.schemas.dashboard_schema import KpiEfficiency, AlertSummary, GoalStatus, VehiclePosition
# --- FIM DOS NOVOS IMPORTS ---
from app.models.vehicle_model import Vehicle, VehicleStatus
from app.models.journey_model import Journey
from app.models.organization_model import Organization
from app.models.report_models import DashboardKPIs, KmPerDay, UpcomingMaintenance, CostByCategory, DashboardPodiumDriver
from app.models.vehicle_cost_model import VehicleCost
from app.schemas.report_schema import FleetManagementReport, VehicleRankingEntry, FleetReportSummary, DriverPerformanceEntry, VehicleConsolidatedReport, VehicleReportPerformanceSummary, VehicleReportFinancialSummary, DriverPerformanceReport  # <-- ImportarDriverPerformanceEntry
from app.models.fuel_log_model import FuelLog
from app.models.maintenance_model import MaintenanceRequest


# --- NOVA FUNÇÃO HELPER ---

async def get_fleet_management_data(
    db: AsyncSession, *, start_date: date, end_date: date, organization_id: int
) -> FleetManagementReport:
    """
    Agrega dados de custo e performance de toda a frota para um período.
    """
    # 1. Obter todos os veículos da organização
    vehicles_stmt = select(Vehicle).where(Vehicle.organization_id == organization_id)
    vehicles = (await db.execute(vehicles_stmt)).scalars().all()
    
    vehicle_ids = [v.id for v in vehicles]

    # 2. Obter todos os custos e abastecimentos do período em consultas otimizadas
    costs_stmt = select(VehicleCost).where(
        VehicleCost.organization_id == organization_id,
        VehicleCost.date.between(start_date, end_date)
    )
    fuel_logs_stmt = select(FuelLog).where(
        FuelLog.organization_id == organization_id,
        func.date(FuelLog.timestamp).between(start_date, end_date)
    )
    
    all_costs = (await db.execute(costs_stmt)).scalars().all()
    all_fuel_logs = (await db.execute(fuel_logs_stmt)).scalars().all()

    # 3. Calcular Resumos e Agregações Gerais
    total_fleet_cost = sum(c.amount for c in all_costs)
    
    costs_by_category: Dict[str, float] = {}
    for cost in all_costs:
        category_key = str(cost.cost_type.value)
        costs_by_category[category_key] = costs_by_category.get(category_key, 0) + cost.amount

    # 4. Processar dados por veículo para criar os rankings
    vehicle_metrics: List[Dict] = []
    total_fleet_distance = 0.0

    for vehicle in vehicles:
        costs = [c for c in all_costs if c.vehicle_id == vehicle.id]
        fuel_logs = [f for f in all_fuel_logs if f.vehicle_id == vehicle.id]
        
        total_cost = sum(c.amount for c in costs)
        
        distance = 0.0
        if len(fuel_logs) > 1:
            sorted_logs = sorted(fuel_logs, key=lambda log: log.odometer or 0)
            min_odo = sorted_logs[0].odometer or 0
            max_odo = sorted_logs[-1].odometer or 0
            distance = float(max_odo - min_odo)
        
        total_fleet_distance += distance
        
        total_liters = sum(log.liters for log in fuel_logs if log.liters)
        avg_consumption = (distance / total_liters) if total_liters > 0 else 0
        cost_per_km = (total_cost / distance) if distance > 0 else 0

        vehicle_metrics.append({
            "id": vehicle.id,
            "identifier": vehicle.license_plate or vehicle.identifier,
            "total_cost": total_cost,
            "cost_per_km": cost_per_km,
            "avg_consumption": avg_consumption
        })

    # 5. Criar os Rankings
    # Usamos `lambda` para ordenar pelo valor desejado. `or 0` trata casos nulos.
    top_expensive = sorted(vehicle_metrics, key=lambda v: v.get('total_cost', 0), reverse=True)[:5]
    top_cost_per_km = sorted(vehicle_metrics, key=lambda v: v.get('cost_per_km', 0), reverse=True)[:5]
    top_efficient = sorted(vehicle_metrics, key=lambda v: v.get('avg_consumption', 0), reverse=True)[:5]
    least_efficient = sorted([v for v in vehicle_metrics if v.get('avg_consumption', 0) > 0], key=lambda v: v.get('avg_consumption', 0))[:5]

    # 6. Montar o objeto final do relatório
    summary = FleetReportSummary(
        total_cost=total_fleet_cost,
        total_distance_km=total_fleet_distance,
        overall_cost_per_km=(total_fleet_cost / total_fleet_distance) if total_fleet_distance > 0 else 0
    )

    report_data = FleetManagementReport(
        report_period_start=start_date,
        report_period_end=end_date,
        generated_at=datetime.utcnow(),
        summary=summary,
        costs_by_category=costs_by_category,
        top_5_most_expensive_vehicles=[VehicleRankingEntry(vehicle_id=v['id'], vehicle_identifier=v['identifier'], value=v['total_cost'], unit='R$') for v in top_expensive],
        top_5_highest_cost_per_km_vehicles=[VehicleRankingEntry(vehicle_id=v['id'], vehicle_identifier=v['identifier'], value=v['cost_per_km'], unit='R$/km') for v in top_cost_per_km],
        top_5_most_efficient_vehicles=[VehicleRankingEntry(vehicle_id=v['id'], vehicle_identifier=v['identifier'], value=v['avg_consumption'], unit='km/l') for v in top_efficient],
        top_5_least_efficient_vehicles=[VehicleRankingEntry(vehicle_id=v['id'], vehicle_identifier=v['identifier'], value=v['avg_consumption'], unit='km/l') for v in least_efficient]
    )
    
    return report_data

def _format_relative_time(dt: datetime) -> str:
    """Formata um datetime em uma string de tempo relativo (ex: 'há 5 minutos')."""
    now = datetime.utcnow()
    delta = now - dt
    seconds = delta.total_seconds()
    
    if seconds < 60:
        return "agora mesmo"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"há {minutes} minuto{'s' if minutes > 1 else ''}"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"há {hours} hora{'s' if hours > 1 else ''}"
    else:
        days = int(seconds / 86400)
        return f"há {days} dia{'s' if days > 1 else ''}"

# --- FUNÇÕES EXISTENTES (sem alterações) ---
async def get_dashboard_kpis(db: AsyncSession, *, organization_id: int) -> dict:
    # ... seu código existente ...
    stmt = select(Vehicle.status, func.count(Vehicle.id)).where(
        Vehicle.organization_id == organization_id
    ).group_by(Vehicle.status)
    
    result = await db.execute(stmt)
    status_counts = {status: count for status, count in result.all()}

    kpis_model = DashboardKPIs(
        total_vehicles=sum(status_counts.values()),
        available_vehicles=status_counts.get(VehicleStatus.AVAILABLE.value, 0),
        in_use_vehicles=status_counts.get(VehicleStatus.IN_USE.value, 0),
        maintenance_vehicles=status_counts.get(VehicleStatus.MAINTENANCE.value, 0),
    )
    return kpis_model.model_dump()


async def get_costs_by_category_last_30_days(db: AsyncSession, *, organization_id: int, start_date: date | None = None) -> List[CostByCategory]:
    """Agrega os custos totais por categoria. Usa os últimos 30 dias se start_date não for fornecido."""
    if not start_date:
        start_date = datetime.utcnow().date() - timedelta(days=30)
    
    stmt = (
        select(
            VehicleCost.cost_type,
            func.sum(VehicleCost.amount).label("total_amount")
        )
        .where(
            VehicleCost.organization_id == organization_id,
            VehicleCost.date >= start_date
        )
        .group_by(VehicleCost.cost_type)
        .order_by(func.sum(VehicleCost.amount).desc())
    )
    
    result = await db.execute(stmt)
    return [CostByCategory(cost_type=row.cost_type.value, total_amount=float(row.total_amount or 0)) for row in result.all()]


async def get_podium_drivers(db: AsyncSession, *, organization_id: int) -> List[DashboardPodiumDriver]:
    leaderboard_data = await crud.user.get_leaderboard_data(db, organization_id=organization_id)
    top_drivers_raw = leaderboard_data.get("leaderboard", [])[:3]
    return [DashboardPodiumDriver.model_validate(driver_data) for driver_data in top_drivers_raw]


async def get_km_per_day_last_30_days(db: AsyncSession, *, organization_id: int, start_date: date | None = None) -> List[KmPerDay]:
    """Calcula a distância/duração total por dia. Usa os últimos 30 dias se start_date não for fornecido."""
    if not start_date:
        start_date = datetime.utcnow().date() - timedelta(days=30)
        
    org = await db.get(Organization, organization_id)
    if not org:
        return []

    if org.sector == 'agronegocio':
        distance_col = func.sum(Journey.end_engine_hours - Journey.start_engine_hours)
        filter_col = Journey.end_engine_hours.is_not(None)
    else:
        distance_col = func.sum(Journey.end_mileage - Journey.start_mileage)
        filter_col = Journey.end_mileage.is_not(None)

    stmt = (
        select(
            func.date(Journey.start_time).label("date"),
            distance_col.label("total_km")
        )
        .where(
            Journey.organization_id == organization_id,
            Journey.is_active == False,
            func.date(Journey.start_time) >= start_date,
            filter_col
        )
        .group_by(func.date(Journey.start_time))
        .order_by(func.date(Journey.start_time))
    )

    result = await db.execute(stmt)
    return [KmPerDay(date=row.date, total_km=float(row.total_km or 0)) for row in result.all()]


async def get_upcoming_maintenances(db: AsyncSession, *, organization_id: int) -> List[UpcomingMaintenance]:
    # ... seu código existente ...
    today = datetime.utcnow().date()
    in_30_days = today + timedelta(days=30)
    stmt = (
        select(Vehicle)
        .where(
            Vehicle.organization_id == organization_id,
            or_(
                Vehicle.next_maintenance_date.between(today, in_30_days),
                (Vehicle.next_maintenance_km - Vehicle.current_km <= 1000)
            )
        )
        .order_by(Vehicle.next_maintenance_date.asc(), Vehicle.next_maintenance_km.asc())
        .limit(10)
    )
    result = await db.execute(stmt)
    vehicles = result.scalars().all()
    return [
        UpcomingMaintenance(
            vehicle_info=f"{v.brand} {v.model} ({v.license_plate or v.identifier})",
            due_date=v.next_maintenance_date,
            due_km=v.next_maintenance_km
        ) for v in vehicles
    ]

# --- NOVAS FUNÇÕES PARA O DASHBOARD AVANÇADO ---

async def get_efficiency_kpis(db: AsyncSession, *, organization_id: int, start_date: date) -> KpiEfficiency:
    """Calcula KPIs de eficiência como custo por km e taxa de utilização."""
    # Custo por KM
    costs_stmt = select(func.sum(VehicleCost.amount)).where(
        VehicleCost.organization_id == organization_id,
        VehicleCost.date >= start_date
    )
    total_costs = (await db.execute(costs_stmt)).scalar_one_or_none() or 0

    km_data = await get_km_per_day_last_30_days(db, organization_id=organization_id, start_date=start_date)
    total_km = sum(item.total_km for item in km_data)
    
    cost_per_km = (total_costs / total_km) if total_km > 0 else 0

    # Taxa de Utilização (simplificada)
    total_vehicles_stmt = select(func.count(Vehicle.id)).where(Vehicle.organization_id == organization_id)
    total_vehicles = (await db.execute(total_vehicles_stmt)).scalar_one()

    in_use_vehicles_stmt = select(func.count(Vehicle.id)).where(
        Vehicle.organization_id == organization_id,
        Vehicle.status == VehicleStatus.IN_USE
    )
    in_use_vehicles = (await db.execute(in_use_vehicles_stmt)).scalar_one()

    utilization_rate = (in_use_vehicles / total_vehicles) * 100 if total_vehicles > 0 else 0

    return KpiEfficiency(cost_per_km=cost_per_km, utilization_rate=utilization_rate)


async def get_recent_alerts(db: AsyncSession, *, organization_id: int) -> List[AlertSummary]:
    """Busca os 5 alertas mais recentes para a organização."""
    stmt = (
        select(Alert, Vehicle.license_plate, Vehicle.identifier, User.full_name)
        .outerjoin(Vehicle, Alert.vehicle_id == Vehicle.id)
        .outerjoin(User, Alert.driver_id == User.id)
        .where(Alert.organization_id == organization_id)
        .order_by(Alert.timestamp.desc())
        .limit(5)
    )
    result = await db.execute(stmt)
    alerts = []
    for row in result.all():
        alert, license_plate, identifier, full_name = row
        
        subtitle = f"Veículo: {license_plate or identifier or 'N/A'}"
        if full_name:
            subtitle += f" | Motorista: {full_name}"

        alerts.append(AlertSummary(
            id=alert.id,
            icon="warning" if alert.level != AlertLevel.INFO else "info",
            color="negative" if alert.level == AlertLevel.CRITICAL else ("warning" if alert.level == AlertLevel.WARNING else "info"),
            title=alert.message,
            subtitle=subtitle,
            time=_format_relative_time(alert.timestamp)
        ))
    return alerts


async def get_active_goal_with_progress(db: AsyncSession, *, organization_id: int) -> Optional[GoalStatus]:
    """Busca a meta ativa para o período atual e calcula seu progresso."""
    today = datetime.utcnow().date()
    stmt = select(Goal).where(
        Goal.organization_id == organization_id,
        Goal.period_start <= today,
        Goal.period_end >= today
    ).order_by(Goal.id.desc())
    
    active_goal = (await db.execute(stmt)).scalars().first()
    if not active_goal:
        return None

    # Lógica para calcular o valor atual - simplificado para custo total
    # Pode ser expandido para outros tipos de metas
    current_value = 0
    if active_goal.unit == "R$":
        costs_stmt = select(func.sum(VehicleCost.amount)).where(
            VehicleCost.organization_id == organization_id,
            VehicleCost.date.between(active_goal.period_start, active_goal.period_end)
        )
        current_value = (await db.execute(costs_stmt)).scalar_one_or_none() or 0

    return GoalStatus(
        title=active_goal.title,
        current_value=current_value,
        target_value=active_goal.target_value,
        unit=active_goal.unit
    )


async def get_vehicle_positions(db: AsyncSession, *, organization_id: int) -> List[VehiclePosition]:
    """Retorna a posição de todos os veículos para o mapa."""
    stmt = select(Vehicle).where(
        Vehicle.organization_id == organization_id,
        Vehicle.last_latitude.is_not(None),
        Vehicle.last_longitude.is_not(None),
    )
    result = await db.execute(stmt)
    vehicles = result.scalars().all()
    return [VehiclePosition.from_orm(v) for v in vehicles]
    
async def get_vehicle_consolidated_data(
    db: AsyncSession, *, vehicle_id: int, start_date: date, end_date: date, organization_id: int
) -> VehicleConsolidatedReport:

    # 1. Busca o veículo para garantir que ele existe e pertence à organização
    vehicle = await db.get(Vehicle, vehicle_id)
    if not vehicle or vehicle.organization_id != organization_id:
        raise ValueError("Veículo não encontrado ou não pertence à organização.")

    # 2. Busca os dados detalhados dentro do período
    costs_stmt = select(VehicleCost).where(
        VehicleCost.vehicle_id == vehicle_id,
        VehicleCost.date.between(start_date, end_date)
    )
    fuel_logs_stmt = select(FuelLog).where(
        FuelLog.vehicle_id == vehicle_id,
        func.date(FuelLog.timestamp).between(start_date, end_date)
    )
    maintenance_stmt = select(MaintenanceRequest).where(
        MaintenanceRequest.vehicle_id == vehicle_id,
        func.date(MaintenanceRequest.created_at).between(start_date, end_date)
    )
    
    costs = (await db.execute(costs_stmt)).scalars().all()
    fuel_logs = (await db.execute(fuel_logs_stmt)).scalars().all()
    maintenances = (await db.execute(maintenance_stmt)).scalars().all()

    # 3. Calcula os resumos de performance e financeiro
    # Performance
    total_liters = sum(log.liters for log in fuel_logs if log.liters)
    
    # Para distância, consideramos o odômetro dos abastecimentos
    if len(fuel_logs) > 1:
        # Ordena por odômetro para pegar o primeiro e o último registro no período
        sorted_logs = sorted(fuel_logs, key=lambda log: log.odometer or 0)
        min_odometer = sorted_logs[0].odometer or 0
        max_odometer = sorted_logs[-1].odometer or 0
        total_distance = max_odometer - min_odometer
    else:
        total_distance = 0

    avg_consumption = (total_distance / total_liters) if total_liters > 0 else 0

    performance_summary = VehicleReportPerformanceSummary(
        total_distance_km=total_distance,
        total_fuel_liters=total_liters,
        average_consumption=avg_consumption
    )

    # Financeiro
    total_costs = sum(cost.amount for cost in costs)
    cost_per_km = (total_costs / total_distance) if total_distance > 0 else 0
    
    costs_by_category = {}
    for cost in costs:
        category_key = str(cost.cost_type.value)
        costs_by_category[category_key] = costs_by_category.get(category_key, 0) + cost.amount

    financial_summary = VehicleReportFinancialSummary(
        total_costs=total_costs,
        cost_per_km=cost_per_km,
        costs_by_category=costs_by_category
    )

    # 4. Monta o objeto final do relatório
    report_data = VehicleConsolidatedReport(
        vehicle_id=vehicle.id,
        vehicle_identifier=vehicle.license_plate or vehicle.identifier,
        vehicle_model=f"{vehicle.brand} {vehicle.model}",
        report_period_start=start_date,
        report_period_end=end_date,
        generated_at=datetime.utcnow(),
        performance_summary=performance_summary,
        financial_summary=financial_summary,
        costs_detailed=costs,
        fuel_logs_detailed=fuel_logs,
        maintenance_detailed=maintenances
    )

    return report_data

async def get_driver_performance_data(
    db: AsyncSession, *, start_date: date, end_date: date, organization_id: int
) -> DriverPerformanceReport:
    """
    Busca e agrega dados de desempenho para todos os motoristas de uma organização
    em um período específico.
    """
    # 1. Busca todos os motoristas da organização
    drivers_stmt = select(User).where(
        User.organization_id == organization_id, 
        User.role == 'driver'
    )
    drivers = (await db.execute(drivers_stmt)).scalars().all()

    drivers_performance_data: List[DriverPerformanceEntry] = []

    # 2. Itera sobre cada motorista para coletar e agregar seus dados
    for driver in drivers:
        # Métricas de Viagens (Journeys)
        journeys_stmt = select(func.count(Journey.id), func.sum(Journey.distance_km)).where(
            Journey.driver_id == driver.id,
            func.date(Journey.start_time).between(start_date, end_date)
        )
        journey_metrics = (await db.execute(journeys_stmt)).first()
        total_journeys = journey_metrics[0] or 0
        total_distance = float(journey_metrics[1] or 0.0)

        # Métricas de Combustível (FuelLog)
        fuel_stmt = select(func.sum(FuelLog.liters), func.sum(FuelLog.total_cost)).where(
            FuelLog.user_id == driver.id,
            func.date(FuelLog.timestamp).between(start_date, end_date)
        )
        fuel_metrics = (await db.execute(fuel_stmt)).first()
        total_liters = float(fuel_metrics[0] or 0.0)
        total_fuel_cost = float(fuel_metrics[1] or 0.0)

        # Métricas de Manutenção
        maintenance_stmt = select(func.count(MaintenanceRequest.id)).where(
            MaintenanceRequest.reported_by_id == driver.id,
            func.date(MaintenanceRequest.created_at).between(start_date, end_date)
        )
        maintenance_count = (await db.execute(maintenance_stmt)).scalar_one_or_none() or 0
        
        # Cálculos derivados
        avg_consumption = (total_distance / total_liters) if total_liters > 0 else 0
        cost_per_km = (total_fuel_cost / total_distance) if total_distance > 0 else 0

        drivers_performance_data.append(
            DriverPerformanceEntry(
                driver_id=driver.id,
                driver_name=driver.full_name,
                total_journeys=total_journeys,
                total_distance_km=total_distance,
                total_fuel_liters=total_liters,
                average_consumption=avg_consumption,
                total_fuel_cost=total_fuel_cost,
                cost_per_km=cost_per_km,
                maintenance_requests=maintenance_count,
            )
        )

    # 3. Ordena o ranking pelo principal indicador (ex: Custo por KM)
    sorted_performance_data = sorted(drivers_performance_data, key=lambda d: d.cost_per_km, reverse=True)

    # 4. Monta o objeto final do relatório
    report_data = DriverPerformanceReport(
        report_period_start=start_date,
        report_period_end=end_date,
        generated_at=datetime.utcnow(),
        drivers_performance=sorted_performance_data
    )

    return report_data