from config import (
    CATALOG_ID,
    MODO_SIMULACION,
    PLANILLAS_DIR,
    URL_NEGOCIACION_TEST,
    BITRIX_WEBHOOK_URL,
    PERMITIR_ESCRITURA_BITRIX,
    PERMITIR_CREAR_PRODUCTOS_BITRIX,
    CREAR_SOLO_PRIMER_PRODUCTO,
    PREFIJO_CARPETA_BITRIX,
)

from deal_utils import extraer_deal_id_desde_url
from lector_excel import leer_renglones, mostrar_vista_previa
from validador import validar_renglones, mostrar_resultado_validacion
from simulador_bitrix import simular_carga

from bitrix_client import (
    probar_conexion_productos,
    probar_conexion_secciones,
    obtener_deal_por_id,
    obtener_o_crear_seccion,
    crear_producto_en_seccion,
    BitrixError,
)


def main():
    print("=== Prueba técnica Bitrix - Carga de renglones ===")
    print(f"Catálogo objetivo: {CATALOG_ID}")
    print(f"Modo simulación: {MODO_SIMULACION}")
    print(f"Carpeta de planillas: {PLANILLAS_DIR}")
    print(f"URL negociación informada: {URL_NEGOCIACION_TEST}")
    print(f"Webhook cargado desde config.py: {'SI' if BITRIX_WEBHOOK_URL else 'NO'}")

    print("\n=== Prueba de URL de negociación ===")

    try:
        deal_id = extraer_deal_id_desde_url(URL_NEGOCIACION_TEST)
        print(f"ID extraído desde URL: {deal_id}")

        resultado_deal = obtener_deal_por_id(deal_id)
        deal = resultado_deal.get("result", {})

        titulo_deal = deal.get("TITLE")

        if not titulo_deal:
            print("No se pudo obtener el título de la negociación.")
            return

        print(f"Nombre real de la negociación: {titulo_deal}")

    except ValueError as error:
        print("Error en URL de negociación:")
        print(error)
        return

    except BitrixError as error:
        print("Error consultando crm.deal.get:")
        print(error)
        return

    archivo_excel = PLANILLAS_DIR / "planilla_test.xlsx"

    renglones = leer_renglones(archivo_excel)

    mostrar_vista_previa(renglones)

    es_valido, errores, advertencias = validar_renglones(renglones)
    mostrar_resultado_validacion(es_valido, errores, advertencias)

    if not es_valido:
        print("\nProceso detenido. Corregí la planilla antes de continuar.")
        return

    print("\nLa planilla está lista para pasar a simulación de carga.")

    if MODO_SIMULACION:
        simular_carga(deal_id, titulo_deal, renglones)
    else:
        print("\nModo simulación desactivado. No se ejecuta simulación local.")

    print("\n=== Prueba controlada de carpeta real en Bitrix ===")

    if PREFIJO_CARPETA_BITRIX:
        nombre_carpeta_real = f"{PREFIJO_CARPETA_BITRIX} - {deal_id} - {titulo_deal}"
    else:
        nombre_carpeta_real = f"{deal_id} - {titulo_deal}"

    print(f"Nombre de carpeta a buscar/crear: {nombre_carpeta_real}")
    print(f"Permitir escritura Bitrix: {PERMITIR_ESCRITURA_BITRIX}")

    try:
        resultado_seccion = obtener_o_crear_seccion(
            CATALOG_ID,
            nombre_carpeta_real,
            permitir_escritura=PERMITIR_ESCRITURA_BITRIX
        )

        print(f"Acción realizada: {resultado_seccion['accion']}")
        print(f"SECTION_ID: {resultado_seccion['id']}")
        print(f"Nombre sección: {resultado_seccion['nombre']}")

    except BitrixError as error:
        print("Error en prueba de carpeta real:")
        print(error)
        return

    print("\n=== Prueba controlada de creación de producto real ===")

    section_id_real = resultado_seccion["id"]

    if not section_id_real:
        print("No hay SECTION_ID real. No se puede crear producto.")
        return

    if CREAR_SOLO_PRIMER_PRODUCTO:
        renglones_a_crear = [renglones[0]]
    else:
        renglones_a_crear = renglones

    print(f"SECTION_ID destino: {section_id_real}")
    print(f"Productos/renglones a crear: {len(renglones_a_crear)}")
    print(f"Permitir crear productos Bitrix: {PERMITIR_CREAR_PRODUCTOS_BITRIX}")

    if not PERMITIR_CREAR_PRODUCTOS_BITRIX:
        producto_preview = renglones_a_crear[0]

        print("Creación de productos desactivada por seguridad.")
        print("Producto que se crearía:")
        print(f"- NAME: {producto_preview['nombre_producto']}")
        print(f"- DESCRIPTION / Descripción detallada: {producto_preview['descripcion_producto']}")
        print(f"- PRICE / Valor unitario: {producto_preview['valor_unitario']}")
        print(f"- PROPERTY_97 / Descripción obligatoria: {producto_preview['descripcion_producto']}")
        print(f"- PROPERTY_101 / Dirección: {producto_preview['domicilio']}")
        print(f"- PROPERTY_103 / Dotación pliego 8hs: {producto_preview['dotacion_8hs']}")
        print(f"- PROPERTY_105 / Dotación pliego 4hs: {producto_preview['dotacion_4hs']}")
        print(f"- PROPERTY_124 / Encargados por pliego: {producto_preview['supervisor']}")

    else:
        try:
            for renglon in renglones_a_crear:
                resultado_producto = crear_producto_en_seccion(
                    CATALOG_ID,
                    section_id_real,
                    renglon
                )

                print("\nProducto creado correctamente.")
                print(f"ID producto Bitrix: {resultado_producto.get('result')}")
                print(f"Nombre producto: {renglon['nombre_producto']}")
                print(f"Descripción obligatoria PROPERTY_97: {renglon['descripcion_producto']}")
                print(f"Dirección PROPERTY_101: {renglon['domicilio']}")
                print(f"Dotación pliego 8hs PROPERTY_103: {renglon['dotacion_8hs']}")
                print(f"Dotación pliego 4hs PROPERTY_105: {renglon['dotacion_4hs']}")
                print(f"Encargados por pliego PROPERTY_124: {renglon['supervisor']}")

        except BitrixError as error:
            print("Error creando producto real:")
            print(error)
            return

    print("\n=== Prueba segura de conexión con Bitrix ===")

    try:
        resultado_bitrix = probar_conexion_productos(CATALOG_ID)

        cantidad_resultados = len(resultado_bitrix.get("result", []))
        total = resultado_bitrix.get("total", "sin total informado")

        print("Conexión con Bitrix: OK")
        print(f"Productos recibidos en esta página: {cantidad_resultados}")
        print(f"Total informado por Bitrix: {total}")

    except BitrixError as error:
        print("Conexión con Bitrix: ERROR")
        print(error)

    print("\n=== Prueba segura de secciones del catálogo ===")

    try:
        resultado_secciones = probar_conexion_secciones(CATALOG_ID)

        cantidad_secciones = len(resultado_secciones.get("result", []))
        total_secciones = resultado_secciones.get("total", "sin total informado")

        print("Conexión con secciones: OK")
        print(f"Secciones recibidas en esta página: {cantidad_secciones}")
        print(f"Total de secciones informado por Bitrix: {total_secciones}")

        print("\nPrimeras secciones detectadas:")
        for seccion in resultado_secciones.get("result", [])[:5]:
            print(
                f"ID: {seccion.get('ID')} | "
                f"Nombre: {seccion.get('NAME')} | "
                f"CATALOG_ID: {seccion.get('CATALOG_ID')} | "
                f"SECTION_ID padre: {seccion.get('SECTION_ID')}"
            )

    except BitrixError as error:
        print("Conexión con secciones: ERROR")
        print(error)


if __name__ == "__main__":
    main()