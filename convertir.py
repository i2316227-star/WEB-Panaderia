"""
convertir.py  -  Convierte la plantilla HTML estática de D'VIDA en plantillas Flask.
Ejecútalo UNA sola vez, dentro de la carpeta del proyecto:   python convertir.py
"""
import re
import shutil
from pathlib import Path

RAIZ = Path(__file__).parent
TEMPLATES = RAIZ / "templates"
STATIC = RAIZ / "static"

# archivo .html  ->  nombre de la función (endpoint) en app.py
RUTAS = {
    "index.html": "inicio",
    "orders.html": "pedidos",
    "docs.html": "documentos",
    "account.html": "cuenta",
    "settings.html": "configuracion",
    "notifications.html": "notificaciones",
    "help.html": "ayuda",
    "charts.html": "graficos",
    "login.html": "login",
    "signup.html": "registro",
    "reset-password.html": "recuperar",
    "404.html": "inicio",
}


BLOQUE_PEDIDOS = """
<div class="d-flex justify-content-between align-items-center mb-3">
  <form method="GET" class="row gx-1">
    <input type="hidden" name="estado" value="{{ estado }}">
    <div class="col-auto"><input type="text" name="q" value="{{ q }}" class="form-control" placeholder="Buscar cliente o producto"></div>
    <div class="col-auto"><button class="btn app-btn-secondary" type="submit">Buscar</button></div>
  </form>
  <button class="btn app-btn-primary" data-bs-toggle="modal" data-bs-target="#modalPedido">+ Nuevo pedido</button>
</div>

{% with mensajes = get_flashed_messages(with_categories=true) %}
  {% for cat, msg in mensajes %}<div class="alert alert-{{ cat }}">{{ msg }}</div>{% endfor %}
{% endwith %}

<nav class="orders-table-tab app-nav-tabs nav shadow-sm flex-column flex-sm-row mb-4">
  {% for val, label in [('', 'Todos'), ('Pagado', 'Pagado'), ('Pendiente', 'Pendiente'), ('Cancelado', 'Cancelado')] %}
  <a class="flex-sm-fill text-sm-center nav-link {{ 'active' if estado == val }}"
     href="{{ url_for('pedidos', estado=val, q=q) }}">{{ label }}</a>
  {% endfor %}
</nav>

<div class="app-card app-card-orders-table shadow-sm mb-5">
  <div class="app-card-body">
    <div class="table-responsive">
      <table class="table app-table-hover mb-0 text-left">
        <thead><tr>
          <th class="cell">Pedido</th><th class="cell">Producto</th><th class="cell">Cliente</th>
          <th class="cell">Fecha</th><th class="cell">Estado</th><th class="cell">Total</th><th class="cell"></th>
        </tr></thead>
        <tbody>
        {% for p in pedidos %}
          <tr>
            <td class="cell">#{{ p.id }}</td>
            <td class="cell"><span class="truncate">{{ p.cantidad }} x {{ p.producto.nombre }}</span></td>
            <td class="cell">{{ p.cliente }}</td>
            <td class="cell"><span>{{ p.fecha.strftime('%d/%m/%Y') }}</span><span class="note">{{ p.fecha.strftime('%I:%M %p') }}</span></td>
            <td class="cell">
              <form method="POST" action="{{ url_for('pedido_estado', id=p.id) }}">
                <select name="estado" class="form-select form-select-sm w-auto" onchange="this.form.submit()">
                  {% for e in estados %}<option value="{{ e }}" {{ 'selected' if p.estado == e }}>{{ e }}</option>{% endfor %}
                </select>
              </form>
            </td>
            <td class="cell">S/ {{ "%.2f"|format(p.total) }}</td>
            <td class="cell">
              <form method="POST" action="{{ url_for('pedido_eliminar', id=p.id) }}"
                    onsubmit="return confirm('¿Eliminar este pedido?');">
                <button class="btn-sm app-btn-secondary" type="submit">Eliminar</button>
              </form>
            </td>
          </tr>
        {% else %}
          <tr><td class="cell" colspan="7">No hay pedidos para mostrar.</td></tr>
        {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>

<div class="modal fade" id="modalPedido" tabindex="-1">
  <div class="modal-dialog"><form class="modal-content" method="POST" action="{{ url_for('pedido_nuevo') }}">
    <div class="modal-header"><h5 class="modal-title">Nuevo pedido</h5>
      <button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
    <div class="modal-body">
      <div class="mb-3"><label class="form-label">Cliente</label>
        <input type="text" name="cliente" class="form-control" required></div>
      <div class="mb-3"><label class="form-label">Producto</label>
        <select name="producto_id" class="form-select" required>
          {% for pr in productos %}<option value="{{ pr.id }}">{{ pr.nombre }} - S/ {{ "%.2f"|format(pr.precio) }}</option>{% endfor %}
        </select></div>
      <div class="mb-3"><label class="form-label">Cantidad</label>
        <input type="number" name="cantidad" class="form-control" min="1" value="1" required></div>
    </div>
    <div class="modal-footer">
      <button type="button" class="btn app-btn-secondary" data-bs-dismiss="modal">Cancelar</button>
      <button type="submit" class="btn app-btn-primary">Guardar pedido</button>
    </div>
  </form></div>
</div>
"""


def hacer_pedidos_dinamico(t):
    """Reemplaza las pestañas + tablas de ejemplo por la tabla dinámica."""
    ini = t.index('<nav id="orders-table-tab"')
    fin_marca = "<!--//tab-content-->"
    fin = t.index(fin_marca) + len(fin_marca)
    # quitar también el cierre del div tab-content que precede al comentario
    return t[:ini] + BLOQUE_PEDIDOS + t[fin:]


TEMPLATES.mkdir(exist_ok=True)
STATIC.mkdir(exist_ok=True)

# 1) Mover assets y favicon a /static
if (RAIZ / "assets").exists():
    shutil.move(str(RAIZ / "assets"), str(STATIC / "assets"))
if (RAIZ / "favicon.ico").exists():
    shutil.move(str(RAIZ / "favicon.ico"), str(STATIC / "favicon.ico"))

# 2) Reescribir cada HTML y moverlo a /templates
for html in RAIZ.glob("*.html"):
    t = html.read_text(encoding="utf-8")

    # assets/...  y favicon.ico  ->  url_for('static', ...)
    t = re.sub(r'(href|src)="assets/([^"]*)"',
               r'''\1="{{ url_for('static', filename='assets/\2') }}"''', t)
    t = t.replace('href="favicon.ico"',
                  '''href="{{ url_for('static', filename='favicon.ico') }}"''')

    # enlaces entre páginas  ->  url_for('funcion')
    for archivo, endpoint in RUTAS.items():
        t = t.replace(f'href="{archivo}"', f'''href="{{{{ url_for('{endpoint}') }}}}"''')

    # en páginas internas el enlace a login.html es "Cerrar sesión" -> /logout
    if html.name not in ("login.html", "signup.html", "reset-password.html", "404.html"):
        t = t.replace("url_for('login')", "url_for('logout')")

    # formularios de login / registro / recuperar: método POST
    if html.name in ("login.html", "signup.html", "reset-password.html"):
        t = re.sub(r'<form class="auth-form([^"]*)">',
                   r'<form class="auth-form\1" method="POST">', t, count=1)

    # mensajes flash (errores/avisos) justo antes del primer <form class="auth-form
    if html.name in ("login.html", "signup.html", "reset-password.html"):
        flash = ("{% with mensajes = get_flashed_messages(with_categories=true) %}"
                 "{% for cat, msg in mensajes %}"
                 '<div class="alert alert-{{ cat }}" role="alert">{{ msg }}</div>'
                 "{% endfor %}{% endwith %}\n")
        t = t.replace('<form class="auth-form', flash + '<form class="auth-form', 1)

    if html.name == "orders.html":
        t = hacer_pedidos_dinamico(t)
    if html.name == "index.html":
        t = t.replace('<div class="stats-figure">S/ 12,628</div>',
                      '<div class="stats-figure">S/ {{ "%.2f"|format(ventas_total) }}</div>')
        t = t.replace('<div class="stats-figure">23</div>',
                      '<div class="stats-figure">{{ total_pedidos }}</div>')

    (TEMPLATES / html.name).write_text(t, encoding="utf-8")
    html.unlink()
    print("OK ", html.name)

print("\nListo. Revisa las carpetas 'templates' y 'static'.")
