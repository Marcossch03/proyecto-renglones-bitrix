def validar_renglones(renglones):
    """
    Valida los renglones leídos desde la planilla.

    Devuelve:
    - es_valido: bool
    - errores: list[str]
    - advertencias: list[str]
    """

    errores = []
    advertencias = []
    nombres_vistos = set()

    if not renglones:
        errores.append("No se detectaron renglones válidos en la planilla.")
        return False, errores, advertencias

    for item in renglones:
        fila = item.get("fila_excel")
        nombre_producto = item.get("nombre_producto")
        descripcion_producto = item.get("descripcion_producto")
        valor_unitario = item.get("valor_unitario", 0)
        valor_total = item.get("valor_total", 0)
        dotacion_4hs = item.get("dotacion_4hs", 0)
        dotacion_8hs = item.get("dotacion_8hs", 0)
        supervisor = item.get("supervisor", 0)

        if nombre_producto is None or str(nombre_producto).strip() == "":
            errores.append(f"Fila {fila}: el renglón/nombre del producto está vacío.")

        if descripcion_producto is None or str(descripcion_producto).strip() == "":
            errores.append(f"Fila {fila}: la descripción del producto está vacía.")

        if valor_unitario <= 0:
            errores.append(f"Fila {fila}: el valor unitario debe ser mayor a 0.")

        if valor_total <= 0:
            advertencias.append(f"Fila {fila}: el valor total está vacío o es 0.")

        if dotacion_4hs == 0 and dotacion_8hs == 0 and supervisor == 0:
            advertencias.append(
                f"Fila {fila}: no tiene dotación ni supervisores informados."
            )

        clave_nombre = str(nombre_producto).strip().lower()

        if clave_nombre in nombres_vistos:
            advertencias.append(
                f"Fila {fila}: el renglón/producto '{nombre_producto}' está duplicado."
            )
        else:
            nombres_vistos.add(clave_nombre)

    es_valido = len(errores) == 0

    return es_valido, errores, advertencias


def mostrar_resultado_validacion(es_valido, errores, advertencias):
    print("\n=== Resultado de validación ===")

    if es_valido:
        print("Validación general: OK")
    else:
        print("Validación general: CON ERRORES")

    if errores:
        print("\nErrores:")
        for error in errores:
            print(f"- {error}")

    if advertencias:
        print("\nAdvertencias:")
        for advertencia in advertencias:
            print(f"- {advertencia}")

    if not errores and not advertencias:
        print("No se detectaron errores ni advertencias.")