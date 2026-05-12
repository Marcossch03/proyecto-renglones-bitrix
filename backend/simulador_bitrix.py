from config import CATALOG_ID, MONEDA, IVA_INCLUIDO


def construir_nombre_carpeta(deal_id, titulo_deal):
    """
    Construye el nombre de la carpeta/sección del catálogo.
    Para pruebas usamos prefijo TEST.

    Formato:
    TEST - ID_NEGOCIACION - TITULO_NEGOCIACION
    """

    deal_id = str(deal_id).strip()
    titulo_deal = str(titulo_deal).strip()

    return f"TEST100 - {deal_id} - {titulo_deal}"


def construir_payload_producto(renglon, section_id_simulado):
    """
    Construye el payload que más adelante se enviaría a Bitrix
    usando crm.product.add.
    """

    payload = {
        "CATALOG_ID": CATALOG_ID,
        "SECTION_ID": section_id_simulado,
        "NAME": renglon["nombre_producto"],
        "DESCRIPTION": renglon["descripcion_producto"],
        "DESCRIPTION_TYPE": "text",
        "PRICE": renglon["valor_unitario"],
        "CURRENCY_ID": MONEDA,
        "VAT_INCLUDED": IVA_INCLUIDO,
        "ACTIVE": "Y",

        # Por ahora mantenemos MEASURE fijo.
        # Más adelante confirmamos si corresponde 11 u otro valor.
        "MEASURE": 11,

        # Campos internos para control/log.
        # Estos todavía NO se mandarían a Bitrix salvo que tengamos campos dedicados.
        "_CONTROL": {
            "fila_excel": renglon["fila_excel"],
            "valor_total": renglon["valor_total"],
            "dotacion_4hs": renglon["dotacion_4hs"],
            "dotacion_8hs": renglon["dotacion_8hs"],
            "supervisor": renglon["supervisor"],
            "empresa_actual": renglon["empresa_actual"],
            "frecuencia": renglon["frecuencia"],
            "domicilio": renglon["domicilio"],
        }
    }

    return payload


def simular_carga(deal_id, titulo_deal, renglones):
    """
    Simula la carga completa:
    - Crear carpeta/sección con ID + nombre real de la negociación
    - Crear productos/renglones dentro de esa sección

    No relaciona automáticamente los renglones con la negociación.
    Esa relación queda manual para mayor control.
    """

    nombre_carpeta = construir_nombre_carpeta(deal_id, titulo_deal)

    # ID ficticio solo para simular la relación carpeta-productos.
    section_id_simulado = "SIMULADO_SECTION_ID"

    print("\n=== Simulación de carga en Bitrix ===")

    print("\n[SIMULACIÓN] Crear carpeta/sección en catálogo")
    print(f"CATALOG_ID: {CATALOG_ID}")
    print(f"Nombre carpeta: {nombre_carpeta}")
    print(f"SECTION_ID generado: {section_id_simulado}")

    print("\n[SIMULACIÓN] Crear productos/renglones")

    productos_simulados = []

    for renglon in renglones:
        payload = construir_payload_producto(renglon, section_id_simulado)
        productos_simulados.append(payload)

        print("\n----------------------------------------")
        print(f"Producto: {payload['NAME']}")
        print(f"Descripción: {payload['DESCRIPTION']}")
        print(f"Precio unitario: {payload['PRICE']} {payload['CURRENCY_ID']}")
        print(f"Catálogo: {payload['CATALOG_ID']}")
        print(f"Carpeta/SECTION_ID: {payload['SECTION_ID']}")
        print(f"Activo: {payload['ACTIVE']}")
        print(f"IVA incluido: {payload['VAT_INCLUDED']}")
        print(f"Unidad de medida: {payload['MEASURE']}")

        print("Datos de control no enviados todavía a Bitrix:")
        print(f"- Valor total: {payload['_CONTROL']['valor_total']}")
        print(f"- Dotación 4hs: {payload['_CONTROL']['dotacion_4hs']}")
        print(f"- Dotación 8hs: {payload['_CONTROL']['dotacion_8hs']}")
        print(f"- Supervisores: {payload['_CONTROL']['supervisor']}")
        print(f"- Empresa actual: {payload['_CONTROL']['empresa_actual']}")
        print(f"- Frecuencia: {payload['_CONTROL']['frecuencia']}")
        print(f"- Domicilio: {payload['_CONTROL']['domicilio']}")

    print("\n=== Fin de simulación ===")
    print("Carpetas a crear: 1")
    print(f"Productos a crear: {len(productos_simulados)}")

    return {
        "deal_id": deal_id,
        "titulo_deal": titulo_deal,
        "nombre_carpeta": nombre_carpeta,
        "section_id_simulado": section_id_simulado,
        "productos": productos_simulados,
    }