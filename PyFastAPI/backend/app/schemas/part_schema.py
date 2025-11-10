from pydantic import BaseModel
from typing import Optional, List
from app.models.inventory_transaction_model import TransactionType
# --- 1. IMPORTAR OS NOVOS MODELOS/SCHEMAS ---
from app.models.part_model import InventoryItemStatus
from datetime import datetime

#
# --- 2. NOVO SCHEMA PARA O ITEM INDIVIDUAL ---
# (Precisamos dele aqui para o PartPublic)
#
class InventoryItemBase(BaseModel):
    status: InventoryItemStatus
    part_id: int
    
class InventoryItemPublic(InventoryItemBase):
    id: int # Este é o "código"
    installed_on_vehicle_id: Optional[int] = None
    created_at: datetime
    installed_at: Optional[datetime] = None

    class Config: # Pydantic v1 usa Config
        from_attributes = True

#
# --- 3. SCHEMAS 'PART' ATUALIZADOS ---
#
class PartBase(BaseModel):
    name: str
    category: str
    serial_number: Optional[str] = None
    part_number: Optional[str] = None
    brand: Optional[str] = None
    # stock: int  <-- REMOVIDO DA BASE!
    location: Optional[str] = None  
    notes: Optional[str] = None
    value: Optional[float] = None
    lifespan_km: Optional[int] = None
    minimum_stock: Optional[int] = 0

class PartCreate(PartBase):
    initial_quantity: Optional[int] = 0 

class PartUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    serial_number: Optional[str] = None
    part_number: Optional[str] = None
    brand: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    value: Optional[float] = None
    lifespan_km: Optional[int] = None
    minimum_stock: Optional[int] = 0

class Part(PartBase):
    id: int
    photo_url: Optional[str] = None
    invoice_url: Optional[str] = None

    class Config:
        from_attributes = True

#
# --- 4. CAMPO 'stock' E 'items' ADICIONADOS AQUI ---
#
class PartPublic(Part):
    stock: int = 0 # <-- O estoque calculado
    items: List[InventoryItemPublic] = [] # <-- A lista de itens serializados