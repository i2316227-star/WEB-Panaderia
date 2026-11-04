from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Inicia sesión para continuar.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Inicia sesión para continuar.", "warning")
            return redirect(url_for("login"))
        if session.get("rol") != "admin":
            return redirect(url_for("tienda"))
        return f(*args, **kwargs)
    return wrapper
