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
    print("\n=== WCZYTUJĘ STATE.JSON ===")
    print("Plik istnieje:", os.path.exists(STATE_FILE))
    print("Ścieżka:", os.path.abspath(STATE_FILE))

    if not os.path.exists(STATE_FILE):
        print("BRAK PLIKU STATE.JSON")
        return []

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        print(f"Wczytano {len(data)} ofert:")

        for item in data:
            print(item)

        return data

    except Exception as e:
        print("BŁĄD ODCZYTU STATE.JSON:", e)
        return []


def save_state(data):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_offer_data(url):
    html = requests.get(url, headers=HEADERS, timeout=20).text
    soup = BeautifulSoup(html, "html.parser")

    title = ""
    price = ""
    location = ""
    image = ""

    page_title = soup.find("title")
    if page_title:
        title = page_title.get_text(strip=True)
        title = title.split("|")[0].strip()

    ogimg = soup.find("meta", property="og:image")
    if ogimg:
        image = ogimg.get("content", "")

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


print("=== POBIERAM PROFIL ===")

html = requests.get(PROFILE, headers=HEADERS, timeout=20).text
soup = BeautifulSoup(html, "html.parser")

links = []

for a in soup.find_all("a", href=True):
    href = a["href"]

    if "/oferta/" in href:
        if href.startswith("/"):
            href = "https://allegrolokalnie.pl" + href

        links.append(href)

links = list(dict.fromkeys(links))

print("\n=== OFERTY Z PROFILU ===")
for l in links:
    print(l)
print("========================")

old = load_state()

print("\n=== STATE.JSON ===")
for l in old:
    print(l)
print("==================")

if not os.path.exists(STATE_FILE):
    print("Pierwsze uruchomienie")
    save_state(links)
    exit()

new = [x for x in links if x not in old]

print("\n=== NOWE OFERTY ===")
for l in new:
    print(l)
print("===================")

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

    r = requests.post(
        WEBHOOK,
        json={
            "username": "🎮 Retro Chomik",
            "content": "## 🆕 Nowa oferta na Allegro Lokalnie!",
            "embeds": [embed]
        },
        timeout=20
    )

    print(f"Wysłano {link} -> HTTP {r.status_code}")

print("\n=== ZAPISUJĘ DO STATE.JSON ===")
for l in links:
    print(l)

save_state(links)

print("\nKoniec.")
