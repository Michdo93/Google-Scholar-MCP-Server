"""
Standalone-Testskript fuer google_scholar_web_search.py

Zweck: Die gleiche Suchlogik ausfuehren, die auch der MCP-Server nutzt,
OHNE Claude Desktop zu starten. Das Skript gibt zusaetzlich die exakte
URL aus, die es an Google Scholar schickt - diese URL kannst du direkt
in deinen Browser einfuegen, um manuell abzugleichen, ob die Ergebnisse
uebereinstimmen.

Verwendung (im aktivierten venv):

    Scripts\\python.exe test_scholar_search.py --query "ROS robot operating system"

    Scripts\\python.exe test_scholar_search.py --query "ROS security" --author "McClean" --year-from 2010 --year-to 2020

Optionen:
    --query        Suchbegriff (Pflicht)
    --author       Autor-Filter (optional, aktiviert die erweiterte Suche)
    --year-from    Startjahr (optional, nur zusammen mit --year-to nutzbar)
    --year-to      Endjahr (optional, nur zusammen mit --year-from nutzbar)
    --num-results  Anzahl Ergebnisse (Standard: 5)
"""

import argparse
import sys

import requests
from bs4 import BeautifulSoup

# Importiert dieselben Funktionen, die auch google_scholar_server.py nutzt -
# Aenderungen an google_scholar_web_search.py wirken sich hier sofort aus,
# ohne dass Claude Desktop neu gestartet werden muss.
from google_scholar_web_search import google_scholar_search, advanced_google_scholar_search


def debug_raw_titles(query: str):
    """Schickt genau dieselbe Anfrage wie google_scholar_search, gibt aber
    ALLE gefundenen Titel in der Reihenfolge aus, in der Google sie im HTML
    zurueckgibt - unabhaengig von num_results. Damit laesst sich pruefen,
    ob Google eine andere Ergebnismenge liefert (Bot-Erkennung) oder ob
    beim Parsen etwas uebersprungen wird (Parsing-Bug)."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get("https://scholar.google.com/scholar", params={"q": query}, headers=headers)
    print(f"HTTP Status: {response.status_code}")
    print(f"Antwortgroesse: {len(response.text)} Zeichen")

    soup = BeautifulSoup(response.text, "html.parser")
    items = soup.find_all("div", class_="gs_ri")
    print(f"Gefundene 'gs_ri'-Bloecke insgesamt: {len(items)}\n")

    for i, item in enumerate(items, start=1):
        title_tag = item.find("h3", class_="gs_rt")
        title = title_tag.get_text() if title_tag else "(kein Titel gefunden)"
        print(f"{i}. {title}")

    # Zusaetzlicher Hinweis, falls Google eine Captcha-/Bot-Warnseite
    # zurueckgibt statt echter Ergebnisse - das erscheint dann NICHT als
    # gs_ri-Block, sondern meist als eigene Fehlerseite.
    if len(items) == 0:
        if "unusual traffic" in response.text.lower() or "captcha" in response.text.lower():
            print("\n!!! Google hat vermutlich eine Bot-/Captcha-Seite zurueckgegeben, keine echten Ergebnisse !!!")
        else:
            print("\nKeine gs_ri-Bloecke gefunden - Seitenstruktur weicht evtl. vom erwarteten Format ab.")


def build_preview_url(query: str, author: str | None, year_from: int | None, year_to: int | None) -> str:
    """Baut dieselbe URL wie die eigentliche Suchfunktion, nur zum Anzeigen -
    zum Copy-Paste in den Browser fuer den manuellen Abgleich."""
    if author or (year_from and year_to):
        params = {"as_q": query}
        if author:
            params["as_sauthors"] = author
        if year_from and year_to:
            params["as_ylo"] = year_from
            params["as_yhi"] = year_to
    else:
        params = {"q": query}

    req = requests.Request("GET", "https://scholar.google.com/scholar", params=params)
    return req.prepare().url


def print_results(results):
    if not results:
        print("(Keine Ergebnisse gefunden)")
        return

    if len(results) == 1 and "error" in results[0]:
        print(f"FEHLER: {results[0]['error']}")
        return

    for i, r in enumerate(results, start=1):
        print(f"\n--- Ergebnis {i} ---")
        print(f"Titel:    {r.get('Title', 'N/A')}")
        print(f"Autoren:  {r.get('Authors', 'N/A')}")
        print(f"Abstract: {r.get('Abstract', 'N/A')[:200]}...")
        print(f"URL:      {r.get('URL', 'N/A')}")


def main():
    parser = argparse.ArgumentParser(
        description="Testet die Google-Scholar-Suchfunktionen direkt, ohne Claude Desktop."
    )
    parser.add_argument("--query", required=True, help="Suchbegriff")
    parser.add_argument("--author", default=None, help="Autor-Filter (optional)")
    parser.add_argument("--year-from", type=int, default=None, help="Startjahr (optional)")
    parser.add_argument("--year-to", type=int, default=None, help="Endjahr (optional)")
    parser.add_argument("--num-results", type=int, default=5, help="Anzahl Ergebnisse (Standard: 5)")
    parser.add_argument(
        "--debug-all-titles",
        action="store_true",
        help="Zeigt ALLE gefundenen Titel in Rohreihenfolge (ignoriert --num-results, --author, --year-*). "
        "Zum Vergleich mit der Browser-Reihenfolge.",
    )
    args = parser.parse_args()

    if args.debug_all_titles:
        preview_url = build_preview_url(args.query, None, None, None)
        print("=" * 80)
        print("DEBUG-MODUS: alle gefundenen Titel in Rohreihenfolge")
        print(f"Angefragte URL: {preview_url}")
        print("=" * 80)
        debug_raw_titles(args.query)
        return

    use_advanced = bool(args.author or (args.year_from and args.year_to))

    if args.year_from and not args.year_to or args.year_to and not args.year_from:
        print("Hinweis: --year-from und --year-to muessen zusammen angegeben werden. Ignoriere Jahresfilter.")
        args.year_from = args.year_to = None

    preview_url = build_preview_url(args.query, args.author, args.year_from, args.year_to)
    print("=" * 80)
    print("Diese URL wird angefragt - zum manuellen Abgleich im Browser oeffnen:")
    print(preview_url)
    print("=" * 80)

    try:
        if use_advanced:
            year_range = (args.year_from, args.year_to) if args.year_from and args.year_to else None
            print(f"\n[Nutze erweiterte Suche] query={args.query!r}, author={args.author!r}, year_range={year_range}")
            results = advanced_google_scholar_search(
                args.query, author=args.author, year_range=year_range, num_results=args.num_results
            )
        else:
            print(f"\n[Nutze einfache Stichwortsuche] query={args.query!r}")
            results = google_scholar_search(args.query, num_results=args.num_results)

        print_results(results)

    except Exception as e:
        print(f"\nUNERWARTETER FEHLER: {type(e).__name__}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
