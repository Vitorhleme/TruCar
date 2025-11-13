# ARQUIVO: app/schemas/inventory_transaction_schema.py

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.models.inventory_transaction_model import TransactionType

# --- 1. IMPORTAR OS SCHEMAS QUE SÃO SEGUROS (sem import circular) ---
from .user_schema import UserPublic
from .vehicle_schema import VehiclePublic
# NÃO importe part_schema aqui

# --- 2. Schema para criar uma nova transação (Sem mudança) ---
class TransactionCreate(BaseModel):
    transaction_type: TransactionType
    quantity: int 
    notes: Optional[str] = None
    related_vehicle_id: Optional[int] = None
    related_user_id: Optional[int] = None

# --- 3. Schema de Resposta com 'Forward References' (strings) ---
class TransactionPublic(BaseModel):
    id: int
    transaction_type: TransactionType
    notes: Optional[str]
    timestamp: datetime
    
    user: Optional[UserPublic] = None
    related_vehicle: Optional[VehiclePublic] = None
    related_user: Optional[UserPublic] = None
    
    item: Optional['InventoryItemPublic'] = None 
    part: Optional['PartPublic'] = Field(None, alias="part_template")

    class Config:
        from_attributes = True

# --- 4. IMPORTAR OS SCHEMAS REFERENCIADOS ---
from .part_schema import InventoryItemPublic, PartPublic
TransactionPublic.model_rebuild()


# --- 5. NOVO SCHEMA SIMPLIFICADO (A CORREÇÃO) ---
# Este schema é usado APENAS para o VehicleComponent.
# Ele só se importa com o usuário (o instalador).
class TransactionForComponent(BaseModel):
    id: int
    user: Optional[UserPublic] = None # Carrega apenas o usuário

    class Config:
        from_attributes = True