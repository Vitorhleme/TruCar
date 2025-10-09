from fastapi import APIRouter, Depends, status, HTTPException, Response, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.models.notification_model import NotificationType
from app import crud
from app.api import deps
from app.models.user_model import User, UserRole
from app.schemas.fuel_log_schema import FuelLogPublic, FuelLogCreate, FuelLogUpdate

router = APIRouter()

# --- ESTE ARQUIVO AGORA LIDA APENAS COM OPERAÇÕES MANUAIS ---

@router.post("/", response_model=FuelLogPublic, status_code=status.HTTP_201_CREATED)
async def create_fuel_log(
    *,
    db: AsyncSession = Depends(deps.get_db),
    background_tasks: BackgroundTasks,
    log_in: FuelLogCreate,
    current_user: User = Depends(deps.get_current_active_user),
):
    """Cria um novo registro de abastecimento e dispara alerta de consumo anormal."""
    # Define o user_id para o usuário logado se ele for um motorista e o campo estiver vazio
    final_user_id = current_user.id
    if current_user.role == UserRole.DRIVER and not log_in.user_id:
        final_user_id = current_user.id
    elif log_in.user_id:
        final_user_id = log_in.user_id

    fuel_log = await crud.fuel_log.create_fuel_log(
        db, log_in=log_in, user_id=final_user_id, organization_id=current_user.organization_id
    )

    # --- GATILHO DE NOTIFICAÇÃO (CONSUMO ANORMAL) ---
    vehicle = await crud.vehicle.get(db, id=fuel_log.vehicle_id, organization_id=current_user.organization_id)
    if vehicle:
        # Lógica para verificar o consumo (pode ser movida para um helper se ficar complexa)
        # Esta é uma lógica simplificada. Uma real precisaria de mais dados.
        # Por exemplo, pegar o último abastecimento para calcular a distância.
        # Vamos assumir que você tem uma função `check_consumption` para isso.
        is_abnormal, details = await crud.fuel_log.check_abnormal_consumption(db, fuel_log=fuel_log, vehicle=vehicle)
        if is_abnormal:
            background_tasks.add_task(
                crud.notification.create_notification,
                db=db,
                message=details,
                notification_type=NotificationType.ABNORMAL_FUEL_CONSUMPTION,
                organization_id=current_user.organization_id,
                send_to_managers=True,
                related_entity_type="fuel_log",
                related_entity_id=fuel_log.id,
                related_vehicle_id=vehicle.id
            )
    # --- FIM DO GATILHO ---

    return fuel_log



@router.get("/", response_model=List[FuelLogPublic])
async def read_fuel_logs(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
):
    """Retorna o histórico de abastecimentos."""
    if current_user.role in [UserRole.CLIENTE_ATIVO, UserRole.CLIENTE_DEMO]:
        return await crud.fuel_log.get_multi_by_org(
            db=db, organization_id=current_user.organization_id, skip=skip, limit=limit
        )
    else: # DRIVER
        return await crud.fuel_log.get_multi_by_user(
            db=db, user_id=current_user.id, organization_id=current_user.organization_id, skip=skip, limit=limit
        )

@router.get("/{log_id}", response_model=FuelLogPublic)
async def read_fuel_log_by_id(
    log_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_manager),
):
    log = await crud.fuel_log.get_fuel_log(db, log_id=log_id, organization_id=current_user.organization_id)
    if not log:
        raise HTTPException(status_code=404, detail="Registo de abastecimento não encontrado.")
    return log

@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fuel_log(
    log_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_manager),
):
    log_to_delete = await crud.fuel_log.get_fuel_log(db, log_id=log_id, organization_id=current_user.organization_id)
    if not log_to_delete:
        raise HTTPException(status_code=404, detail="Registo de abastecimento não encontrado.")
    
    await crud.fuel_log.remove_fuel_log(db, db_obj=log_to_delete)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

