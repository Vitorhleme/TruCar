from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
import logging
import datetime # <--- IMPORTAR DATETIME

# --- NOVOS IMPORTS NECESSÁRIOS ---
from app.models.vehicle_component_model import VehicleComponent
from app.models.vehicle_cost_model import VehicleCost, CostType
from app.models.inventory_transaction_model import InventoryTransaction
# --- FIM DOS NOVOS IMPORTS ---

from app.crud.crud_user import count_by_org
from app.models.part_model import Part, InventoryItem, InventoryItemStatus, PartCategory
from . import crud_inventory_transaction as crud_transaction
from app.schemas.part_schema import PartCreate, PartUpdate
from app.models.inventory_transaction_model import TransactionType

# --- 1. CORREÇÃO: Esta função não precisa ser 'async' ---
def log_transaction(
    db: AsyncSession, *, item_id: int, part_id: int, user_id: int, 
    transaction_type: TransactionType, notes: Optional[str] = None, 
    related_vehicle_id: Optional[int] = None
) -> InventoryTransaction: # <--- Retorna o objeto de log
    """Apenas cria e adiciona o log à sessão, sem commit ou flush."""
    log_entry = InventoryTransaction(
        item_id=item_id,
        part_id=part_id,
        user_id=user_id,
        transaction_type=transaction_type,
        notes=notes,
        related_vehicle_id=related_vehicle_id
    )
    return log_entry


async def create_inventory_items(
    db: AsyncSession, *, part: Part, quantity: int, user_id: int, notes: Optional[str] = None
) -> List[InventoryItem]:
    logging.warning(f"ID DA SESSÃO NO CRUD: {id(db)}")
    """Cria itens e os adiciona à sessão, sem commit ou flush."""
    new_items = []
    for _ in range(quantity):
        new_item = InventoryItem(
            part_id=part.id,
            organization_id=part.organization_id,
            status=InventoryItemStatus.DISPONIVEL
        )
        db.add(new_item)
        new_items.append(new_item)
    
    await db.flush() 

    for new_item in new_items:
        # --- 2. CORREÇÃO: Remover 'await' ---
        log = log_transaction(
            db=db, item_id=new_item.id, part_id=part.id, user_id=user_id,
            transaction_type=TransactionType.ENTRADA,
            notes=notes or "Entrada de novo item"
        )
        db.add(log) # Adiciona o log aqui
        
    return new_items

# --- CORRIGIDO (Carrega o 'part' para sabermos o preço e nome) ---
async def get_item_by_id(db: AsyncSession, *, item_id: int, organization_id: int) -> Optional[InventoryItem]:
    """Busca um item serializado específico e os dados da peça (part) associada."""
    stmt = select(InventoryItem).where(
        InventoryItem.id == item_id, 
        InventoryItem.organization_id == organization_id
    ).options(
        selectinload(InventoryItem.part) # Carrega a relação com Part
    )
    result = await db.execute(stmt)
    return result.scalars().first()

# --- CORREÇÃO DEFINITIVA (Adiciona lógica de Custo e Componente) ---
# --- CORREÇÃO DEFINITIVA (Adiciona lógica de Custo e Componente) ---
async def change_item_status(
    db: AsyncSession, *, item: InventoryItem, new_status: InventoryItemStatus, 
    user_id: int, vehicle_id: Optional[int] = None, notes: Optional[str] = None
) -> InventoryItem:
    """Muda o status de um item E cria Custo/Componente se for instalação."""
    
    transaction_type_map = {
        InventoryItemStatus.EM_USO: TransactionType.SAIDA_USO,
        InventoryItemStatus.FIM_DE_VIDA: TransactionType.FIM_DE_VIDA
    }
    
    if new_status not in transaction_type_map:
        raise ValueError("Tipo de transação inválido para mudança de status.")

    # 1. Atualiza o Item
    item.status = new_status
    item.installed_on_vehicle_id = vehicle_id
    item.installed_at = func.now() if vehicle_id else None
    
    # 2. Cria o Log de Histórico (Corrigido sem 'await')
    log_entry = log_transaction( 
        db=db, item_id=item.id, part_id=item.part_id, user_id=user_id,
        transaction_type=transaction_type_map[new_status],
        notes=notes,
        related_vehicle_id=vehicle_id
    )
    
    db.add(item) # Adiciona o item atualizado
    
    # 3. Lógica de Custo e Componente
    if new_status == InventoryItemStatus.EM_USO and vehicle_id:
        
        part_template = item.part 
        
        if part_template:
            # 3a. Cria o "Componente"
            new_component = VehicleComponent(
                vehicle_id=vehicle_id,
                part_id=part_template.id,
                is_active=True,
                installation_date=func.now()
            )
            
            # Liga o Componente à Transação
            new_component.inventory_transaction = log_entry
            
            db.add(log_entry) # Adiciona o log (agora ligado)
            db.add(new_component) # Adiciona o componente
            
            # 3b. Cria o "Custo"
            if part_template.value and part_template.value > 0:
                new_cost = VehicleCost(
                    description=f"Instalação da peça: {part_template.name}",
                    amount=part_template.value,
                    date=datetime.date.today(), 
                    cost_type=CostType.PECAS_COMPONENTES, 
                    vehicle_id=vehicle_id,
                    organization_id=item.organization_id
                )
                db.add(new_cost)
        else:
            db.add(log_entry)
    else:
        db.add(log_entry)

    # O CRUD NÃO FAZ COMMIT
    await db.flush()
    # --- 3. CORREÇÃO: Remover 'db.refresh' ---
    # await db.refresh(item) # <--- REMOVIDO! Causa MissingGreenlet
    return item
# --- FIM DA CORREÇÃO DEFINITIVA ---


#
# --- RESTANTE DO FICHEIRO (Sem alterações) ---
#
async def get_simple(db: AsyncSession, *, part_id: int, organization_id: int) -> Optional[Part]:
    stmt = select(Part).where(Part.id == part_id, Part.organization_id == organization_id)
    result = await db.execute(stmt)
    return result.scalars().first()
    
async def get_part_with_stock(db: AsyncSession, *, part_id: int, organization_id: int) -> Optional[Part]:
    stmt = (
        select(Part)
        .where(Part.id == part_id, Part.organization_id == organization_id)
        .options(
            selectinload(Part.items) 
        )
    )
    part = (await db.execute(stmt)).scalars().first()
    
    if part:
        part.stock = sum(1 for item in part.items if item.status == InventoryItemStatus.DISPONIVEL)
    return part


async def get_multi_by_org(
    db: AsyncSession,
    *,
    organization_id: int,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Part]:
    
    subquery = (
        select(
            InventoryItem.part_id,
            func.count(InventoryItem.id).label("stock_count")
        )
        .where(InventoryItem.status == InventoryItemStatus.DISPONIVEL)
        .group_by(InventoryItem.part_id)
    ).subquery()

    stmt = (
        select(Part, func.coalesce(subquery.c.stock_count, 0))
        .outerjoin(subquery, Part.id == subquery.c.part_id)
        .where(Part.organization_id == organization_id)
        
        # --- ESTA LINHA É REMOVIDA ---
        # .options(selectinload(Part.items)) # <-- REMOVIDO! Causa ResponseValidationError
    )

    if search:
        search_term = f"%{search.lower()}%"
        stmt = stmt.where(
            or_(
                Part.name.ilike(search_term),
                Part.brand.ilike(search_term),
                Part.part_number.ilike(search_term)
            )
        )
    
    stmt = stmt.order_by(Part.name).offset(skip).limit(limit)
    
    result_rows = (await db.execute(stmt)).all()

    parts_with_stock = []
    for part, stock_count in result_rows:
        part.stock = stock_count 
        # part.items não será carregado aqui, o que é o correto
        parts_with_stock.append(part)
        
    return parts_with_stock

async def get_items_for_part(
    db: AsyncSession,
    *,
    part_id: int,
    status: Optional[InventoryItemStatus] = None
) -> List[InventoryItem]:
    stmt = select(InventoryItem).where(InventoryItem.part_id == part_id)
    if status:
        stmt = stmt.where(InventoryItem.status == status)
    
    items = (await db.execute(stmt.order_by(InventoryItem.id))).scalars().all()
    return items

async def create(db: AsyncSession, *, part_in: PartCreate, organization_id: int, user_id: int, photo_url: Optional[str] = None, invoice_url: Optional[str] = None) -> Part:
    """Cria uma nova Part (template) (Corrigido: Sem commit e Sem refresh)."""
    
    initial_quantity = part_in.initial_quantity
    part_data = part_in.model_dump(exclude={"initial_quantity"})

    db_obj = Part(
        **part_data,
        photo_url=photo_url,
        invoice_url=invoice_url,
        organization_id=organization_id
    )
    db.add(db_obj)
    await db.flush() # Isso já popula o db_obj.id

    if initial_quantity and initial_quantity > 0:
        await create_inventory_items(
            db=db,
            part=db_obj, # Passa o db_obj com o ID
            quantity=initial_quantity,
            user_id=user_id,
            notes=f"Carga inicial de {initial_quantity} itens no sistema."
        )
    
    # await db.refresh(db_obj) # <--- REMOVA ESTA LINHA. ELA CAUSA O ERRO.
    
    return db_obj # Retorna o objeto (com ID) para o endpoint

async def update(db: AsyncSession, *, db_obj: Part, obj_in: PartUpdate, photo_url: Optional[str], invoice_url: Optional[str]) -> Part:
    """Atualiza uma Part (Corrigido: Sem commit)."""
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    db_obj.photo_url = photo_url
    db_obj.invoice_url = invoice_url 
    
    db.add(db_obj)
    
    await db.flush()
    # --- 4. CORREÇÃO: Remover 'db.refresh' ---
    # await db.refresh(db_obj) # <--- REMOVIDO! Causa MissingGreenlet
    
    return db_obj

async def remove(db: AsyncSession, *, id: int, organization_id: int) -> Optional[Part]:
    """Remove uma Part (Corrigido: Sem commit)."""
    db_obj = await get_simple(db, part_id=id, organization_id=organization_id)
    if db_obj:
        await db.delete(db_obj)
    return db_obj