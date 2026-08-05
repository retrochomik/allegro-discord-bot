import os
import json
import re
import requests
from bs4 import BeautifulSoup

PROFILE = "https://allegrolokalnie.pl/uzytkownik/vin324pl"
WEBHOOK = os.getenv("DISCORD_WEBHOOK")
STATE_FILE = "state.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_state(data):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)


def get_offer_data(url):
    html = requests.get(url, headers=HEADERS).text
    soup = BeautifulSoup(html, "html.parser")

    title = ""
    price = ""
    location = ""
    image = ""

    # ==========================
    # Tytuł
    # ==========================
    page_title = soup.find("title")
    if page_title:
        title = page_title.get_text(strip=True)
        title = title.split("|")[0].strip()

    # ==========================
    # Zdjęcie
    # ==========================
    ogimg = soup.find("meta", property="og:image")
    if ogimg:
        image = ogimg.get("content", "")

    # ==========================
    # Cena + lokalizacja
    # ==========================
    description = ""
    meta = soup.find("meta", attrs={"name": "description"})
    if meta:
        description = meta.get("content", "")

    m = re.search(r'za\s+([\d\s,.]+)\s*zł', description)
    if m:
        price = m.group(1).strip() + " zł"

    l = re.search(r'w mieście\s+([^.,]+)', description)
    if l:
        location = l.group(1).strip()

    return {
        "title": title,
        "price": price,
        "location": location,
        "image": image
    }


# ===================================
# Pobranie listy ofert
# ===================================

html = requests.get(PROFILE, headers=HEADERS).text
soup = BeautifulSoup(html, "html.parser")

links = []

for a in soup.find_all("a", href=True):
    href = a["href"]

    if "/oferta/" in href:

        if href.startswith("/"):
            href = "https://allegrolokalnie.pl" + href

        links.append(href)

# usuń duplikaty
links = list(dict.fromkeys(links))

old = load_state()

# pierwsze uruchomienie
if not os.path.exists(STATE_FILE):
    save_state(links)
    print("Pierwsze uruchomienie.")
    exit()

# nowe oferty
new = [x for x in links if x not in old]

for link in new:

    offer = get_offer_data(link)

    embed = {
        "title": offer["title"] or "Nowa oferta",
        "url": link,
        "color": 0x2ECC71,
        "fields": [
            {
                "name": "💰 Cena",
                "value": offer["price"] or "Brak danych",
                "inline": True
            },
            {
                "name": "📍 Lokalizacja",
                "value": offer["location"] or "Brak danych",
                "inline": True
            }
        ]
    }

    if offer["image"]:
        embed["image"] = {
            "url": offer["image"]
        }

    requests.post(
        WEBHOOK,
        json={
            "username": "🎮 Retro Chomik",
            "content": "## 🆕 Nowa oferta na Allegro Lokalnie!",
            "embeds": [embed]
        }
    )

save_state(links)
