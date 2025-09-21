import os, json, time, requests
from tuya_connector import (
    TuyaOpenAPI,
    TuyaOpenMQ,
)

# === Configuración desde variables de entorno ===
ACCESS_ID     = os.environ["TUYA_ACCESS_ID"]
ACCESS_SECRET = os.environ["TUYA_ACCESS_SECRET"]
ENDPOINT      = os.environ.get("TUYA_ENDPOINT", "https://openapi.tuyaus.com")  # América
TARGET_DEVICE = os.environ["TARGET_DEVICE_ID"]   # ej: eb9ac32d80d90cb0b0o6cd
TARGET_DP     = os.environ.get("TARGET_DP_CODE", "switch_1")
VM_URL        = os.environ["VOICEMONKEY_URL"]    # tu link de Voice Monkey

# === Conexión al OpenAPI ===
openapi = TuyaOpenAPI(ENDPOINT, ACCESS_ID, ACCESS_SECRET)
openapi.connect()

# === Callback de mensajes MQ ===
def on_message(msg):
    try:
        data = json.loads(msg)
    except Exception:
        return

    biz = (data.get("bizCode")
           or data.get("header", {}).get("bizCode")
           or data.get("type")
           or "").lower()
    if "deviceproperty" not in biz:
        return

    dev_id = (data.get("devId")
              or data.get("deviceId")
              or data.get("data", {}).get("devId"))
    if dev_id != TARGET_DEVICE:
        return

    payload = data.get("data") or {}
    status_list = payload.get("status") or []
    props = payload.get("properties") or {}

    turned_on = False
    for item in status_list:
        if item.get("code") == TARGET_DP and item.get("value") in (True, 1, "1", "true", "on"):
            turned_on = True
            break

    if not turned_on and isinstance(props, dict):
        val = props.get(TARGET_DP)
        if val in (True, 1, "1", "true", "on"):
            turned_on = True

    if not turned_on:
        return

    try:
        requests.get(VM_URL, timeout=5)
    except Exception:
        pass

# === Conectar al MQ y escuchar ===
openmq = TuyaOpenMQ(openapi)
openmq.start()
openmq.add_message_listener(on_message)

while True:
    time.sleep(60)
