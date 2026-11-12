"""Two uses:

    python -m lectura                      analyse the health articles in data/intros.csv
    python -m lectura "Texto a revisar."   score any text you write
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .data import load
from .readability import BAND_ORDER, analyze

OUTPUT = Path(__file__).resolve().parent.parent / "output"
SURFACE, INK, INK_SECONDARY, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
AXIS, BLUE, LIGHT_BLUE = "#c3c2b7", "#2a78d6", "#9ec5f4"
EASY_ENOUGH = {"Normal", "Bastante fácil", "Muy fácil"}


def score_articles(intros: pd.DataFrame) -> pd.DataFrame:
    scores = pd.DataFrame([analyze(text) for text in intros["text"]])
    scores.insert(0, "article", intros["article"].to_numpy())
    return scores.sort_values("score").reset_index(drop=True)


def chart(scores: pd.DataFrame, path: Path) -> None:
    counts = scores["band"].value_counts().reindex(BAND_ORDER, fill_value=0)
    hard = int(counts[[name for name in BAND_ORDER if name not in EASY_ENOUGH]].sum())
    fig, ax = plt.subplots(figsize=(8, 4.2), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    fig.text(0.02, 0.95, f"{hard} de {len(scores)} artículos de salud son difíciles de leer",
             fontsize=13, fontweight="bold", color=INK, va="top")
    fig.text(0.02, 0.87, "Artículos de salud de Wikipedia en español según la facilidad de "
             "lectura de su introducción (escala INFLESZ).",
             fontsize=9.5, color=INK_SECONDARY, va="top")
    fig.text(0.02, 0.03, "Fuente: Wikipedia en español (CC BY-SA 4.0). Índice de Szigriszt-Pazos.",
             fontsize=8, color=MUTED, va="bottom")
    labels = ["Muy difícil\n(menos de 40)", "Algo difícil\n(40 a 55)", "Normal\n(55 a 65)",
              "Bastante fácil\n(65 a 80)", "Muy fácil\n(más de 80)"]
    colors = [LIGHT_BLUE if name in EASY_ENOUGH else BLUE for name in BAND_ORDER]
    bars = ax.bar(labels, counts.to_numpy(), width=0.6, color=colors)
    for bar, value in zip(bars, counts.to_numpy()):
        ax.text(bar.get_x() + bar.get_width() / 2, value + counts.max() * 0.02, str(value),
                ha="center", fontsize=11, color=INK)
    ax.set_ylim(0, counts.max() * 1.15)
    ax.yaxis.set_visible(False)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(colors=MUTED, labelsize=9, length=0)
    fig.subplots_adjust(left=0.04, right=0.97, top=0.76, bottom=0.2)
    fig.savefig(path, dpi=160, facecolor=SURFACE)
    plt.close(fig)


def main() -> None:
    if len(sys.argv) > 1:
        result = analyze(" ".join(sys.argv[1:]))
        print(f"Facilidad de lectura: {result['score']} de 100 ({result['band']})")
        print(f"Palabras por oración: {result['words_per_sentence']}   "
              f"Sílabas por palabra: {result['syllables_per_word']}")
        return
    (OUTPUT / "charts").mkdir(parents=True, exist_ok=True)
    scores = score_articles(load())
    scores.to_csv(OUTPUT / "readability_by_article.csv", index=False, encoding="utf-8-sig")
    chart(scores, OUTPUT / "charts" / "readability_bands.png")
    report = scores["band"].value_counts().reindex(BAND_ORDER, fill_value=0)
    print(report.to_string())
    print("median score", scores["score"].median(),
          "| words/sentence", scores["words_per_sentence"].median(),
          "| syllables/word", scores["syllables_per_word"].median())
    print(pd.concat([scores.head(5), scores.tail(5)]).drop(columns=["words", "sentences"])
          .to_string(index=False))


if __name__ == "__main__":
    main()
