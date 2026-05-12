from pathlib import Path
import os
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
ENV_PATH = BACKEND_DIR / ".env"

print("Existe .env:", ENV_PATH.exists())

contenido = ENV_PATH.read_text(encoding="utf-8-sig")

print("Primeros 30 caracteres del archivo:")
print(repr(contenido[:30]))

print("\nLíneas detectadas:")
for linea in contenido.splitlines():
    if "BITRIX_WEBHOOK_URL" in linea:
        print("La línea contiene BITRIX_WEBHOOK_URL: SI")
        print("La línea empieza exactamente con BITRIX_WEBHOOK_URL=:", linea.startswith("BITRIX_WEBHOOK_URL="))
        print("Tiene espacios antes:", linea.startswith(" "))
        print("Tiene espacios después del nombre:", "BITRIX_WEBHOOK_URL =" in linea)
    else:
        print("Línea no reconocida:", repr(linea))

load_dotenv(ENV_PATH, override=True, encoding="utf-8-sig")

webhook = os.getenv("BITRIX_WEBHOOK_URL")

print("\nResultado:")
print("BITRIX_WEBHOOK_URL cargado:", "SI" if webhook else "NO")