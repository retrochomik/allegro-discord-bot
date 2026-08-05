import os
import json
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

    og = soup.find("meta", property="og:title")
    if og:
        title = og.get("content", "")

    price = ""
    location = ""
    image = ""

    ogimg = soup.find("meta", property="og:image")
    if ogimg:
        image = ogimg.get("content", "")

    text = soup.get_text(" ", strip=True)

    import re

    p = re.search(r'(\d[\d ]*)\s*zł', text)
    if p:
        price = p.group(0)

    loc = re.search(r'Miejscowość\s*([A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż \-]+)', text)
    if loc:
        location = loc.group(1)

    return {
        "title": title,
        "price": price,
        "location": location,
        "image": image
    }


html = requests.get(PROFILE, headers=HEADERS).text
soup = BeautifulSoup(html, "lxml")

links = []

for a in soup.find_all("a", href=True):
    href = a["href"]

    if "/oferta/" in href:
        if href.startswith("/"):
            href = "https://allegrolokalnie.pl" + href

        links.append(href)

links = list(dict.fromkeys(links))

old = load_state()

if not os.path.exists(STATE_FILE):
    save_state(links)
    print("Pierwsze uruchomienie")
    exit()

new = [x for x in links if x not in old]

for link in new:

    offer = get_offer_data(link)

    embed = {
        "title": offer["title"],
        "url": link,
        "color": 3066993,
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
            "embeds": [embed]
        }
    )

save_state(links)
