# Em backend/app/api/v1/endpoints/fines.py

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.models.notification_model import NotificationType
from app import crud
from app.api import deps
from app.models.user_model import User, UserRole
from app.schemas.fine_schema import FineCreate, FineUpdate, FinePublic

router = APIRouter()

@router.post("/", response_model=FinePublic, status_code=status.HTTP_201_CREATED)
async def create_fine(
    *,
    db: AsyncSession = Depends(deps.get_db),
    background_tasks: BackgroundTasks,
    fine_in: FineCreate,
    current_user: User = Depends(deps.get_current_active_user)
):
    """Cria uma nova multa e notifica os gestores em segundo plano."""
    if current_user.role == UserRole.DRIVER:
        if fine_in.driver_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você só pode registrar multas para si mesmo."
            )
            
    fine = await crud.fine.create(db=db, fine_in=fine_in, organization_id=current_user.organization_id)
    
    # --- GATILHO DE NOTIFICAÇÃO EM SEGUNDO PLANO ---
    message = f"Nova multa de R${fine.value:.2f} registrada para o veículo."
    background_tasks.add_task(
        crud.notification.create_notification,
        db=db,
        message=message,
        notification_type=NotificationType.NEW_FINE_REGISTERED,
        organization_id=current_user.organization_id,
        send_to_managers=True,
        related_entity_type="fine",
        related_entity_id=fine.id,
        related_vehicle_id=fine.vehicle_id
    )
    # --- FIM DO GATILHO ---
    
    return fine

@router.get("/", response_model=List[FinePublic])
async def read_fines(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Lista as multas.
    - Gestores veem todas as multas da organização.
    - Motoristas veem apenas as suas próprias multas.
    """
    if current_user.role in [UserRole.CLIENTE_ATIVO, UserRole.CLIENTE_DEMO]:
        fines = await crud.fine.get_multi_by_org(
            db, organization_id=current_user.organization_id, skip=skip, limit=limit
        )
    elif current_user.role == UserRole.DRIVER:
        fines = await crud.fine.get_multi_by_driver(
            db, driver_id=current_user.id, organization_id=current_user.organization_id, skip=skip, limit=limit
        )
    else:
        fines = [] # Retorna lista vazia para outros perfis por segurança
        
    return fines

@router.put("/{fine_id}", response_model=FinePublic)
async def update_fine(
    *,
    db: AsyncSession = Depends(deps.get_db),
    fine_id: int,
    fine_in: FineUpdate,
    current_user: User = Depends(deps.get_current_active_manager)
):
    """Atualiza uma multa existente (Apenas Gestores)."""
    db_fine = await crud.fine.get(db, fine_id=fine_id, organization_id=current_user.organization_id)
    if not db_fine:
        raise HTTPException(status_code=404, detail="Multa não encontrada.")
    
    fine = await crud.fine.update(db=db, db_fine=db_fine, fine_in=fine_in)
    return fine

@router.delete("/{fine_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fine(
    *,
    db: AsyncSession = Depends(deps.get_db),
    fine_id: int,
    current_user: User = Depends(deps.get_current_active_manager)
):
    """Deleta uma multa (Apenas Gestores)."""
    db_fine = await crud.fine.get(db, fine_id=fine_id, organization_id=current_user.organization_id)
    if not db_fine:
        raise HTTPException(status_code=404, detail="Multa não encontrada.")
    
    await crud.fine.remove(db=db, db_fine=db_fine)