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
    quantity: int # A quantidade sempre será positiva no payload
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
    
    # Use o NOME DA CLASSE como string (ForwardRef)
    item: Optional['InventoryItemPublic'] = None 
    
    # Use o NOME DA CLASSE como string e o alias
    part: Optional['PartPublic'] = Field(None, alias="part_template")

    class Config:
        from_attributes = True

# --- 4. IMPORTAR OS SCHEMAS REFERENCIADOS ---
# Agora que TransactionPublic está definido, podemos importar
# os schemas que ele usa como string (ForwardRef).
from .part_schema import InventoryItemPublic, PartPublic

# --- 5. RECONSTRUIR O MODELO ---
# Esta chamada agora encontrará 'InventoryItemPublic' e 'PartPublic'
# no escopo do módulo e resolverá as strings.
TransactionPublic.model_rebuild()