import os
import json
import requests
from bs4 import BeautifulSoup

PROFILE = "https://allegrolokalnie.pl/uzytkownik/vin324pl"
WEBHOOK = os.getenv("DISCORD_WEBHOOK")
STATE_FILE = "state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return []

def save_state(data):
    with open(STATE_FILE, "w") as f:
        json.dump(data, f)

html = requests.get(
    PROFILE,
    headers={"User-Agent": "Mozilla/5.0"}
).text

soup = BeautifulSoup(html, "html.parser")

links = []

for a in soup.find_all("a", href=True):
    href = a["href"]
    if "/oferta/" in href:
        if href.startswith("/"):
            href = "https://allegrolokalnie.pl" + href
        links.append(href)

links = list(dict.fromkeys(links))

old = load_state()

# Pierwsze uruchomienie - zapisz aktualne oferty i nic nie wysyłaj
if not os.path.exists(STATE_FILE):
    save_state(links)
    print("Pierwsze uruchomienie")
    exit()

new = [x for x in links if x not in old]

for link in new:
    requests.post(
        WEBHOOK,
        json={"content": f"🆕 Nowa oferta na Allegro Lokalnie!\n{link}"}
    )

save_state(links)
