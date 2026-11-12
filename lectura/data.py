"""Download the opening section of Spanish Wikipedia articles about health topics.

Source: MediaWiki API (text under CC BY-SA 4.0). The opening section is what
most readers see, and what search engines and assistants quote.

    python -m lectura.data
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

API = "https://es.wikipedia.org/w/api.php"
USER_AGENT = "lectura-facil-salud/0.1 (educational open-data project)"
DATA = Path(__file__).resolve().parent.parent / "data"

TOPICS = [
    "Diabetes mellitus", "Hipertensión arterial", "Obesidad", "Sobrepeso", "Colesterol",
    "Infarto agudo de miocardio", "Insuficiencia cardíaca", "Accidente cerebrovascular",
    "Cáncer", "Cáncer de mama", "Cáncer de próstata", "Cáncer de pulmón",
    "Cáncer colorrectal", "Cáncer de cuello uterino", "Leucemia",
    "Gripe", "Resfriado común", "COVID-19", "Neumonía", "Bronquitis", "Asma",
    "Enfermedad pulmonar obstructiva crónica", "Tuberculosis",
    "Dengue", "Fiebre del Zika", "Malaria", "Cólera", "Rabia", "Tétanos", "Sarampión",
    "Varicela", "Hepatitis", "VIH/sida", "Poliomielitis",
    "Depresión", "Trastorno de ansiedad", "Insomnio", "Suicidio", "Salud mental",
    "Enfermedad de Alzheimer", "Enfermedad de Parkinson", "Epilepsia", "Migraña",
    "Síndrome de Down", "Anemia", "Osteoporosis", "Artritis reumatoide",
    "Gastritis", "Diarrea", "Apendicitis", "Cirrosis hepática", "Insuficiencia renal",
    "Cálculo renal", "Infección urinaria", "Glaucoma", "Catarata", "Caries",
    "Embarazo", "Lactancia materna", "Vacuna", "Antibiótico", "Paracetamol", "Ibuprofeno",
    "Tabaquismo", "Alcoholismo", "Desnutrición", "Donación de sangre",
]


def fetch_intros(titles: list[str]) -> pd.DataFrame:
    """Opening section (plain text) of each article; redirects are followed."""
    rows = []
    for start in range(0, len(titles), 20):                  # the API takes 20 titles at a time
        query = urllib.parse.urlencode({
            "action": "query", "prop": "extracts", "exintro": 1, "explaintext": 1,
            "redirects": 1, "format": "json", "formatversion": 2,
            "titles": "|".join(titles[start:start + 20]),
        })
        request = urllib.request.Request(f"{API}?{query}", headers={"User-Agent": USER_AGENT})
        for attempt in range(6):
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    pages = json.load(response)["query"]["pages"]
                break
            except urllib.error.HTTPError as error:
                if error.code != 429 or attempt == 5:
                    raise
                time.sleep(30 * (attempt + 1))   # the server asked us to slow down
        rows += [{"article": page["title"], "text": page.get("extract", "")}
                 for page in pages if not page.get("missing")]
        time.sleep(1)
    return pd.DataFrame(rows)


def load() -> pd.DataFrame:
    return pd.read_csv(DATA / "intros.csv")


if __name__ == "__main__":
    intros = fetch_intros(TOPICS)
    intros = intros[intros["text"].str.split().str.len() >= 40]   # skip stubs and redirects
    DATA.mkdir(exist_ok=True)
    intros.sort_values("article").to_csv(DATA / "intros.csv", index=False)
    print(f"{len(intros)} of {len(TOPICS)} articles saved")
