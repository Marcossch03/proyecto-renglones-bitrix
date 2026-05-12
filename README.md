# Carga automática de renglones en Bitrix

Aplicación web interna para cargar renglones/productos en el Catálogo de productos CRM de Bitrix a partir de una planilla Excel de cotización.

## Funcionalidad principal

La aplicación permite:

1. Pegar la URL de una negociación de Bitrix.
2. Extraer automáticamente el ID de la negociación.
3. Consultar el nombre real de la negociación mediante `crm.deal.get`.
4. Subir una planilla Excel de cotización.
5. Leer y validar los renglones de la planilla.
6. Crear o reutilizar una carpeta/sección en el Catálogo de productos CRM.
7. Cargar los renglones como productos dentro de esa carpeta.
8. Mostrar confirmación visual de carga exitosa.

La carpeta se crea con el siguiente formato:

```text
ID_NEGOCIACION - NOMBRE_REAL_NEGOCIACION
