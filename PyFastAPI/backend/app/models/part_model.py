import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum as SAEnum, Float, DateTime, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum
from app.db.base_class import Base
from typing import Optional, List

# --- Enum de Categoria (Sem alteração) ---
class PartCategory(str, enum.Enum):
    PECA = "Peça"
    FLUIDO = "Fluído"
    CONSUMIVEL = "Consumível"
    PNEU = "Pneu"
    OUTRO = "Outro"

#
# --- MODELO PART (AGORA É UM "TEMPLATE") ---
#
class Part(Base):
    __tablename__ = "parts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    category = Column(SAEnum(PartCategory), nullable=False, default=PartCategory.PECA)
    value = Column(Float, nullable=True) 
    invoice_url = Column(String(512), nullable=True)
    serial_number = Column(String(100), nullable=True, index=True, unique=True)
    minimum_stock: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    part_number = Column(String(100), nullable=True, index=True)
    brand = Column(String(100), nullable=True)
    
    # --- COLUNA DE ESTOQUE REMOVIDA ---
    # stock = Column(Integer, nullable=False, default=0) # <-- REMOVIDO

    location = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    photo_url = Column(String(512), nullable=True)
    lifespan_km = Column(Integer, nullable=True) 

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    organization = relationship("Organization")

    # --- RELAÇÕES ATUALIZADAS ---
    # Part não tem mais transações diretas, os Itens têm
    transactions = relationship("InventoryTransaction", back_populates="part_template") 
    
    # Nova relação: Part (template) tem muitos Itens (estoque)
    items = relationship("InventoryItem", back_populates="part", cascade="all, delete-orphan")


#
# --- NOVO MODELO: INVENTORY ITEM (ESTE É O ESTOQUE) ---
#
class InventoryItemStatus(str, enum.Enum):
    DISPONIVEL = "Disponível"
    EM_USO = "Em Uso"
    FIM_DE_VIDA = "Fim de Vida"

class InventoryItem(Base):
    __tablename__ = "inventory_items"

    # Este 'id' é o "código" 1, 2, 3... que você pediu
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    status: Mapped[InventoryItemStatus] = mapped_column(SAEnum(InventoryItemStatus), nullable=False, default=InventoryItemStatus.DISPONIVEL, index=True)
    
    part_id: Mapped[int] = mapped_column(Integer, ForeignKey("parts.id"), nullable=False)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    installed_on_vehicle_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("vehicles.id"), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    installed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relações
    part: Mapped["Part"] = relationship("Part", back_populates="items")
    organization: Mapped["Organization"] = relationship("Organization")
    installed_on_vehicle: Mapped[Optional["Vehicle"]] = relationship("Vehicle")
    
    # Cada item tem seu próprio histórico de transações
    transactions: Mapped[List["InventoryTransaction"]] = relationship("InventoryTransaction", back_populates="item", cascade="all, delete-orphan")