import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmarks"))

from metrics import cer, normalize, wer, word_f1  # noqa: E402


def test_perfect_reading_scores_zero_error():
    assert cer("Facture 2026", "Facture 2026") == 0.0
    assert wer("Facture 2026", "Facture 2026") == 0.0
    assert word_f1("Facture 2026", "Facture 2026") == 1.0


def test_one_wrong_character():
    assert cer("Factvre", "Facture") == pytest.approx(1 / 7)


def test_whitespace_and_line_breaks_are_ignored():
    assert cer("Total\n\n  TTC", "Total TTC") == 0.0


def test_arabic_diacritics_alef_and_digits_are_normalized():
    assert normalize("إِشْعَار  ١٢٣") == "اشعار 123"
    assert cer("اشعار بالدفع", "إِشْعَار بالدفع") == 0.0


def test_word_f1_ignores_reading_order_but_cer_does_not():
    truth = "République Tunisienne Municipalité de Sfax"
    swapped = "Municipalité de Sfax République Tunisienne"
    assert word_f1(swapped, truth) == 1.0
    assert cer(swapped, truth) > 0.3


def test_empty_output_is_a_full_error():
    assert cer("", "texte") == 1.0
    assert word_f1("", "texte") == 0.0


def test_invisible_direction_marks_are_ignored():
    assert cer("‎République Tunisienne‏", "République Tunisienne") == 0.0


def test_form_blocks_are_read_top_to_bottom_then_left_to_right():
    from sampleset import reading_order_text

    blocks = [([300, 100, 400, 120], "right"), ([10, 102, 100, 118], "left"), ([10, 200, 100, 220], "below")]
    assert reading_order_text(blocks) == "left\nright\nbelow"
