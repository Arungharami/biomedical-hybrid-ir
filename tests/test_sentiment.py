import pytest

from biomedical_ir.sentiment import prepare_reviews, rating_label, text_hash


@pytest.mark.parametrize("rating,label", [(1, "negative"), (4, "negative"),
    (5, "neutral"), (6, "neutral"), (7, "positive"), (10, "positive")])
def test_boundaries(rating, label):
    assert rating_label(rating) == label


@pytest.mark.parametrize("rating", [0, 11, float("nan"), float("inf")])
def test_invalid_rating(rating):
    with pytest.raises(ValueError):
        rating_label(rating)


def test_deduplication_and_official_split_overlap():
    train, _ = prepare_reviews([{"review": "Good &amp; helpful", "rating": 9}])
    test, audit = prepare_reviews([
        {"review": " GOOD & helpful ", "rating": 9},
        {"review": "Pain remains", "rating": 2},
        {"review": "pain  remains", "rating": 2},
        {"review": "", "rating": 3},
        {"review": "x", "rating": 20}], [r["hash"] for r in train])
    assert len(test) == 1
    assert audit == {"input": 5, "invalid": 2, "duplicate_or_overlap": 2, "kept": 1}
    assert text_hash("Good &amp; helpful") == text_hash("good & helpful")
