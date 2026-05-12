import re


def extraer_deal_id_desde_url(url):
    """
    Extrae el ID de una negociación desde una URL de Bitrix.

    Ejemplo:
    https://sistemacrm.bitrix24.es/crm/deal/details/82328/
    devuelve:
    82328
    """

    url = str(url).strip()

    patron = r"/crm/deal/details/(\d+)/?"
    coincidencia = re.search(patron, url)

    if not coincidencia:
        raise ValueError(
            "No se pudo extraer el ID de la negociación desde la URL."
        )

    return int(coincidencia.group(1))