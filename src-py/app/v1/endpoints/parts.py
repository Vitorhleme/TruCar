from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid
import shutil
from pathlib import Path
from pydantic import BaseModel
import logging # (Manter para logs)
import aiofiles # Importamos, mas não vamos usar no 'create'
from sqlalchemy.exc import IntegrityError
from app import crud
from app.api import deps
from app.models.user_model import User
from app.models.part_model import PartCategory, InventoryItemStatus
from app.models.notification_model import NotificationType
from app.schemas.part_schema import PartPublic, PartCreate, PartUpdate, InventoryItemPublic, PartListPublic
from app.schemas.inventory_transaction_schema import TransactionPublic
from app.crud import crud_part 
from app.models.inventory_transaction_model import TransactionType

router = APIRouter()

UPLOAD_DIRECTORY = Path("static/uploads/parts")
UPLOAD_INVOICE_DIRECTORY = Path("static/uploads/invoices")
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
UPLOAD_INVOICE_DIRECTORY.mkdir(parents=True, exist_ok=True)

# Função de upload assíncrona (usada apenas pelo 'update_part' agora)
async def save_upload_file(upload_file: UploadFile, directory: Path) -> str:
    if not upload_file:
        return None
        
    extension = Path(upload_file.filename).suffix if upload_file.filename else ""
    unique_filename = f"{uuid.uuid4()}{extension}"
    file_path = directory / unique_filename
    
    try:
        async with aiofiles.open(file_path, "wb") as buffer:
            while content := await upload_file.read(1024 * 1024):
                await buffer.write(content)
    except Exception as e:
        logging.error(f"Falha ao salvar arquivo: {e}")
        return None
    finally:
        await upload_file.close()
        
    return f"/{file_path}"


# --- 1. CORREÇÃO EM 'create_part' (REMOVENDO LÓGICA) ---
# Removido o 'response_model' E a lógica de upload de arquivo
@router.post("/", status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(deps.check_demo_limit("parts"))])
async def create_part(
    name: str = Form(...),
    category: str = Form(...), # <--- Recebido como string
    minimum_stock: int = Form(...),
    initial_quantity: int = Form(0), 
    db: AsyncSession = Depends(deps.get_db),
    part_number: Optional[str] = Form(None),
    brand: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    value: Optional[float] = Form(None),
    serial_number: Optional[str] = Form(None), # <--- Ponto de falha (Unique)
    lifespan_km: Optional[int] = Form(None),
    current_user: User = Depends(deps.get_current_active_manager)
):
    
    # --- 2. ADICIONAR VALIDAÇÃO DE ENUM (Igual ao update_part) ---
    try:
        category_enum = PartCategory(category)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Valor de categoria inválido: '{category}'. Valores esperados: {[e.value for e in PartCategory]}"
        )
    # --- FIM DA VALIDAÇÃO ---

    part_in = PartCreate(
        name=name, 
        category=category_enum, # <--- 3. Usar o Enum validado
        minimum_stock=minimum_stock,
        initial_quantity=initial_quantity,
        part_number=part_number, 
        brand=brand, 
        location=location, 
        notes=notes, 
        value=value,
        serial_number=serial_number,
        lifespan_km=lifespan_km
    )
    
    photo_url, invoice_url = None, None
    
    try:
        # 1. CRUD (NÃO FAZ COMMIT)
        part_db = await crud_part.create(
            db=db, part_in=part_in, organization_id=current_user.organization_id, 
            user_id=current_user.id, photo_url=photo_url, invoice_url=invoice_url
        )
        
        # --- A SOLUÇÃO ESTÁ AQUI ---
        # 2. Capture o ID ANTES do commit, enquanto a sessão está ativa.
        part_id_to_return = part_db.id
        
        # 3. ENDPOINT FAZ COMMIT
        await db.commit()
        
        # 4. Retorne o ID que você salvou (um int), não o objeto part_db
        return {"id": part_id_to_return, "message": "Peça criada com sucesso."}
        # --- FIM DA SOLUÇÃO ---
        
    except ValueError as e:
        await db.rollback() 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        
    except IntegrityError as e: # (Manter da solução anterior)
        await db.rollback()
        logging.warning(f"Erro de integridade ao criar peça: {e}")
        if "unique constraint failed: parts.serial_number" in str(e).lower():
             raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"O número de série '{serial_number}' já está em uso por outra peça."
            )
        raise HTTPException(status_code=500, detail=f"Erro de integridade no banco: {e}")
        
    except Exception as e: 
        await db.rollback()
        logging.error(f"Erro ao criar peça: {e}", exc_info=True) # Loga o erro real
        raise HTTPException(status_code=500, detail=f"Erro ao criar peça: {e}")
    

# A função 'update_part' (Editar) agora é usada para adicionar as fotos
@router.put("/{part_id}") 
async def update_part(
    part_id: int,
    background_tasks: BackgroundTasks,
    name: str = Form(...),
    category: str = Form(...), 
    minimum_stock: int = Form(...),
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
    
    # Validação de Categoria (da solução anterior)
    try:
        category_enum = PartCategory(category)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Valor de categoria inválido: '{category}'. Valores esperados: {[e.value for e in PartCategory]}"
        )

    db_part = await crud_part.get_simple(db, part_id=part_id, organization_id=current_user.organization_id)
    if not db_part:
        raise HTTPException(status_code=404, detail="Peça não encontrada.")
        
    part_in = PartUpdate(
        name=name, category=category_enum, minimum_stock=minimum_stock, part_number=part_number, 
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
    
    try:
        await crud_part.update( # <--- Chamamos 'update'
            db=db, db_obj=db_part, obj_in=part_in, photo_url=photo_url, invoice_url=invoice_url
        )
        await db.commit() # <--- Commitamos
        
        # --- 2. NÃO RECARREGUE O OBJETO ---
        # Removido: part_with_stock = await crud_part.get_part_with_stock(...)
        
        # --- 3. RETORNE UMA MENSAGEM SIMPLES ---
        # O frontend vai chamar fetchParts() de qualquer maneira
        return {"message": "Peça atualizada com sucesso."}
        
    except IntegrityError as e:
        await db.rollback()
        logging.warning(f"Erro de integridade ao atualizar peça: {e}")
        if "unique constraint failed: parts.serial_number" in str(e).lower():
             raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail=f"O número de série '{serial_number}' já está em uso por outra peça."
            )
        raise HTTPException(status_code=500, detail=f"Erro de integridade no banco: {e}")
        
    except Exception as e: 
        await db.rollback()
        # Não vamos mais pegar o MissingGreenlet, mas mantemos o log
        logging.error(f"Erro genérico ao atualizar peça: {e}", exc_info=True) 
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar peça: {e}")
    
@router.get("/", response_model=List[PartListPublic])
async def read_parts(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: User = Depends(deps.get_current_active_manager)
):
    parts = await crud_part.get_multi_by_org(
        db, organization_id=current_user.organization_id, search=search, skip=skip, limit=limit
    )
    return parts

@router.delete("/{part_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_part(
    part_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_manager)
):
    db_part = await crud_part.get_simple(db, part_id=part_id, organization_id=current_user.organization_id)
    if not db_part:
        raise HTTPException(status_code=404, detail="Peça não encontrada.")
    
    try:
        await crud_part.remove(db=db, id=part_id, organization_id=current_user.organization_id)
        await db.commit()
    except Exception as e: 
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao deletar peça: {e}")


class AddItemsPayload(BaseModel):
    quantity: int
    notes: Optional[str] = None

# --- 4. CORREÇÃO EM 'add_inventory_items' (SUA LÓGICA) ---
# Removido o 'response_model=PartPublic'
@router.post("/{part_id}/add-items", status_code=status.HTTP_201_CREATED)
async def add_inventory_items(
    part_id: int,
    payload: AddItemsPayload,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_manager)
):
    
    # Buscamos o 'part' apenas para verificar se ele existe
    part = await crud_part.get_simple(db, part_id=part_id, organization_id=current_user.organization_id)
    if not part:
        raise HTTPException(status_code=404, detail="Peça (template) não encontrada.")
    if payload.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantidade deve ser maior que zero.")

    try:
        # --- ESTA É A LINHA DA CORREÇÃO ---
        # ANTES:
        # await crud_part.create_inventory_items(
        #     db=db, part=part, quantity=payload.quantity, 
        #     user_id=current_user.id, notes=payload.notes
        # )
        
        # DEPOIS:
        await crud_part.create_inventory_items(
            db=db, 
            part_id=part.id,  # Passamos o part_id
            organization_id=current_user.organization_id, # Passamos o org_id (seguro)
            quantity=payload.quantity, 
            user_id=current_user.id, 
            notes=payload.notes
        )
        # --- FIM DA CORREÇÃO ---
        
        await db.commit()
    
    except Exception as e:
        await db.rollback()
        # Adicionado log para ver erros futuros
        logging.error(f"Erro ao adicionar itens: {e}", exc_info=True) 
        raise HTTPException(status_code=500, detail=f"Erro ao adicionar itens: {e}")
    
    # SUA SOLUÇÃO: Retorna uma resposta simples de sucesso 201.
    return {"message": "Itens adicionados com sucesso."}

# --- O RESTO DO ARQUIVO NÃO PRECISA DE MUDANÇAS ---
class SetItemStatusPayload(BaseModel):
    new_status: InventoryItemStatus
    related_vehicle_id: Optional[int] = None
    notes: Optional[str] = None

@router.put("/items/{item_id}/set-status", response_model=InventoryItemPublic)
async def set_inventory_item_status(
    item_id: int,
    payload: SetItemStatusPayload,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_manager)
):
    item = await crud_part.get_item_by_id(db, item_id=item_id, organization_id=current_user.organization_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item de inventário não encontrado.")
    if item.status != InventoryItemStatus.DISPONIVEL:
        raise HTTPException(status_code=400, detail=f"Item não está disponível (status atual: {item.status}).")

    try:
        updated_item = await crud_part.change_item_status(
            db=db, item=item, new_status=payload.new_status,
            user_id=current_user.id, vehicle_id=payload.related_vehicle_id, notes=payload.notes
        )
        
        part = await crud_part.get_part_with_stock(db, part_id=item.part_id, organization_id=current_user.organization_id)
        if part and part.stock < part.minimum_stock:
            message = f"Estoque baixo para a peça '{part.name}'. Quantidade atual: {part.stock}."
            background_tasks.add_task(
                crud.notification.create_notification,
                # db=db, # Removido
                message=message,
                notification_type=NotificationType.LOW_STOCK,
                organization_id=part.organization_id, 
                send_to_managers=True,
                related_entity_type="part",
                related_entity_id=part.id
            )

        await db.commit()
        
        await db.refresh(updated_item, ["part"]) 
        return updated_item
        
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await db.rollback()
        logging.error(f"Erro ao mudar status do item: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao mudar status do item: {e}")


@router.get("/{part_id}/items", response_model=List[InventoryItemPublic])
async def get_items_for_part(
    part_id: int,
    status: Optional[InventoryItemStatus] = None,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_manager)
):
    part = await crud_part.get_simple(db, part_id=part_id, organization_id=current_user.organization_id)
    if not part:
        raise HTTPException(status_code=404, detail="Peça (template) não encontrada.")
    
    items = await crud_part.get_items_for_part(db, part_id=part_id, status=status)
    return items

@router.get("/{part_id}/history", response_model=List[TransactionPublic])
async def read_part_history(
    part_id: int,
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_manager)
):
    part = await crud_part.get_simple(db, part_id=part_id, organization_id=current_user.organization_id)
    if not part:
        raise HTTPException(status_code=404, detail="Peça não encontrada.")
        
    history = await crud.inventory_transaction.get_transactions_by_part_id(
        db, part_id=part_id, skip=skip, limit=limit
    )
    return history