from pathlib import Path
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from config import (
    CATALOG_ID,
    PREFIJO_CARPETA_BITRIX,
    GOOGLE_CLIENT_ID,
    SECRET_KEY,
    DOMINIO_AUTORIZADO,
    USUARIOS_AUTORIZADOS,
)

from deal_utils import extraer_deal_id_desde_url
from lector_excel import leer_renglones
from validador import validar_renglones

from bitrix_client import (
    obtener_deal_por_id,
    obtener_o_crear_seccion,
    crear_producto_en_seccion,
    asociar_productos_a_negociacion,
    BitrixError,
)


BASE_DIR = Path(__file__).resolve().parent.parent
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)


app = Flask(__name__)

app.secret_key = SECRET_KEY





def construir_nombre_carpeta(deal_id, titulo_deal):
    """
    Construye el nombre de la carpeta/sección que se creará en Bitrix.

    Producción:
    82328 - Nombre de la negociación

    Con prefijo configurado:
    TEST - 82328 - Nombre de la negociación
    """

    if PREFIJO_CARPETA_BITRIX:
        return f"{PREFIJO_CARPETA_BITRIX} - {deal_id} - {titulo_deal}"

    return f"{deal_id} - {titulo_deal}"


def usuario_autorizado(email):
    """
    Valida si el usuario puede acceder a la aplicación.
    Puede autorizar por lista de emails o por dominio.
    """

    if not email:
        return False

    email = email.lower().strip()

    if USUARIOS_AUTORIZADOS:
        return email in USUARIOS_AUTORIZADOS

    if DOMINIO_AUTORIZADO:
        return email.endswith(f"@{DOMINIO_AUTORIZADO}")

    return False


def login_requerido(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "usuario" not in session:
            return redirect(url_for("login"))

        return func(*args, **kwargs)

    return wrapper


@app.route("/login")
def login():
    # Para GIS pasamos el CLIENT_ID al template
    return render_template("login.html", client_id=GOOGLE_CLIENT_ID)


@app.route("/auth/callback", methods=["POST"])
def auth_callback():
    token = request.form.get("credential")
    
    if not token:
        return render_template(
            "login.html",
            client_id=GOOGLE_CLIENT_ID,
            error="Falta credencial de Google"
        )
        
    try:
        # Verificar el token JWT (GIS)
        idinfo = id_token.verify_oauth2_token(
            token, 
            google_requests.Request(), 
            GOOGLE_CLIENT_ID
        )
        
        email = idinfo.get("email")
        nombre = idinfo.get("name")
        
        if not usuario_autorizado(email):
            session.clear()
            return render_template(
                "login.html",
                client_id=GOOGLE_CLIENT_ID,
                error=f"Usuario no autorizado: {email}"
            )
            
        session["usuario"] = {
            "email": email,
            "nombre": nombre,
        }
        
        return redirect(url_for("index"))
        
    except ValueError:
        # Token inválido
        return render_template(
            "login.html",
            client_id=GOOGLE_CLIENT_ID,
            error="El token de Google es inválido"
        )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/", methods=["GET"])
@login_requerido
def index():
    return render_template(
        "index.html",
        usuario=session.get("usuario")
    )


@app.route("/validar", methods=["POST"])
@login_requerido
def validar():
    url_negociacion = request.form.get("url_negociacion")
    archivo_excel = request.files.get("archivo_excel")

    if not url_negociacion:
        return render_template(
            "index.html",
            error="Debe ingresar la URL de la negociación de Bitrix.",
            usuario=session.get("usuario"),
        )

    if not archivo_excel:
        return render_template(
            "index.html",
            error="Debe subir una planilla Excel.",
            usuario=session.get("usuario"),
        )

    try:
        deal_id = extraer_deal_id_desde_url(url_negociacion)

        resultado_deal = obtener_deal_por_id(deal_id)
        deal = resultado_deal.get("result", {})
        titulo_deal = deal.get("TITLE")

        if not titulo_deal:
            return render_template(
                "index.html",
                error="No se pudo obtener el nombre real de la negociación.",
                usuario=session.get("usuario"),
            )

        ruta_archivo = UPLOADS_DIR / archivo_excel.filename
        archivo_excel.save(ruta_archivo)

        renglones = leer_renglones(ruta_archivo)

        es_valido, errores, advertencias = validar_renglones(renglones)

        nombre_carpeta = construir_nombre_carpeta(deal_id, titulo_deal)

        return render_template(
            "index.html",
            url_negociacion=url_negociacion,
            deal_id=deal_id,
            titulo_deal=titulo_deal,
            nombre_carpeta=nombre_carpeta,
            renglones=renglones,
            es_valido=es_valido,
            errores=errores,
            advertencias=advertencias,
            archivo_guardado=str(ruta_archivo),
            usuario=session.get("usuario"),
        )

    except ValueError as error:
        return render_template(
            "index.html",
            error=str(error),
            url_negociacion=url_negociacion,
            usuario=session.get("usuario"),
        )

    except BitrixError as error:
        return render_template(
            "index.html",
            error=f"Error Bitrix: {error}",
            url_negociacion=url_negociacion,
            usuario=session.get("usuario"),
        )

    except Exception as error:
        return render_template(
            "index.html",
            error=f"Error inesperado: {error}",
            url_negociacion=url_negociacion,
            usuario=session.get("usuario"),
        )


@app.route("/cargar", methods=["POST"])
@login_requerido
def cargar():
    url_negociacion = request.form.get("url_negociacion")
    archivo_guardado = request.form.get("archivo_guardado")

    if not url_negociacion:
        return render_template(
            "index.html",
            error="No se recibió la URL de la negociación.",
            usuario=session.get("usuario"),
        )

    if not archivo_guardado:
        return render_template(
            "index.html",
            error="No se recibió la planilla validada.",
            usuario=session.get("usuario"),
        )

    try:
        deal_id = extraer_deal_id_desde_url(url_negociacion)

        resultado_deal = obtener_deal_por_id(deal_id)
        deal = resultado_deal.get("result", {})
        titulo_deal = deal.get("TITLE")

        if not titulo_deal:
            return render_template(
                "index.html",
                error="No se pudo obtener el nombre real de la negociación.",
                usuario=session.get("usuario"),
            )

        ruta_archivo = Path(archivo_guardado)

        renglones = leer_renglones(ruta_archivo)

        es_valido, errores, advertencias = validar_renglones(renglones)

        if not es_valido:
            return render_template(
                "index.html",
                error="La planilla tiene errores. No se realizó la carga.",
                url_negociacion=url_negociacion,
                deal_id=deal_id,
                titulo_deal=titulo_deal,
                renglones=renglones,
                es_valido=es_valido,
                errores=errores,
                advertencias=advertencias,
                usuario=session.get("usuario"),
            )

        nombre_carpeta = construir_nombre_carpeta(deal_id, titulo_deal)

        resultado_seccion = obtener_o_crear_seccion(
            CATALOG_ID,
            nombre_carpeta,
            permitir_escritura=True,
        )

        section_id = resultado_seccion["id"]

        productos_creados = []

        for renglon in renglones:
            resultado_producto = crear_producto_en_seccion(
                CATALOG_ID,
                section_id,
                renglon,
            )

            productos_creados.append({
                "id": resultado_producto.get("result"),
                "nombre": renglon["nombre_producto"],
                "descripcion": renglon["descripcion_producto"],
                "cantidad": renglon["cantidad"],
                "precio": renglon["valor_unitario"],
            })

        resultado_asociacion = asociar_productos_a_negociacion(
            deal_id,
            productos_creados,
        )

        productos_asociados = len(productos_creados)

        return render_template(
            "index.html",
            url_negociacion=url_negociacion,
            deal_id=deal_id,
            titulo_deal=titulo_deal,
            nombre_carpeta=nombre_carpeta,
            renglones=renglones,
            es_valido=es_valido,
            errores=[],
            advertencias=advertencias,
            carga_realizada=True,
            accion_carpeta=resultado_seccion["accion"],
            section_id=section_id,
            productos_creados=productos_creados,
            productos_asociados=productos_asociados,
            resultado_asociacion=resultado_asociacion,
            usuario=session.get("usuario"),
        )

    except BitrixError as error:
        return render_template(
            "index.html",
            error=f"Error Bitrix durante la carga: {error}",
            url_negociacion=url_negociacion,
            usuario=session.get("usuario"),
        )

    except Exception as error:
        return render_template(
            "index.html",
            error=f"Error inesperado durante la carga: {error}",
            url_negociacion=url_negociacion,
            usuario=session.get("usuario"),
        )


if __name__ == "__main__":
    app.run(debug=True)
