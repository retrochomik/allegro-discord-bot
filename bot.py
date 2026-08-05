import os
import json
import requests
from bs4 import BeautifulSoup

PROFILE = "https://allegrolokalnie.pl/uzytkownik/vin324pl"
WEBHOOK = os.getenv("DISCORD_WEBHOOK")
STATE_FILE = "state.json"


def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_state(data):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)


html = requests.get(
    PROFILE,
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=20
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

# Pierwsze uruchomienie
if not old:
    save_state(links)
    print("Pierwsze uruchomienie - zapisano oferty.")
    exit(0)

new = [x for x in links if x not in old]

for link in new:
    requests.post(
        WEBHOOK,
        json={
            "username": "🎮 Retro Chomik",
            "avatar_url": "https://i.imgur.com/q8Q1VbP.png",
            "content": f"🆕 **Nowa oferta na Allegro Lokalnie!**\n{link}"
        },
        timeout=20
    )

save_state(links)

print(f"Nowych ofert: {len(new)}")
