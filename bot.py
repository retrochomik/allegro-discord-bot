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
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_offer_data(url):
    try:
        r = requests.get(
            url,
            headers=HEADERS,
            timeout=20
        )

        if r.status_code != 200:
            print(f"Nie udało się pobrać oferty: {url} -> HTTP {r.status_code}")
            return {
                "title": "",
                "price": "",
                "location": "",
                "image": ""
            }

        html = r.text
        soup = BeautifulSoup(html, "html.parser")

        title = ""
        price = ""
        location = ""
        image = ""

        # ==========================
        # TYTUŁ
        # ==========================

        page_title = soup.find("title")

        if page_title:
            title = page_title.get_text(strip=True)
            title = title.split("|")[0].strip()

        # ==========================
        # ZDJĘCIE
        # ==========================

        ogimg = soup.find("meta", property="og:image")

        if ogimg:
            image = ogimg.get("content", "")

        # ==========================
        # DESCRIPTION
        # ==========================

        description = ""

        meta = soup.find(
            "meta",
            attrs={"name": "description"}
        )

        if meta:
            description = meta.get("content", "")

        # ==========================
        # CENA
        # ==========================

        m = re.search(
            r'za\s+([\d\s,.]+)\s*zł',
            description
        )

        if m:
            price = m.group(1).strip() + " zł"

        # ==========================
        # LOKALIZACJA
        # ==========================

        l = re.search(
            r'w mieście\s+([^.,]+)',
            description
        )

        if l:
            location = l.group(1).strip()

        return {
            "title": title,
            "price": price,
            "location": location,
            "image": image
        }

    except Exception as e:

        print(f"Błąd pobierania oferty {url}: {e}")

        return {
            "title": "",
            "price": "",
            "location": "",
            "image": ""
        }


def send_discord(embed, content):

    try:

        r = requests.post(
            WEBHOOK,
            json={
                "username": "🎮 Retro Chomik",
                "content": content,
                "embeds": [embed]
            },
            timeout=20
        )

        print(
            f"Discord -> HTTP {r.status_code}"
        )

        return r.status_code == 204

    except Exception as e:

        print(
            f"Błąd wysyłania Discord: {e}"
        )

        return False


# ===================================
# POBIERANIE PROFILU
# ===================================

print("=== POBIERAM PROFIL ===")

try:

    r = requests.get(
        PROFILE,
        headers=HEADERS,
        timeout=20
    )

    r.raise_for_status()

except Exception as e:

    print(f"Błąd pobierania profilu: {e}")
    exit(1)


soup = BeautifulSoup(
    r.text,
    "html.parser"
)

links = []

for a in soup.find_all("a", href=True):

    href = a["href"]

    if "/oferta/" in href:

        if href.startswith("/"):
            href = "https://allegrolokalnie.pl" + href

        links.append(href)


# usuń duplikaty

links = list(
    dict.fromkeys(links)
)


print("\n=== OFERTY Z PROFILU ===")

for link in links:
    print(link)

print("========================")


# ===================================
# WCZYTANIE STATE
# ===================================

old = load_state()

print("\n=== STATE.JSON ===")

for link in old:
    print(link)

print("==================")


# ===================================
# PIERWSZE URUCHOMIENIE
# ===================================

if not os.path.exists(STATE_FILE):

    print(
        "\nPierwsze uruchomienie - zapisuję aktualny stan."
    )

    save_state(links)

    exit()


# ===================================
# NOWE OFERTY
# ===================================

new = [
    link
    for link in links
    if link not in old
]


print("\n=== NOWE OFERTY ===")

for link in new:
    print(link)

print("===================")


# ===================================
# USUNIĘTE / SPRZEDANE OFERTY
# ===================================

removed = [
    link
    for link in old
    if link not in links
]


print("\n=== ZNIKNIĘTE OFERTY ===")

for link in removed:
    print(link)

print("========================")


# ===================================
# WYSYŁANIE NOWYCH OFERT
# ===================================

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

    send_discord(
        embed,
        "## 🆕 Nowa oferta na Allegro Lokalnie!"
    )


# ===================================
# WYSYŁANIE SPRZEDANYCH / ZAKOŃCZONYCH
# ===================================

for link in removed:

    offer = get_offer_data(link)

    # jeżeli strona nie zwróciła danych,
    # robimy nazwę z adresu

    title = offer["title"]

    if not title:

        slug = link.rstrip("/").split("/")[-1]

        title = slug.replace("-", " ")

        title = title.capitalize()

    embed = {

        "title": title,

        "url": link,

        "color": 0xE74C3C,

        "fields": [

            {
                "name": "📦 Status",
                "value": "Oferta zniknęła z aktywnych",
                "inline": False
            },

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

    send_discord(
        embed,
        "## 🔴 Oferta sprzedana / zakończona!"
    )


# ===================================
# AKTUALIZACJA STATE
# ===================================

print("\n=== AKTUALIZUJĘ STATE.JSON ===")

save_state(links)

print(
    f"Zapisano {len(links)} aktywnych ofert."
)

print("\nKoniec.")
