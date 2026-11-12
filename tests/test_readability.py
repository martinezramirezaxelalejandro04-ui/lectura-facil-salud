import pytest

from lectura.readability import analyze, band, count_syllables, sentences, words  # noqa: I001


@pytest.mark.parametrize("word, expected", [
    ("sol", 1), ("casa", 2), ("médico", 3), ("enfermedad", 4),
    ("día", 2), ("país", 2), ("aéreo", 4), ("poeta", 3),        # hiatus
    ("ciudad", 2), ("cuidado", 3), ("aire", 2), ("agua", 2),     # diphthongs
    ("que", 1), ("quien", 1), ("guerra", 2), ("guía", 2),        # silent u
    ("pingüino", 3), ("hoy", 1), ("y", 1), ("ahora", 3),
    ("hipertensión", 4), ("otorrinolaringólogo", 9),
])
def test_syllables(word, expected):
    assert count_syllables(word) == expected


def test_words_ignore_numbers_and_punctuation():
    assert words("En 2024, ¡hubo 3 casos!") == ["en", "hubo", "casos"]


def test_sentences_are_split_on_final_punctuation():
    assert len(sentences("Lávate las manos. ¿Tienes fiebre? Ve al médico.")) == 3


def test_invisible_footnote_marks_do_not_merge_sentences():
    # Wikipedia leaves a zero-width space after the period where a footnote was.
    with_marks = "Da fiebre.​​ Da dolor.​Se cura sola."
    assert analyze(with_marks)["sentences"] == 3
    assert analyze(with_marks)["score"] == analyze("Da fiebre. Da dolor. Se cura sola.")["score"]


def test_score_matches_a_hand_calculation():
    # 2 sentences, 7 words, 10 syllables: 206.835 - 62.3 * (10 / 7) - (7 / 2) = 114.3
    simple = analyze("La casa es azul. El sol sale.")
    assert simple["sentences"] == 2 and simple["words"] == 7
    syllables = 1 + 2 + 1 + 2 + 1 + 1 + 2      # la ca-sa es a-zul el sol sa-le
    assert simple["score"] == pytest.approx(206.835 - 62.3 * syllables / 7 - 7 / 2, abs=0.05)


def test_plain_language_scores_higher_than_technical_language():
    plain = analyze("El dengue es una enfermedad. La transmite un mosquito. Da fiebre y dolor.")
    technical = analyze(
        "El dengue es una enfermedad infecciosa de etiología viral transmitida por mosquitos "
        "del género Aedes, caracterizada por manifestaciones clínicas heterogéneas que "
        "comprenden desde formas asintomáticas hasta cuadros hemorrágicos potencialmente letales."
    )
    assert plain["score"] > 80 > 40 > technical["score"]
    assert plain["band"] == "Muy fácil" and technical["band"] == "Muy difícil"


@pytest.mark.parametrize("score, expected", [
    (85, "Muy fácil"), (70, "Bastante fácil"), (55, "Normal"), (54.9, "Algo difícil"),
    (39.9, "Muy difícil"), (-10, "Muy difícil"),
])
def test_bands(score, expected):
    assert band(score) == expected


def test_empty_text_is_rejected():
    with pytest.raises(ValueError):
        analyze("123 456.")
