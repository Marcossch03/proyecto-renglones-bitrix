import requests
from config import BITRIX_WEBHOOK_URL


class BitrixError(Exception):
    pass


def validar_configuracion_bitrix():
    if not BITRIX_WEBHOOK_URL:
        raise BitrixError(
            "No se encontró BITRIX_WEBHOOK_URL. Revisá el archivo .env."
        )

    if not BITRIX_WEBHOOK_URL.endswith("/"):
        raise BitrixError(
            "BITRIX_WEBHOOK_URL debe terminar con '/'."
        )


def llamar_metodo_bitrix(metodo, parametros=None):
    """
    Ejecuta un método REST de Bitrix.

    Ejemplo:
    llamar_metodo_bitrix("crm.product.list", {"filter": {"CATALOG_ID": 23}})
    """

    validar_configuracion_bitrix()

    if parametros is None:
        parametros = {}

    url = f"{BITRIX_WEBHOOK_URL}{metodo}.json"

    try:
        respuesta = requests.post(url, json=parametros, timeout=30)
    except requests.RequestException as error:
        raise BitrixError(f"Error de conexión con Bitrix: {error}")

    if respuesta.status_code != 200:
        raise BitrixError(
            f"Bitrix devolvió HTTP {respuesta.status_code}: {respuesta.text}"
        )

    datos = respuesta.json()

    if "error" in datos:
        descripcion = datos.get("error_description", "Sin descripción")
        raise BitrixError(
            f"Error Bitrix: {datos['error']} - {descripcion}"
        )

    return datos


def probar_conexion_productos(catalog_id):
    """
    Prueba segura de lectura.
    No crea ni modifica nada.
    """

    parametros = {
        "filter": {
            "CATALOG_ID": catalog_id
        },
        "select": [
            "ID",
            "NAME",
            "CATALOG_ID",
            "SECTION_ID",
            "PRICE",
            "CURRENCY_ID"
        ]
    }

    return llamar_metodo_bitrix("crm.product.list", parametros)


def probar_conexion_secciones(catalog_id):
    """
    Prueba segura de lectura de secciones/carpetas del catálogo.
    No crea ni modifica nada.
    """

    parametros = {
        "filter": {
            "CATALOG_ID": catalog_id
        },
        "select": [
            "ID",
            "CATALOG_ID",
            "SECTION_ID",
            "NAME",
            "CODE"
        ]
    }

    return llamar_metodo_bitrix("crm.productsection.list", parametros)


def obtener_deal_por_id(deal_id):
    """
    Consulta una negociación por ID usando crm.deal.get.
    """

    parametros = {
        "id": deal_id
    }

    return llamar_metodo_bitrix("crm.deal.get", parametros)


def buscar_seccion_por_nombre(catalog_id, nombre_seccion):
    """
    Busca una carpeta/sección del catálogo por nombre.
    No modifica nada.
    """

    parametros = {
        "filter": {
            "CATALOG_ID": catalog_id,
            "NAME": nombre_seccion
        },
        "select": [
            "ID",
            "CATALOG_ID",
            "SECTION_ID",
            "NAME",
            "CODE"
        ]
    }

    return llamar_metodo_bitrix("crm.productsection.list", parametros)


def crear_seccion_producto(catalog_id, nombre_seccion, section_id_padre=None):
    """
    Crea una carpeta/sección en el catálogo de productos.
    """

    fields = {
        "CATALOG_ID": catalog_id,
        "NAME": nombre_seccion,
        "ACTIVE": "Y"
    }

    if section_id_padre is not None:
        fields["SECTION_ID"] = section_id_padre

    parametros = {
        "fields": fields
    }

    return llamar_metodo_bitrix("crm.productsection.add", parametros)


def obtener_o_crear_seccion(catalog_id, nombre_seccion, permitir_escritura=False):
    """
    Busca una sección por nombre.
    Si existe, devuelve la existente.
    Si no existe y permitir_escritura=True, la crea.
    Si no existe y permitir_escritura=False, no crea nada.
    """

    resultado_busqueda = buscar_seccion_por_nombre(catalog_id, nombre_seccion)
    secciones = resultado_busqueda.get("result", [])

    if secciones:
        seccion = secciones[0]

        return {
            "accion": "existente",
            "id": seccion.get("ID"),
            "nombre": seccion.get("NAME"),
            "detalle": seccion,
        }

    if not permitir_escritura:
        return {
            "accion": "no_creada_por_seguridad",
            "id": None,
            "nombre": nombre_seccion,
            "detalle": None,
        }

    resultado_creacion = crear_seccion_producto(catalog_id, nombre_seccion)

    return {
        "accion": "creada",
        "id": resultado_creacion.get("result"),
        "nombre": nombre_seccion,
        "detalle": resultado_creacion,
    }


def crear_producto_en_seccion(catalog_id, section_id, renglon):
    """
    Crea un producto/renglón dentro de una sección del catálogo.
    Usa crm.product.add.
    """

    descripcion = str(renglon["descripcion_producto"])
    domicilio = str(renglon.get("domicilio", ""))
    dotacion_4hs = renglon.get("dotacion_4hs", 0)
    dotacion_8hs = renglon.get("dotacion_8hs", 0)
    encargados_pliego = renglon.get("supervisor", 0)

    fields = {
        "CATALOG_ID": catalog_id,
        "SECTION_ID": section_id,

        # Datos principales del producto
        "NAME": str(renglon["nombre_producto"]),
        "DESCRIPTION": descripcion,
        "DESCRIPTION_TYPE": "text",
        "PRICE": renglon["valor_unitario"],
        "CURRENCY_ID": "ARS",
        "VAT_INCLUDED": "N",
        "ACTIVE": "Y",
        "MEASURE": 11,

        # Campos personalizados detectados en Bitrix
        "PROPERTY_97": descripcion,
        "PROPERTY_101": domicilio,
        "PROPERTY_103": dotacion_8hs,
        "PROPERTY_105": dotacion_4hs,
        "PROPERTY_124": encargados_pliego,
    }

    parametros = {
        "fields": fields
    }

    return llamar_metodo_bitrix("crm.product.add", parametros)


def asociar_productos_a_negociacion(deal_id, productos_para_asociar):
    """
    Asocia productos/renglones a una negociación de Bitrix.

    Usa crm.deal.productrows.set.

    Importante:
    Este método reemplaza los renglones actuales de la negociación
    por los enviados en ROWS.

    Para el enfoque actual del proyecto, esto es correcto porque
    se carga toda la planilla de una vez.
    """

    if not productos_para_asociar:
        raise BitrixError(
            "No hay productos para asociar a la negociación."
        )

    rows = []

    for producto in productos_para_asociar:
        product_id = producto.get("id")
        nombre = producto.get("nombre")
        precio = producto.get("precio", 0)
        cantidad = producto.get("cantidad", 0)

        if not product_id:
            raise BitrixError(
                f"Producto sin ID de Bitrix. No se puede asociar: {producto}"
            )

        if cantidad <= 0:
            raise BitrixError(
                f"Producto con cantidad inválida. No se puede asociar: {producto}"
            )

        rows.append({
            "PRODUCT_ID": int(product_id),
            "PRODUCT_NAME": str(nombre),
            "PRICE": float(precio),
            "QUANTITY": float(cantidad),
        })

    parametros = {
        "id": int(deal_id),
        "rows": rows
    }

    return llamar_metodo_bitrix("crm.deal.productrows.set", parametros)

def limpiar_productos_de_negociacion(deal_id):
    """
    Elimina todos los productos/renglones asociados a una negociación.

    No elimina productos del catálogo.
    No elimina secciones.
    Solo limpia los renglones asociados al deal.
    """

    parametros = {
        "id": int(deal_id),
        "rows": []
    }

    return llamar_metodo_bitrix("crm.deal.productrows.set", parametros)
