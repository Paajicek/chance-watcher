import os
import time
import json
import requests

API_URL = "https://www.chance.cz/api/rest/offer?limit=75"
THRESHOLD = 17
CHECK_INTERVAL = 15  # vteřin
NOTIFIED_FILE = "notified_matches.json"

# Získání proměnných z prostředí (bezpečně)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def load_notified_ids():
    try:
        with open(NOTIFIED_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_notified_ids(ids):
    with open(NOTIFIED_FILE, "w") as f:
        json.dump(ids, f)

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Chyba při posílání zprávy na Telegram: {e}")

def check_chance():
    notified_ids = load_notified_ids()
    try:
        response = requests.get(API_URL)
        data = response.json()
    except Exception as e:
        print(f"Chyba při načítání dat z Chance.cz: {e}")
        return

    new_notifications = []

    for sport in data.get("offerSuperSports", []):
        for tab in sport.get("tabs", []):
            for offer in tab.get("offerCompetitionAnnuals", []):
                for match in offer.get("matches", []):
                    match_id = match.get("id")
                    match_name = match.get("nameFull", "Neznámý zápas")
                    count_tables = match.get("countEventTables", 0)
                    url = f"https://www.chance.cz{match.get('url')}"

                    if count_tables >= THRESHOLD and match_id not in notified_ids:
                        message = (
                            f"🎾 *Nový kurzový zápas!*\n"
                            f"🆚 {match_name}\n"
                            f"📊 Počet sázkových tabulek: {count_tables}\n"
                            f"🔗 {url}"
                        )
                        send_telegram_message(message)
                        new_notifications.append(match_id)

    if new_notifications:
        notified_ids.extend(new_notifications)
        save_notified_ids(notified_ids)

if __name__ == "__main__":
    print("✅ Sledování Chance.cz spuštěno...")
    while True:
        check_chance()
        time.sleep(CHECK_INTERVAL)
