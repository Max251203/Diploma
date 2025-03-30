import os
from dotenv import load_dotenv
from core.ws_client import HomeAssistantWSClient
from core.device_manager import DeviceManager
from core.entity_manager import EntityManager

def main():
    load_dotenv()

    ws_url = os.getenv("HA_WS_URL")
    token = os.getenv("HA_TOKEN")

    if not ws_url or not token:
        print("❌ Не заданы переменные окружения HA_WS_URL и HA_TOKEN")
        return

    ws_client = HomeAssistantWSClient(ws_url, token)
    entity_manager = EntityManager(ws_client)
    device_manager = DeviceManager(ws_client, entity_manager)

    categorized = device_manager.get_categorized_devices()


    # # 👉 Укажи entity_id твоей лампы (можно взять из вывода DeviceManager)
    # lamp_entity_id = "light.midesklamp1s_963a"

    # # === Получение текущего состояния лампы ===
    # state = entity_manager.get_state(lamp_entity_id)
    # print(f"💡 Состояние лампы '{lamp_entity_id}': {state}")

    # # === Включение лампы ===
    # print("\n🔛 Включаем лампу...")
    # if entity_manager.turn_on(lamp_entity_id):
    #     print("✅ Лампа включена")
    # else:
    #     print("❌ Не удалось включить лампу")

    # # === Выключение лампы ===
    # print("\n🔌 Выключаем лампу...")
    # if entity_manager.turn_off(lamp_entity_id):
    #     print("✅ Лампа выключена")
    # else:
    #     print("❌ Не удалось выключить лампу")

    # # === Переключение (toggle) ===
    # print("\n🔁 Переключаем (toggle) лампу...")
    # if entity_manager.toggle(lamp_entity_id):
    #     print("✅ Состояние лампы переключено")
    # else:
    #     print("❌ Не удалось переключить лампу")



    print("\n📦 Устройства по категориям:\n")
    for category, devices in categorized.items():
        if not devices:
            continue
        print(f"📂 {category} ({len(devices)})")
        for device in devices:
            print(f"  🧩 {device['name']} | {device['manufacturer']} {device['model']}")
            # сд
        print("-" * 60)


if __name__ == "__main__":
    main()