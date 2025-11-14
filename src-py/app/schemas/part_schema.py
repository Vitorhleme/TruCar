# ARQUIVO: app/schemas/part_schema.py

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.part_model import PartCategory, InventoryItemStatus
# NÃO importe inventory_transaction_schema aqui no topo

# --- 1. Schema para o Item Físico (Individual) ---
class InventoryItemPublic(BaseModel):
    id: int
    item_identifier: int  # <-- CORREÇÃO: Adicionado o ID local
    status: InventoryItemStatus
    part_id: int 
    organization_id: int
    installed_on_vehicle_id: Optional[int] = None
    created_at: datetime
    installed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# --- 2. Schemas Base para a Peça (Template) ---
class PartBase(BaseModel):
    name: str
    category: str 
    minimum_stock: int = 0
    part_number: Optional[str] = None
    brand: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    value: Optional[float] = None
    serial_number: Optional[str] = None
    lifespan_km: Optional[int] = None

class PartCreate(PartBase):
    initial_quantity: int = 0

class PartUpdate(PartBase):
    condition: Optional[str] = None 
    pass

# --- 3. Schema Público de LISTA (usado para GET /parts/) ---
class PartListPublic(PartBase):
    id: int
    organization_id: int
    photo_url: Optional[str] = None
    invoice_url: Optional[str] = None
    stock: int = Field(0, description="Estoque disponível (calculado)")
    class Config:
        from_attributes = True

# --- 4. Schema Público de DETALHE (Template) ---
class PartPublic(PartBase):
    id: int
    organization_id: int
    photo_url: Optional[str] = None
    invoice_url: Optional[str] = None
    stock: int = Field(0, description="Estoque disponível (calculado)")
    items: List[InventoryItemPublic] = [] # Mostra os itens físicos
    class Config:
        from_attributes = True

# --- 5. NOVO SCHEMA DE DETALHES DO ITEM (Para a nova página) ---
# Usamos strings (Forward Refs) para evitar a importação circular
class InventoryItemDetails(InventoryItemPublic):
    part: 'PartListPublic' # Carrega o "template" (sem recursão)
    transactions: List['TransactionPublic'] = [] # Carrega o histórico completo

# --- 6. CORREÇÃO DO IMPORT CIRCULAR: Importar e Reconstruir ---
from .inventory_transaction_schema import TransactionPublic 

InventoryItemPublic.model_rebuild()
PartPublic.model_rebuild()
PartListPublic.model_rebuild()
InventoryItemDetails.model_rebuild() # Agora ele pode encontrar 'TransactionPublic'
