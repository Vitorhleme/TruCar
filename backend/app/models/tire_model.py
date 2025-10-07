from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, func, Float
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class VehicleTire(Base):
    __tablename__ = 'vehicle_tires'

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id'), nullable=False)
    part_id = Column(Integer, ForeignKey('parts.id'), nullable=False)
    position_code = Column(String(20), nullable=False)

    install_km = Column(Integer, nullable=False)
    removal_km = Column(Integer, nullable=True)
    
    install_engine_hours = Column(Float, nullable=True)
    removal_engine_hours = Column(Float, nullable=True)

    # --- CAMPO ADICIONADO ---
    # Armazena o total de KM ou Horas que o pneu rodou durante sua vida útil.
    km_run = Column(Float, nullable=True)
    # --- FIM DA ADIÇÃO ---

    is_active = Column(Boolean, default=True, nullable=False)
    installation_date = Column(DateTime(timezone=True), server_default=func.now())
    removal_date = Column(DateTime(timezone=True), nullable=True)
    
    inventory_transaction_id = Column(Integer, ForeignKey('inventory_transactions.id'), nullable=True)

    vehicle = relationship("Vehicle", back_populates="tires")
    part = relationship("Part")
    inventory_transaction = relationship("InventoryTransaction")