from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload, joinedload
from typing import List, Optional

from app.crud.crud_user import count_by_org
from app.models.part_model import Part, InventoryItem, InventoryItemStatus, PartCategory
from . import crud_inventory_transaction as crud_transaction
from app.schemas.part_schema import PartCreate, PartUpdate
from app.models.inventory_transaction_model import TransactionType
from app.models.inventory_transaction_model import InventoryTransaction # <-- IMPORTAR

# --- FUNÇÃO HELPER PARA LOG (MODIFICADA) ---
def log_transaction(
    db: AsyncSession, *, item_id: int, part_id: int, user_id: int, 
    transaction_type: TransactionType, notes: Optional[str] = None, 
    related_vehicle_id: Optional[int] = None
):
    """Apenas cria e adiciona o log à sessão, sem commit ou flush."""
    log_entry = InventoryTransaction(
        item_id=item_id,
        part_id=part_id,
        user_id=user_id,
        transaction_type=transaction_type,
        notes=notes,
        related_vehicle_id=related_vehicle_id
    )
    db.add(log_entry)

#
# --- CRUD DO ITEM DE INVENTÁRIO (MODIFICADO) ---
#
async def create_inventory_items(
    db: AsyncSession, *, part: Part, quantity: int, user_id: int, notes: Optional[str] = None
) -> List[InventoryItem]:
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
    
    # Adicionamos os itens à sessão primeiro
    await db.flush() 

    # Agora que os itens têm IDs, podemos logar as transações
    for new_item in new_items:
        log_transaction(
            db=db, item_id=new_item.id, part_id=part.id, user_id=user_id,
            transaction_type=TransactionType.ENTRADA,
            notes=notes or "Entrada de novo item"
        )
        
    return new_items

async def get_item_by_id(db: AsyncSession, *, item_id: int, organization_id: int) -> Optional[InventoryItem]:
    """Busca um item serializado específico."""
    stmt = select(InventoryItem).where(
        InventoryItem.id == item_id, 
        InventoryItem.organization_id == organization_id
    )
    result = await db.execute(stmt)
    return result.scalars().first()

async def change_item_status(
    db: AsyncSession, *, item: InventoryItem, new_status: InventoryItemStatus, 
    user_id: int, vehicle_id: Optional[int] = None, notes: Optional[str] = None
) -> InventoryItem:
    """Muda o status de um item (Saída para Uso, Fim de Vida)."""
    
    transaction_type_map = {
        InventoryItemStatus.EM_USO: TransactionType.SAIDA_USO,
        InventoryItemStatus.FIM_DE_VIDA: TransactionType.FIM_DE_VIDA
    }
    
    if new_status not in transaction_type_map:
        raise ValueError("Tipo de transação inválido para mudança de status.")

    item.status = new_status
    item.installed_on_vehicle_id = vehicle_id
    item.installed_at = func.now() if vehicle_id else None
    
    log_transaction( # <-- Sem await
        db=db, item_id=item.id, part_id=item.part_id, user_id=user_id,
        transaction_type=transaction_type_map[new_status],
        notes=notes,
        related_vehicle_id=vehicle_id
    )
    
    db.add(item)
    # O commit foi movido para o endpoint
    await db.commit()
    await db.refresh(item)
    return item

#
# --- CRUD PART (ATUALIZADO) ---
#

async def get_simple(db: AsyncSession, *, part_id: int, organization_id: int) -> Optional[Part]:
    """Busca uma Part (template) simples, sem calcular estoque ou carregar itens."""
    stmt = select(Part).where(Part.id == part_id, Part.organization_id == organization_id)
    result = await db.execute(stmt)
    return result.scalars().first()
    
async def get_part_with_stock(db: AsyncSession, *, part_id: int, organization_id: int) -> Optional[Part]:
    """Busca uma Part (template) e calcula seu estoque e itens."""
    stmt = (
        select(Part)
        .where(Part.id == part_id, Part.organization_id == organization_id)
        .options(
            selectinload(Part.items) # Carrega todos os itens serializados
        )
    )
    part = (await db.execute(stmt)).scalars().first()
    
    if part:
        # Calcula o estoque dinamicamente
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
    """Retorna uma lista de Parts (templates), calculando o estoque para cada."""
    
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
        .options(selectinload(Part.items))
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
        parts_with_stock.append(part)
        
    return parts_with_stock

# --- NOVA FUNÇÃO (PARA CORRIGIR O ERRO 1) ---
async def get_items_for_part(
    db: AsyncSession,
    *,
    part_id: int,
    status: Optional[InventoryItemStatus] = None
) -> List[InventoryItem]:
    """Lista todos os itens serializados de um Part (template), opcionalmente por status."""
    stmt = select(InventoryItem).where(InventoryItem.part_id == part_id)
    if status:
        stmt = stmt.where(InventoryItem.status == status)
    
    items = (await db.execute(stmt.order_by(InventoryItem.id))).scalars().all()
    return items


async def create(db: AsyncSession, *, part_in: PartCreate, organization_id: int, user_id: int, photo_url: Optional[str] = None, invoice_url: Optional[str] = None) -> Part:
    """Cria uma nova Part (template) e, opcionalmente, seus primeiros itens."""
    
    initial_quantity = part_in.initial_quantity
    part_data = part_in.model_dump(exclude={"initial_quantity"})

    db_obj = Part(
        **part_data,
        photo_url=photo_url,
        invoice_url=invoice_url,
        organization_id=organization_id
    )
    db.add(db_obj)
    await db.flush() 

    if initial_quantity and initial_quantity > 0:
        await create_inventory_items(
            db=db,
            part=db_obj,
            quantity=initial_quantity,
            user_id=user_id,
            notes=f"Carga inicial de {initial_quantity} itens no sistema."
        )
    
    await db.commit() # Commit único
    
    # Recarrega com o estoque calculado para retornar o objeto correto
    db_obj = await get_part_with_stock(db, part_id=db_obj.id, organization_id=organization_id)
    return db_obj


async def update(db: AsyncSession, *, db_obj: Part, obj_in: PartUpdate, photo_url: Optional[str], invoice_url: Optional[str]) -> Part:
    # ... (sem mudança)
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    db_obj.photo_url = photo_url
    db_obj.invoice_url = invoice_url 
    
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    
    db_obj = await get_part_with_stock(db, part_id=db_obj.id, organization_id=db_obj.organization_id)
    return db_obj

async def remove(db: AsyncSession, *, id: int, organization_id: int) -> Optional[Part]:
    # ... (sem mudança)
    db_obj = await get_simple(db, part_id=id, organization_id=organization_id)
    if db_obj:
        await db.delete(db_obj)
        await db.commit()
    return db_obj