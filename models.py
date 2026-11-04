from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    rol = Column(String(20), nullable=False, default="cliente")  # "admin" o "cliente"


class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(120), nullable=False)
    categoria = Column(String(50), nullable=True)
    precio = Column(Numeric(8, 2), nullable=False)

    items = relationship("PedidoItem", back_populates="producto")


class Pedido(Base):
    """Un pedido = una persona. Los productos que pide van en `items`."""
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente = Column(String(100), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL", name="fk_pedidos_usuario"), nullable=True)
    total = Column(Numeric(10, 2), nullable=False, default=0)
    estado = Column(String(20), nullable=False, default="Pendiente")
    fecha = Column(DateTime, nullable=False, default=datetime.now)

    usuario = relationship("Usuario")
    items = relationship("PedidoItem", back_populates="pedido",
                         cascade="all, delete-orphan", order_by="PedidoItem.id")

    def recalcular(self):
        """Recalcula los subtotales y el total del pedido."""
        total = Decimal("0")
        for it in self.items:
            it.subtotal = Decimal(it.precio_unitario) * it.cantidad
            total += it.subtotal
        self.total = total


class PedidoItem(Base):
    """Cada producto (con su cantidad) dentro de un pedido."""
    __tablename__ = "pedido_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id", ondelete="CASCADE", name="fk_items_pedido"), nullable=False)
    producto_id = Column(Integer, ForeignKey("productos.id", name="fk_items_producto"), nullable=False)
    cantidad = Column(Integer, nullable=False, default=1)
    precio_unitario = Column(Numeric(8, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)

    pedido = relationship("Pedido", back_populates="items")
    producto = relationship("Producto", back_populates="items")
