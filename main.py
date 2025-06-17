import json
import os
from flask import Flask, render_template, request, redirect, url_for, session

aplicacion = Flask(__name__) # Creamos la aplicacion Flask y le pasamos el nombre del archivo
aplicacion.secret_key = "clave-secreta-educativa"  # necesaria para usar sesiones

@aplicacion.route("/")
def inicio():
    return redirect(url_for("login"))

ARCHIVO_DATOS = "usuarios.json"

def cargar_usuarios():
    if os.path.exists(ARCHIVO_DATOS):
        with open(ARCHIVO_DATOS, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return []

usuarios = cargar_usuarios()

def guardar_usuarios():
    with open(ARCHIVO_DATOS, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=2, ensure_ascii=False)

@aplicacion.route("/")

# Mostrar el formulario al visitar la página principal
def mostrar_formulario():
    return render_template("formulario.html") #Toma el archivo formulario.html que está en la carpeta templatesm, lo renderiza y devuelve al navegador para que se vea como una página web

from datetime import datetime

@aplicacion.route("/crear_personaje", methods=["GET", "POST"])
def crear_personaje():
    if "username" not in session:
        return redirect(url_for("login"))
    usuario = obtener_usuario_actual()
    if usuario["personaje"] is not None:
        return redirect(url_for("mostrar_perfil"))

    if request.method == "POST":
        nombre = request.form["nombre"]
        personaje = {
            "nombre": nombre,
            "dinero": 100,
            "posesiones": "ropa común",
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        usuario["personaje"] = personaje
        guardar_usuarios()
        return redirect(url_for("mostrar_perfil"))
    return render_template("formulario.html")

@aplicacion.route("/perfil")
def mostrar_perfil():
        usuario = obtener_usuario_actual()
        if not usuario or usuario["personaje"] is None:
            return redirect(url_for("crear_personaje"))
        p = usuario["personaje"]
        return render_template("perfil.html",
                               nombre=p["nombre"],
                               dinero=p["dinero"],
                               posesiones=p["posesiones"])

@aplicacion.route("/trabajo")
def mostrar_trabajo():
    usuario = obtener_usuario_actual()
    if usuario is None:
            return redirect(url_for("login"))
    return render_template("trabajo.html", dinero=usuario["personaje"]["dinero"])


@aplicacion.route("/trabajar", methods=["POST"])
def trabajar():
    usuario = obtener_usuario_actual()
    if not usuario: return redirect(url_for("login"))
    usuario["personaje"]["dinero"] += 1
    guardar_usuarios()
    return redirect(url_for("mostrar_trabajo"))


@aplicacion.route("/ranking")
def mostrar_ranking():
    personajes = [u["personaje"] for u in usuarios if u["personaje"] is not None]
    lista_ordenada = sorted(personajes, key=lambda x: x["dinero"], reverse=True)
    return render_template("ranking.html", lista_personajes=lista_ordenada)


@aplicacion.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        # Verificar si ya existe ese usuario
        for u in usuarios:
            if u["username"] == username:
                return "Ese usuario ya existe. Intenta con otro."
        nuevo_usuario = {
            "username": username,
            "password": password,
            "personaje": None
        }
        usuarios.append(nuevo_usuario)
        guardar_usuarios()
        session["username"] = username
        return redirect(url_for("crear_personaje"))
    return render_template("registro.html")

@aplicacion.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        for u in usuarios:
            if u["username"] == username and u["password"] == password:
                session["username"] = username
                return redirect(url_for("perfil_o_crear"))
        return "Usuario o contraseña incorrectos."
    return render_template("login.html")

def obtener_usuario_actual():
    for u in usuarios:
        if u["username"] == session.get("username"):
            return u
    return None

@aplicacion.route("/perfil_o_crear")
def perfil_o_crear():
    usuario = obtener_usuario_actual()
    if usuario["personaje"] is None:
        return redirect(url_for("crear_personaje"))
    return redirect(url_for("mostrar_perfil"))

@aplicacion.route("/logout")
def logout():
    session.clear()  # borra todo lo que estaba en la sesión
    return redirect(url_for("login"))  # redirige a login

from flask import Flask
from threading import Thread

def run():
    aplicacion.run(host='0.0.0.0', port=8080)

def mantener_vivo():
    t = Thread(target=run)
    t.start()

mantener_vivo()