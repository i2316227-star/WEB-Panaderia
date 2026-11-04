from datetime import datetime
from decimal import Decimal

from flask import Flask, render_template, request, redirect, url_for, flash, session
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from werkzeug.security import generate_password_hash, check_password_hash

import config
from auth import login_required, admin_required
from database import get_session, remove_session
from models import Usuario, Producto, Pedido, PedidoItem

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

ESTADOS = ["Pagado", "Pendiente", "Cancelado"]


@app.teardown_appcontext
def cerrar_sesion_db(exception=None):
    remove_session(exception)


@app.errorhandler(404)
def no_encontrado(e):
    return render_template("404.html"), 404


# ---------------------------------------------------------------- autenticación
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["signin-email"].strip()
        password = request.form["signin-password"]

        db = get_session()
        usuario = db.query(Usuario).filter_by(email=email).first()
        if usuario and check_password_hash(usuario.password, password):
            session.clear()
            session["user_id"] = usuario.id
            session["nombre"] = usuario.nombre
            session["rol"] = usuario.rol
            if usuario.rol == "admin":
                return redirect(url_for("inicio"))
            return redirect(url_for("tienda"))
        flash("Correo o contraseña incorrectos.", "danger")
    return render_template("login.html")


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form["signup-name"].strip()
        email = request.form["signup-email"].strip()
        password = request.form["signup-password"]

        if len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "danger")
            return render_template("signup.html")

        db = get_session()
        try:
            db.add(Usuario(nombre=nombre, email=email,
                           password=generate_password_hash(password),
                           rol="cliente"))
            db.commit()
            flash("Cuenta creada. Ya puedes iniciar sesión.", "success")
            return redirect(url_for("login"))
        except IntegrityError:
            db.rollback()
            flash("Ya existe una cuenta con ese correo.", "danger")
    return render_template("signup.html")


@app.route("/recuperar", methods=["GET", "POST"])
def recuperar():
    if request.method == "POST":
        flash("Función pendiente: por ahora pide el cambio al administrador.", "info")
    return render_template("reset-password.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("login"))


# ---------------------------------------------------------------- panel
@app.route("/")
@admin_required
def inicio():
    db = get_session()
    ventas_total = (
        db.query(func.coalesce(func.sum(Pedido.total), 0))
        .filter(Pedido.estado == "Pagado")
        .scalar()
    )
    total_pedidos = db.query(func.count(Pedido.id)).scalar()
    return render_template("index.html",
                           ventas_total=Decimal(ventas_total),
                           total_pedidos=total_pedidos)


# ---------------------------------------------------------------- ayudantes de pedidos
def _pedido_abierto(db, usuario_id, cliente):
    """El pedido 'Pendiente' de esa persona, si ya tiene uno."""
    consulta = db.query(Pedido).filter(Pedido.estado == "Pendiente")
    if usuario_id:
        consulta = consulta.filter(Pedido.usuario_id == usuario_id)
    else:
        consulta = consulta.filter(Pedido.usuario_id.is_(None),
                                   func.lower(Pedido.cliente) == cliente.lower())
    return consulta.order_by(Pedido.fecha.desc()).first()


def _agregar_al_pedido(db, producto, cantidad, cliente, usuario_id=None):
    """Suma el producto al pedido pendiente de la persona (o crea uno si no tiene)."""
    pedido = _pedido_abierto(db, usuario_id, cliente)
    if pedido is None:
        pedido = Pedido(cliente=cliente, usuario_id=usuario_id, estado="Pendiente", total=Decimal("0"))
        db.add(pedido)

    item = next((i for i in pedido.items if i.producto_id == producto.id), None)
    if item:
        item.cantidad = min(item.cantidad + cantidad, 500)
        item.precio_unitario = producto.precio
    else:
        pedido.items.append(PedidoItem(producto_id=producto.id, cantidad=cantidad,
                                       precio_unitario=producto.precio, subtotal=Decimal("0")))
    pedido.recalcular()
    pedido.fecha = datetime.now()
    db.commit()
    return pedido


# ---------------------------------------------------------------- pedidos (admin)
@app.route("/pedidos")
@admin_required
def pedidos():
    estado = request.args.get("estado", "")
    q = request.args.get("q", "").strip()

    db = get_session()
    consulta = db.query(Pedido).options(joinedload(Pedido.items).joinedload(PedidoItem.producto))
    if estado in ESTADOS:
        consulta = consulta.filter(Pedido.estado == estado)
    if q:
        like = f"%{q}%"
        consulta = consulta.filter(or_(
            Pedido.cliente.like(like),
            Pedido.items.any(PedidoItem.producto.has(Producto.nombre.like(like))),
        ))
    filas = consulta.order_by(Pedido.fecha.desc()).all()
    productos = db.query(Producto).order_by(Producto.nombre).all()

    return render_template("orders.html", pedidos=filas, productos=productos,
                           estados=ESTADOS, estado=estado, q=q)


@app.route("/pedidos/nuevo", methods=["POST"])
@admin_required
def pedido_nuevo():
    cliente = request.form["cliente"].strip()
    producto_id = int(request.form["producto_id"])
    cantidad = min(max(1, int(request.form.get("cantidad", 1))), 500)

    db = get_session()
    producto = db.get(Producto, producto_id)
    if not producto or not cliente:
        flash("Datos del pedido inválidos.", "danger")
        return redirect(url_for("pedidos"))

    # si el nombre es de un cliente registrado, el producto se suma a SU pedido
    usuario = (db.query(Usuario)
               .filter(func.lower(Usuario.nombre) == cliente.lower(), Usuario.rol == "cliente")
               .first())
    pedido = _agregar_al_pedido(db, producto, cantidad,
                                usuario.nombre if usuario else cliente,
                                usuario.id if usuario else None)
    flash(f"Pedido #{pedido.id} de {pedido.cliente}: se agregó {cantidad} x {producto.nombre}.", "success")
    return redirect(url_for("pedidos"))


@app.route("/pedidos/<int:id>/estado", methods=["POST"])
@admin_required
def pedido_estado(id):
    nuevo = request.form.get("estado")
    db = get_session()
    pedido = db.get(Pedido, id)
    if pedido and nuevo in ESTADOS:
        pedido.estado = nuevo
        db.commit()
        flash(f"Pedido #{id} marcado como {nuevo}.", "success")
    return redirect(request.referrer or url_for("pedidos"))


@app.route("/pedidos/<int:id>/eliminar", methods=["POST"])
@admin_required
def pedido_eliminar(id):
    db = get_session()
    pedido = db.get(Pedido, id)
    if pedido:
        db.delete(pedido)
        db.commit()
        flash("Pedido eliminado.", "success")
    return redirect(url_for("pedidos"))


# ---------------------------------------------------------------- tienda (cliente)
@app.route("/tienda")
@login_required
def tienda():
    db = get_session()
    productos = db.query(Producto).order_by(Producto.categoria, Producto.nombre).all()
    mis_pedidos = (
        db.query(Pedido)
        .options(joinedload(Pedido.items).joinedload(PedidoItem.producto))
        .filter(Pedido.usuario_id == session["user_id"])
        .order_by(Pedido.fecha.desc())
        .all()
    )
    return render_template("tienda.html", productos=productos, mis_pedidos=mis_pedidos)


@app.route("/tienda/pedir", methods=["POST"])
@login_required
def tienda_pedir():
    try:
        producto_id = int(request.form["producto_id"])
        cantidad = int(request.form.get("cantidad", 1))
    except (KeyError, ValueError):
        flash("Datos del pedido inválidos.", "danger")
        return redirect(url_for("tienda"))
    cantidad = min(max(1, cantidad), 500)

    db = get_session()
    producto = db.get(Producto, producto_id)
    if not producto:
        flash("Ese producto ya no existe.", "danger")
        return redirect(url_for("tienda"))

    pedido = _agregar_al_pedido(db, producto, cantidad, session["nombre"], session["user_id"])
    flash(f"Agregado a tu pedido #{pedido.id}: {cantidad} x {producto.nombre}.", "success")
    return redirect(url_for("tienda"))


@app.route("/tienda/cancelar/<int:id>", methods=["POST"])
@login_required
def tienda_cancelar(id):
    db = get_session()
    pedido = db.get(Pedido, id)
    # solo puede cancelar SU pedido y mientras esté pendiente
    if pedido and pedido.usuario_id == session["user_id"] and pedido.estado == "Pendiente":
        pedido.estado = "Cancelado"
        db.commit()
        flash(f"Pedido #{id} cancelado.", "info")
    else:
        flash("No se puede cancelar ese pedido.", "danger")
    return redirect(url_for("tienda"))


# ------------------------------------------------ páginas aún estáticas del tema
def _pagina(nombre_endpoint, plantilla, ruta):
    @admin_required
    def vista():
        return render_template(plantilla)
    vista.__name__ = nombre_endpoint
    app.add_url_rule(ruta, nombre_endpoint, vista)


_pagina("documentos", "docs.html", "/documentos")
_pagina("cuenta", "account.html", "/cuenta")
_pagina("configuracion", "settings.html", "/configuracion")
_pagina("notificaciones", "notifications.html", "/notificaciones")
_pagina("ayuda", "help.html", "/ayuda")
_pagina("graficos", "charts.html", "/graficos")


if __name__ == "__main__":
    app.run(debug=True)
