import os
from pathlib import Path
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
BASE_DIR = BACKEND_DIR.parent

ENV_PATH = BACKEND_DIR / ".env"

load_dotenv(ENV_PATH, override=True, encoding="utf-8-sig")

PLANILLAS_DIR = BASE_DIR / "planillas"
LOGS_DIR = BASE_DIR / "logs"

CATALOG_ID = 23
MONEDA = "ARS"
IVA_INCLUIDO = "N"

# Producción:
# Dejar vacío para que las carpetas se creen así:
# 82328 - Nombre real de la negociación
PREFIJO_CARPETA_BITRIX = ""

MODO_SIMULACION = True

PERMITIR_ESCRITURA_BITRIX = False
PERMITIR_CREAR_PRODUCTOS_BITRIX = False
CREAR_SOLO_PRIMER_PRODUCTO = False

# Uso local/técnico de main.py.
# En la web, este valor lo escribe el usuario desde el formulario.
URL_NEGOCIACION_TEST = "https://sistemacrm.bitrix24.es/crm/deal/details/82328/"

BITRIX_WEBHOOK_URL = os.getenv("BITRIX_WEBHOOK_URL")

# Fallback manual por si dotenv falla
if not BITRIX_WEBHOOK_URL and ENV_PATH.exists():
    contenido = ENV_PATH.read_text(encoding="utf-8-sig")

    for linea in contenido.splitlines():
        linea = linea.strip()

        if linea.startswith("BITRIX_WEBHOOK_URL="):
            BITRIX_WEBHOOK_URL = linea.split("=", 1)[1].strip()
            break

# Configuración de Oauth
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
SECRET_KEY = os.getenv("SECRET_KEY", "clave-temporal-cambiar-en-produccion")

DOMINIO_AUTORIZADO = os.getenv("DOMINIO_AUTORIZADO", "").strip().lower()

USUARIOS_AUTORIZADOS = [
    email.strip().lower()
    for email in os.getenv("USUARIOS_AUTORIZADOS", "").split(",")
    if email.strip()
]
