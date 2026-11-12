"""Measure how easy a Spanish text is to read.

Index: Szigriszt-Pazos "perspicuity" (1993), the Spanish adaptation of the
Flesch formula:

    206.835 - 62.3 * (syllables / words) - (words / sentences)

Scale: INFLESZ (Barrio-Cantalejo et al., 2008), built for health texts read by
patients. Higher is easier. Long words and long sentences lower the score.
"""
from __future__ import annotations

import re

STRONG = set("aeoáéó")
ACCENTED_WEAK = set("íú")
VOWELS = STRONG | ACCENTED_WEAK | set("iuü")

BANDS = [  # (lowest score of the band, name)
    (80, "Muy fácil"), (65, "Bastante fácil"), (55, "Normal"),
    (40, "Algo difícil"), (float("-inf"), "Muy difícil"),
]
BAND_ORDER = [name for _, name in reversed(BANDS)]


def count_syllables(word: str) -> int:
    """Syllables of a Spanish word, following the diphthong and hiatus rules."""
    word = word.lower()
    word = word.replace("qu", "q")                 # the u in que, qui is silent
    word = re.sub(r"gu(?=[eéií])", "g", word)      # and in gue, gui
    if word.endswith("y"):                         # hoy, rey, muy: final y sounds like i
        word = word[:-1] + "i"
    syllables, previous = 0, None
    for letter in word:
        if letter not in VOWELS:
            previous = None
            continue
        if previous is None:
            syllables += 1                         # a new group of vowels
        elif (previous in STRONG and letter in STRONG) \
                or previous in ACCENTED_WEAK or letter in ACCENTED_WEAK:
            syllables += 1                         # hiatus: a-é-re-o, dí-a, pa-ís
        previous = letter
    return max(syllables, 1)


def clean_text(text: str) -> str:
    """Remove invisible characters that hide sentence endings.

    Wikipedia leaves a zero-width space where each footnote marker was. A period
    followed by one of them is not followed by a space, so without this step
    whole paragraphs were read as one sentence of hundreds of words.
    """
    text = re.sub(r"[​‌‍⁠﻿]", "", text)
    text = re.sub(r"(?<=[.!?…])(?=[A-ZÁÉÍÓÚÑ¿¡])", " ", text)   # "bajas.Sucede" -> "bajas. Sucede"
    return re.sub(r"\s+", " ", text).strip()


def words(text: str) -> list[str]:
    return re.findall(r"[a-záéíóúüñ]+", text.lower())


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?…])\s+", text.strip())
    return [part for part in parts if words(part)]


def band(score: float) -> str:
    return next(name for lowest, name in BANDS if score >= lowest)


def analyze(text: str) -> dict:
    """Score a text and report the two things that drive the score."""
    text = clean_text(text)
    word_list, sentence_list = words(text), sentences(text)
    if not word_list:
        raise ValueError("the text has no words")
    syllables_per_word = sum(count_syllables(word) for word in word_list) / len(word_list)
    words_per_sentence = len(word_list) / len(sentence_list)
    score = 206.835 - 62.3 * syllables_per_word - words_per_sentence
    return {
        "words": len(word_list),
        "sentences": len(sentence_list),
        "syllables_per_word": round(syllables_per_word, 2),
        "words_per_sentence": round(words_per_sentence, 1),
        "score": round(score, 1),
        "band": band(score),
    }
