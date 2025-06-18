# ====================
# IMPORTACIÓN DE MÓDULOS
# ====================

from datetime import datetime  # Para registrar la fecha de creación del personaje

# Flask: Framework web que usamos para crear la aplicación del juego
from flask import Flask, render_template, request, redirect, url_for, session

import firebase_admin
from firebase_admin import credentials, db

# ====================
# CONFIGURACIÓN INICIAL DE FLASK
# ====================

# Creamos la aplicación Flask. El parámetro __name__ le dice a Flask dónde está el archivo principal.
aplicacion = Flask(__name__)

# Inicializar Firebase
cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://lifegame-f5805-default-rtdb.firebaseio.com/"
})

# Clave secreta para poder usar sesiones (por ejemplo, mantener al usuario logueado).
# En producción se debería usar una clave secreta segura y no pública.
aplicacion.secret_key = "clave-secreta-educativa"

# ====================
# DEFINICIÓN DE PRODUCTOS DE LA TIENDA
# ====================

# Lista estática con productos disponibles para comprar en la tienda.
# Cada producto es un diccionario con nombre y precio en pesos.
TIENDA_PRODUCTOS = [
    {"nombre": "Ropa corriente", "precio": 40},
    {"nombre": "Ropa de oficina", "precio": 323},
    {"nombre": "Ropa refinada", "precio": 685},
    {"nombre": "Ropa agradable", "precio": 125},
]

# ====================
# FUNCIONES AUXILIARES
# ====================

def cargar_usuarios():
    """Carga los usuarios desde Firebase Realtime Database. Devuelve una lista."""
    ref = db.reference("/usuarios")
    datos = ref.get()
    return datos if datos else []

def guardar_usuarios():
    """Guarda la lista completa de usuarios en Firebase Realtime Database."""
    ref = db.reference("/usuarios")
    ref.set(usuarios)

def obtener_usuario_actual():
    """
    Busca en la lista de usuarios el que coincida con el nombre guardado en la sesión.
    Devuelve ese usuario o None si no está logueado.
    """
    for u in usuarios:
        if u["username"] == session.get("username"):
            return u
    return None

# ====================
# CARGA INICIAL DE USUARIOS
# ====================

# Al iniciar la aplicación se carga la base de datos de usuarios en una lista en memoria
usuarios = cargar_usuarios()
if usuarios is None:
    usuarios = []

# ====================
# RUTAS PRINCIPALES (Inicio, Registro, Login, Logout)
# ====================

@aplicacion.route("/")
def inicio():
    """
    Ruta raíz del sitio. Redirige automáticamente a la pantalla de login.
    """
    return redirect(url_for("login"))

@aplicacion.route("/registro", methods=["GET", "POST"])
def registro():
    """
    Permite a un nuevo usuario registrarse.
    Verifica que el nombre de usuario no esté repetido.
    Si se registra exitosamente, se inicia sesión y se le redirige a crear su personaje.
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Verifica si ya existe ese nombre de usuario
        for u in usuarios:
            if u["username"] == username:
                return "Ese usuario ya existe. Intenta con otro."

        # Crea un nuevo usuario con personaje vacío
        nuevo_usuario = {
            "username": username,
            "password": password,
            "personaje": None
        }

        usuarios.append(nuevo_usuario)
        guardar_usuarios()
        session["username"] = username
        return redirect(url_for("crear_personaje"))

    # Si es método GET, se muestra el formulario de registro
    return render_template("registro.html")

@aplicacion.route("/login", methods=["GET", "POST"])
def login():
    """
    Inicia sesión. Verifica las credenciales ingresadas.
    Si son correctas, redirige al perfil o al creador de personaje.
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        for u in usuarios:
            if u["username"] == username and u["password"] == password:
                session["username"] = username
                return redirect(url_for("perfil_o_crear"))

        return "Usuario o contraseña incorrectos."

    return render_template("login_inicio.html")

@aplicacion.route("/logout")
def logout():
    """
    Cierra la sesión del usuario actual y lo redirige al login.
    """
    session.clear()
    return redirect(url_for("login"))

# ====================
# GESTIÓN DE PERSONAJE (Crear, Ver, Redirigir)
# ====================

@aplicacion.route("/crear_personaje", methods=["GET", "POST"])
def crear_personaje():
    """
    Si el usuario no tiene personaje, se le permite crear uno nuevo.
    Solo puede tener un personaje.
    """
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
            "posesiones": ["ropa sucia y vieja"],
            "ropa_equipada": "ropa sucia y vieja",
            "ropa_comprada": [],
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        usuario["personaje"] = personaje
        guardar_usuarios()
        return redirect(url_for("mostrar_perfil"))

    return render_template("formulario.html")

@aplicacion.route("/perfil")
def mostrar_perfil():
    """
    Muestra el perfil del personaje del usuario actual.
    Si no tiene personaje, se le redirige a crearlo.
    """
    usuario = obtener_usuario_actual()
    if not usuario or usuario["personaje"] is None:
        return redirect(url_for("crear_personaje"))

    p = usuario["personaje"]

    return render_template("perfil.html",
                           nombre=p["nombre"],
                           dinero=p["dinero"],
                           posesiones=p.get("posesiones", []),
                           ropa_actual=p.get("ropa_equipada", p["posesiones"][0]))

@aplicacion.route("/perfil_o_crear")
def perfil_o_crear():
    """
    Redirige automáticamente al perfil si ya tiene personaje,
    o a crear uno si aún no lo tiene.
    """
    usuario = obtener_usuario_actual()
    if usuario["personaje"] is None:
        return redirect(url_for("crear_personaje"))
    return redirect(url_for("mostrar_perfil"))

@aplicacion.route("/cambiar_ropa", methods=["POST"])
def cambiar_ropa():
    if "username" not in session:
        return redirect(url_for("login"))

    usuario = obtener_usuario_actual()
    if usuario is None or usuario["personaje"] is None:
        return redirect(url_for("crear_personaje"))

    nueva_ropa = request.form.get("nueva_ropa")
    inventario = usuario["personaje"].get("posesiones", [])

    # Validamos que la ropa seleccionada esté en el inventario
    if nueva_ropa in inventario:
        usuario["personaje"]["ropa_equipada"] = nueva_ropa
        guardar_usuarios()

    return redirect(url_for("mostrar_perfil"))

# ====================
# RUTAS DE TIENDA
# ====================
@aplicacion.route("/tienda")
def mostrar_tienda():
    """
    Muestra la tienda con los productos disponibles para compra,
    muestra el dinero actual del personaje y la ropa comprada (si la hay).
    """
    # Verifica que el usuario esté logueado
    if "username" not in session:
        return redirect(url_for("login"))

    # Obtiene el usuario actual con sus datos
    usuario = obtener_usuario_actual()
    if usuario is None or usuario["personaje"] is None:
        # Si no hay personaje, redirige a crearlo antes de usar la tienda
        return redirect(url_for("crear_personaje"))

    # Obtiene el dinero disponible del personaje
    dinero = usuario["personaje"].get("dinero", 0)

    # Obtiene la lista de ropa comprada, si no existe, inicia como lista vacía
    ropa_comprada = usuario["personaje"].get("ropa_comprada", [])

    # Renderiza la plantilla tienda.html pasándole los productos, dinero y ropa
    return render_template("tienda.html",
                           productos=TIENDA_PRODUCTOS,
                           dinero=dinero,
                           ropa_comprada=ropa_comprada)

@aplicacion.route("/comprar", methods=["POST"])
def comprar():
    if "username" not in session:
        return redirect(url_for("login"))

    usuario = obtener_usuario_actual()
    if usuario is None or usuario["personaje"] is None:
        return redirect(url_for("crear_personaje"))

    producto_nombre = request.form.get("producto")
    # Buscar el producto en la lista de productos de la tienda
    producto = next((p for p in TIENDA_PRODUCTOS if p["nombre"] == producto_nombre), None)
    if producto is None:
        return "Producto no encontrado.", 400

    dinero = usuario["personaje"].get("dinero", 0)
    precio = producto["precio"]

    # Validar si hay suficiente dinero
    if dinero < precio:
        return "No tienes suficiente dinero para comprar este producto.", 400

    # Restar el dinero
    usuario["personaje"]["dinero"] = dinero - precio

    # Agregar la ropa comprada al inventario
    posesiones = usuario["personaje"].get("posesiones", [])
    posesiones.append(producto_nombre)
    usuario["personaje"]["posesiones"] = posesiones

    # Guardar los cambios
    guardar_usuarios()

    return redirect(url_for("mostrar_tienda"))

# ====================
# SISTEMA DE TRABAJO
# ====================

@aplicacion.route("/trabajo")
def mostrar_trabajo():
    usuario = obtener_usuario_actual()
    if usuario is None:
        return redirect(url_for("login"))

    # Diccionario con bonos según la ropa equipada
    bonos_por_ropa = {
        "Ropa corriente": 0.5,
        "Ropa agradable": 1,
        "Ropa de oficina": 1,
        "Ropa refinada": 2
    }

    ropa_actual = usuario["personaje"].get("ropa_equipada", "Ropa corriente")

    # Obtener bono o 0 si no hay bono para esa ropa
    bono_ropa = bonos_por_ropa.get(ropa_actual, 0)

    # Salario base fijo
    salario_base = 1

    # Salario total incluyendo bono
    salario_total = salario_base + bono_ropa

    return render_template("trabajo.html",
                           dinero=usuario["personaje"]["dinero"],
                           salario=salario_total,
                           ropa_actual=ropa_actual,
                           bono_ropa=bono_ropa)

@aplicacion.route("/trabajar", methods=["POST"])
def trabajar():
    usuario = obtener_usuario_actual()
    if not usuario:
        return redirect(url_for("login"))

    bonos_por_ropa = {
        "Ropa corriente": 0.5,
        "Ropa agradable": 1,
        "Ropa de oficina": 1,
        "Ropa refinada": 2
    }

    ropa_actual = usuario["personaje"].get("ropa_equipada", "Ropa corriente")
    bono_ropa = bonos_por_ropa.get(ropa_actual, 0)
    salario_base = 1
    salario_total = salario_base + bono_ropa

    usuario["personaje"]["dinero"] += salario_total
    guardar_usuarios()
    return redirect(url_for("mostrar_trabajo"))

# ====================
# RANKING GLOBAL
# ====================

@aplicacion.route("/ranking")
def mostrar_ranking():
    """
    Muestra una lista ordenada de personajes, del más rico al más pobre.
    Solo se incluyen usuarios que ya tienen personaje.
    """
    personajes = [u["personaje"] for u in usuarios if u["personaje"] is not None]
    lista_ordenada = sorted(personajes, key=lambda x: x["dinero"], reverse=True)
    return render_template("ranking.html", lista_personajes=lista_ordenada)


@aplicacion.route("/perfil/<nombre>")
def ver_perfil(nombre):
    """
    Muestra el perfil público de un personaje dado su nombre.
    Incluye nombre, dinero, ropa equipada y el nombre del usuario creador.
    """
    # Buscar el personaje y su usuario creador por nombre
    for usuario in usuarios:
        personaje = usuario.get("personaje")
        if personaje and personaje.get("nombre") == nombre:
            # Datos para mostrar
            datos_perfil = {
                "nombre": personaje["nombre"],
                "dinero": personaje["dinero"],
                "ropa_actual": personaje.get("ropa_equipada", "Sin ropa equipada"),
                "creado_por": usuario["username"]
            }
            return render_template("perfil_publico.html", **datos_perfil)
    
    # Si no se encuentra el personaje, mostrar error 404 o mensaje
    return f"Personaje '{nombre}' no encontrado.", 404

# ====================
# EJECUCIÓN DEL SERVIDOR
# ====================

if __name__ == "__main__":
    # Ejecuta la aplicación Flask. Acepta conexiones externas (host='0.0.0.0')
    # El puerto 8080 es común en servidores locales.
    aplicacion.run(host='0.0.0.0', port=8080, debug=True)