from referee.evidence.retrieval import build_index, context_for_concern

FILLER = "Background text about general matters and context. "


def _doc():
    text = ("Abstract. We study X.\n\n" + FILLER * 700
            + "\n\nMethods. Participants were sampled by convenience from one hospital and no control group was used.\n\n"
            + FILLER * 300)
    return [{"document_id": "D1", "text": text}]


def test_deep_passage_is_retrieved_beyond_old_30k_cutoff():
    docs = _doc()
    assert docs[0]["text"].find("convenience") > 30000  # old verifier would never see it
    idx = build_index(docs)
    ctx = context_for_concern(idx, "convenience sampling one hospital no control group", ["no control group was used"])
    assert "convenience from one hospital" in ctx
    assert "D1:P" in ctx  # passages are labelled so the verifier can cite them


def test_no_match_says_so_instead_of_guessing():
    idx = build_index(_doc())
    assert context_for_concern(idx, "zzzz qqqq") == "(no relevant passage found in the supplied material)"


def test_deterministic():
    idx = build_index(_doc())
    q = "control group sampling"
    assert context_for_concern(idx, q) == context_for_concern(idx, q)
