"""
migrar_pedidos.py  -  Pasa tus pedidos al formato nuevo: UN pedido por persona.

Úsalo UNA sola vez, con Flask apagado, dentro de la carpeta del proyecto:

    python migrar_pedidos.py

Qué hace:
  1. Renombra la tabla vieja `pedidos` como `pedidos_respaldo` (queda de copia de seguridad).
  2. Crea las tablas nuevas `pedidos` y `pedido_items`.
  3. Junta los pedidos viejos de cada persona que tengan el MISMO estado en un solo pedido
     (Pagado con Pagado, Pendiente con Pendiente, Cancelado con Cancelado), sumando
     las cantidades cuando el producto se repite.
  4. Comprueba que el dinero total no haya cambiado.

Si algo falla, deja todo como estaba.
"""
from collections import OrderedDict
from datetime import datetime
from decimal import Decimal

from sqlalchemy import inspect, text

from database import engine, Base
import models  # noqa: F401  (registra las tablas)
from models import Pedido, PedidoItem

DOS = Decimal("0.01")


def _fecha(valor):
    """MySQL entrega datetime; por si acaso, también acepta texto."""
    return datetime.fromisoformat(valor) if isinstance(valor, str) else valor


def main():
    insp = inspect(engine)
    tablas = insp.get_table_names()

    if "pedido_items" in tablas:
        print("Ya estaba migrado (existe la tabla pedido_items). No hice nada.")
        return
    if "pedidos" not in tablas or "producto_id" not in [c["name"] for c in insp.get_columns("pedidos")]:
        print("La tabla `pedidos` no tiene el formato viejo. No hice nada.")
        return
    if "pedidos_respaldo" in tablas:
        print("Ya existe `pedidos_respaldo`. Revísala o bórrala antes de volver a intentar.")
        return

    print("1/4  Guardando copia de la tabla vieja como `pedidos_respaldo`...")
    with engine.begin() as con:
        con.execute(text("ALTER TABLE pedidos RENAME TO pedidos_respaldo"))

    try:
        print("2/4  Creando tablas nuevas...")
        Base.metadata.create_all(engine)

        with engine.begin() as con:
            filas = con.execute(text(
                "SELECT id, cliente, usuario_id, producto_id, cantidad, total, estado, fecha "
                "FROM pedidos_respaldo ORDER BY fecha, id")).mappings().all()
            total_viejo = sum((Decimal(str(f["total"])) for f in filas), Decimal("0"))

            print(f"3/4  Agrupando {len(filas)} pedidos viejos...")
            grupos = OrderedDict()
            for f in filas:
                persona = ("u", f["usuario_id"]) if f["usuario_id"] else ("c", f["cliente"].strip().lower())
                grupos.setdefault((persona, f["estado"]), []).append(f)

            tabla_pedidos = Pedido.__table__
            tabla_items = PedidoItem.__table__
            for (_, estado), lista in grupos.items():
                productos = OrderedDict()   # producto_id -> [cantidad, subtotal]
                for f in lista:
                    acum = productos.setdefault(f["producto_id"], [0, Decimal("0")])
                    acum[0] += f["cantidad"]
                    acum[1] += Decimal(str(f["total"]))
                total = sum((s for _, s in productos.values()), Decimal("0"))
                nuevo_id = con.execute(tabla_pedidos.insert().values(
                    cliente=lista[0]["cliente"], usuario_id=lista[0]["usuario_id"],
                    total=total, estado=estado, fecha=max(_fecha(f["fecha"]) for f in lista),
                )).inserted_primary_key[0]
                for producto_id, (cantidad, subtotal) in productos.items():
                    con.execute(tabla_items.insert().values(
                        pedido_id=nuevo_id, producto_id=producto_id, cantidad=cantidad,
                        precio_unitario=(subtotal / cantidad).quantize(DOS), subtotal=subtotal,
                    ))

            total_nuevo = Decimal(str(con.execute(text("SELECT COALESCE(SUM(total), 0) FROM pedidos")).scalar()))
            if total_nuevo != total_viejo:
                raise RuntimeError(f"Los totales no coinciden: antes S/ {total_viejo}, ahora S/ {total_nuevo}")

        print(f"4/4  Listo. {len(filas)} pedidos viejos -> {len(grupos)} pedidos nuevos. "
              f"Total sin cambios: S/ {total_nuevo}")
        print("     Cuando verifiques que todo está bien, puedes borrar la tabla `pedidos_respaldo`.")

    except Exception as e:
        print(f"\nERROR: {e}\nDeshaciendo los cambios...")
        with engine.begin() as con:
            con.execute(text("DROP TABLE IF EXISTS pedido_items"))
            con.execute(text("DROP TABLE IF EXISTS pedidos"))
            con.execute(text("ALTER TABLE pedidos_respaldo RENAME TO pedidos"))
        print("Todo quedó como antes. Avísame el error y lo revisamos.")
        raise


if __name__ == "__main__":
    main()
