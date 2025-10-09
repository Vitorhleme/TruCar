from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid
import shutil
from pathlib import Path

from app import crud
from app.api import deps
from app.models.user_model import User
from app.models.part_model import PartCategory
from app.models.notification_model import NotificationType
from app.schemas.part_schema import PartPublic, PartCreate, PartUpdate, StockAdjustment
from app.schemas.inventory_transaction_schema import TransactionCreate, TransactionPublic
from app.models.inventory_transaction_model import TransactionType

router = APIRouter()

# --- DIRETÓRIOS DE UPLOAD ---
UPLOAD_DIRECTORY = Path("static/uploads/parts")
UPLOAD_INVOICE_DIRECTORY = Path("static/uploads/invoices")
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
UPLOAD_INVOICE_DIRECTORY.mkdir(parents=True, exist_ok=True)

# --- FUNÇÃO HELPER PARA SALVAR ARQUIVOS ---
async def save_upload_file(upload_file: UploadFile, directory: Path) -> str:
    extension = Path(upload_file.filename).suffix if upload_file.filename else ""
    unique_filename = f"{uuid.uuid4()}{extension}"
    file_path = directory / unique_filename
    
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
        
    return f"/{file_path}"


@router.post("/", response_model=PartPublic, status_code=status.HTTP_201_CREATED)
async def create_part(
    name: str = Form(...),
    category: str = Form(...),
    stock: int = Form(...),
    min_stock: int = Form(...),
    db: AsyncSession = Depends(deps.get_db),
    part_number: Optional[str] = Form(None),
    brand: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    value: Optional[float] = Form(None),
    serial_number: Optional[str] = Form(None),
    lifespan_km: Optional[int] = Form(None),
    file: Optional[UploadFile] = File(None),
    invoice_file: Optional[UploadFile] = File(None),
    current_user: User = Depends(deps.get_current_active_manager)
):
    """Cria uma nova peça no inventário, com valor e nota fiscal opcionais."""
    part_in = PartCreate(
        name=name, category=category, stock=stock, min_stock=min_stock,
        part_number=part_number, brand=brand, location=location, notes=notes, value=value,
        serial_number=serial_number,
        lifespan_km=lifespan_km
    )
    
    photo_url, invoice_url = None, None
    if file:
        photo_url = await save_upload_file(file, UPLOAD_DIRECTORY)
    if invoice_file:
        invoice_url = await save_upload_file(invoice_file, UPLOAD_INVOICE_DIRECTORY)
    
    try:
        part_db = await crud.part.create(
            db=db, part_in=part_in, organization_id=current_user.organization_id, 
            user_id=current_user.id, photo_url=photo_url, invoice_url=invoice_url
        )
        return part_db
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put("/{part_id}", response_model=PartPublic)
async def update_part(
    part_id: int,
    background_tasks: BackgroundTasks,
    name: str = Form(...),
    category: str = Form(...),
    min_stock: int = Form(...),
    db: AsyncSession = Depends(deps.get_db),
    part_number: Optional[str] = Form(None),
    brand: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    value: Optional[float] = Form(None),
    serial_number: Optional[str] = Form(None),
    lifespan_km: Optional[int] = Form(None),
    condition: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    invoice_file: Optional[UploadFile] = File(None),
    current_user: User = Depends(deps.get_current_active_manager)
):
    """Atualiza uma peça e dispara alerta se um pneu for marcado como 'ruim'."""
    db_part = await crud.part.get(db, id=part_id, organization_id=current_user.organization_id)
    if not db_part:
        raise HTTPException(status_code=404, detail="Peça não encontrada.")
        
    original_condition = db_part.condition if hasattr(db_part, 'condition') else None
    
    part_in = PartUpdate(
        name=name, category=category, min_stock=min_stock, part_number=part_number, 
        brand=brand, location=location, notes=notes, value=value,
        serial_number=serial_number,
        lifespan_km=lifespan_km,
        condition=condition
    )
    
    photo_url = db_part.photo_url
    if file:
        photo_url = await save_upload_file(file, UPLOAD_DIRECTORY)

    invoice_url = db_part.invoice_url
    if invoice_file:
        invoice_url = await save_upload_file(invoice_file, UPLOAD_INVOICE_DIRECTORY)
    
    updated_part = await crud.part.update(
        db=db, db_obj=db_part, obj_in=part_in, photo_url=photo_url, invoice_url=invoice_url
    )

    new_condition = updated_part.condition if hasattr(updated_part, 'condition') else None
    if updated_part.category == PartCategory.PNEU and new_condition == 'ruim' and original_condition != 'ruim':
        message = f"O pneu '{updated_part.name}' (Série: {updated_part.serial_number or 'N/A'}) foi marcado como 'ruim'."
        background_tasks.add_task(
            crud.notification.create_notification,
            db=db, message=message,
            notification_type=NotificationType.TIRE_STATUS_BAD,
            organization_id=updated_part.organization_id,
            send_to_managers=True,
            related_entity_type="part",
            related_entity_id=updated_part.id
        )
    
    return updated_part

@router.get("/", response_model=List[PartPublic])
async def read_parts(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: User = Depends(deps.get_current_active_manager)
):
    """Retorna a lista de peças do inventário."""
    parts = await crud.part.get_multi_by_org(
        db, organization_id=current_user.organization_id, search=search, skip=skip, limit=limit
    )
    return parts

@router.delete("/{part_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_part(
    part_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_manager)
):
    """Remove uma peça do inventário."""
    db_part = await crud.part.get(db, id=part_id, organization_id=current_user.organization_id)
    if not db_part:
        raise HTTPException(status_code=404, detail="Peça não encontrada.")
    await crud.part.remove(db=db, id=part_id, organization_id=current_user.organization_id)

@router.post("/{part_id}/transaction", response_model=TransactionPublic)
async def add_stock_transaction(
    part_id: int,
    transaction_in: TransactionCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_manager)
):
    """Registra uma movimentação de estoque e dispara alerta de estoque baixo."""
    part = await crud.part.get(db, id=part_id, organization_id=current_user.organization_id)
    if not part:
        raise HTTPException(status_code=404, detail="Peça não encontrada.")

    if transaction_in.transaction_type in [TransactionType.SAIDA_USO, TransactionType.SAIDA_FIM_DE_VIDA]:
        quantity_change = -abs(transaction_in.quantity)
    else:
        quantity_change = abs(transaction_in.quantity)

    try:
        transaction = await crud.inventory_transaction.create_transaction(
            db=db, part_id=part_id, user_id=current_user.id,
            transaction_type=transaction_in.transaction_type,
            quantity_change=quantity_change,
            notes=transaction_in.notes,
            related_vehicle_id=transaction_in.related_vehicle_id,
            related_user_id=transaction_in.related_user_id
        )
        
        part_after_transaction = await crud.part.get(db, id=part_id, organization_id=current_user.organization_id)
        if part_after_transaction and part_after_transaction.stock < part_after_transaction.minimum_stock:
            message = f"Estoque baixo para a peça '{part_after_transaction.name}'. Quantidade atual: {part_after_transaction.stock}."
            background_tasks.add_task(
                crud.notification.create_notification,
                db=db, message=message,
                notification_type=NotificationType.LOW_STOCK,
                organization_id=part_after_transaction.organization_id,
                send_to_managers=True,
                related_entity_type="part",
                related_entity_id=part_after_transaction.id
            )

        return transaction
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{part_id}/history", response_model=List[TransactionPublic])
async def read_part_history(
    part_id: int,
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_manager)
):
    """Retorna o histórico de movimentações de uma peça específica."""
    part = await crud.part.get(db, id=part_id, organization_id=current_user.organization_id)
    if not part:
        raise HTTPException(status_code=404, detail="Peça não encontrada.")
        
    history = await crud.inventory_transaction.get_transactions_by_part_id(
        db, part_id=part_id, skip=skip, limit=limit
    )
    return history