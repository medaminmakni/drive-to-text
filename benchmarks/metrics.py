"""Accuracy metrics for OCR output: character error rate (CER) and word error rate (WER).

Both are the edit distance between the OCR text and the ground truth, divided by the
length of the ground truth. 0.0 is perfect, 0.10 means 10% of characters are wrong.
Values can go above 1.0 when the engine outputs a lot of extra text.
"""

import re
import unicodedata

ARABIC_DIACRITICS = re.compile(r"[ً-ْٰـ]")  # tashkeel + tatweel
ALEF_VARIANTS = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا"})
EASTERN_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")


def normalize(text: str) -> str:
    """Remove differences that are not reading errors.

    - Unicode compatibility forms (Arabic presentation forms, ligatures) are unified.
    - Arabic diacritics and tatweel are removed, alef variants are unified,
      Arabic-Indic digits become 0-9. Engines and ground truths disagree on these
      even when the reading is correct.
    - All whitespace (spaces, line breaks) collapses to one space.
    """
    text = unicodedata.normalize("NFKC", text)
    text = ARABIC_DIACRITICS.sub("", text)
    text = text.translate(ALEF_VARIANTS).translate(EASTERN_DIGITS)
    return " ".join(text.split())


def edit_distance(a, b) -> int:
    """Levenshtein distance between two sequences (strings or word lists)."""
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, item_a in enumerate(a, 1):
        current = [i]
        for j, item_b in enumerate(b, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (item_a != item_b)))
        previous = current
    return previous[-1]


def cer(prediction: str, reference: str) -> float:
    ref, pred = normalize(reference), normalize(prediction)
    if not ref:
        return 0.0 if not pred else 1.0
    return edit_distance(pred, ref) / len(ref)


def wer(prediction: str, reference: str) -> float:
    ref, pred = normalize(reference).split(), normalize(prediction).split()
    if not ref:
        return 0.0 if not pred else 1.0
    return edit_distance(pred, ref) / len(ref)


def word_f1(prediction: str, reference: str) -> float:
    """Order-free score: F1 of the words found, counted with repetitions.

    CER and WER also punish a different reading order (for example a two-column
    layout read column by column). This score only checks that the right words
    were read, so the two together separate reading errors from ordering errors.
    1.0 is perfect.
    """
    from collections import Counter

    ref, pred = Counter(normalize(reference).split()), Counter(normalize(prediction).split())
    if not ref and not pred:
        return 1.0
    common = sum((ref & pred).values())
    if common == 0:
        return 0.0
    precision, recall = common / sum(pred.values()), common / sum(ref.values())
    return 2 * precision * recall / (precision + recall)
