"""Tests for the evaluation metrics."""
from lipisetu.eval.metrics import precision_at_k, recall_at_k, mrr_at_k, ndcg_at_k, rbo, cross_script_consistency


def test_precision_recall():
    ranking = ["a", "b", "c", "d", "e"]
    relevant = {"b", "e", "z"}
    assert precision_at_k(ranking, relevant, 5) == 2 / 5
    assert recall_at_k(ranking, relevant, 5) == 2 / 3


def test_mrr():
    assert mrr_at_k(["a", "b", "c"], {"c"}) == 1 / 3
    assert mrr_at_k(["a", "b", "c"], {"z"}) == 0.0


def test_ndcg_perfect_and_zero():
    assert ndcg_at_k(["a", "b", "x"], {"a", "b"}) == 1.0
    assert ndcg_at_k(["x", "y"], {"a"}) == 0.0
    assert 0.0 < ndcg_at_k(["x", "a"], {"a"}) < 1.0


def test_rbo():
    same = ["a", "b", "c", "d"]
    assert abs(rbo(same, same, k=4) - 1.0) < 1e-9
    assert rbo(["a", "b"], ["c", "d"], k=2) == 0.0
    # Swapping the top two items lowers RBO, but not to zero
    swapped = rbo(["a", "b", "c", "d"], ["b", "a", "c", "d"], k=4)
    assert 0.5 < swapped < 1.0


def test_cross_script_consistency():
    rankings = {"deva": ["a", "b"], "roman": ["a", "b"], "casual": ["a", "b"]}
    assert abs(cross_script_consistency(rankings, k=2) - 1.0) < 1e-9
