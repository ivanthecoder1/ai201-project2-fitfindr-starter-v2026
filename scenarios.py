"""
The runs your test needs. ← UNIT 4, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
the empty-search branch needs an impossible query. One about the fit card needs
the same item run more than once. Working that out is Milestone 3's first step,
and this file is where you write it down.

`run_eval.py` runs everything here five times and writes the run log — five
because your criteria are written out of five.

Three scenarios are filled in to show the shape. Add or change whatever your
own criteria need — these are a starting point, not a fixed set.
"""

SCENARIOS = [
    # ── Criterion 1: a matching query completes all three tools ──────────────
    # Different phrasings, because your reason for 4 of 5 is that keyword
    # matching can miss. The same query five times wouldn't test that.
    {
        "name": "matching query completes",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 1,
    },
    {
        "name": "matching query with a size",
        "query": "90s track jacket in size M",
        "wardrobe": "example",
        "criterion": 1,
    },
    {
        "name": "matching query, different item type",
        "query": "denim jacket under $50",
        "wardrobe": "example",
        "criterion": 1,
    },

    # ── Criterion 2: impossible query stops before suggest_outfit ────────────
    {
        "name": "impossible query stops early",
        "query": "designer ballgown size XXS under $5",
        "wardrobe": "example",
        "criterion": 2,
    },

    # ── Criterion 3: the item that was selected is the item suggest_outfit got
    # Any normal query works. What's checked is session["selected_item"]["id"]
    # against session["suggest_item_id"].
    {
        "name": "state: selected item reaches suggest_outfit",
        "query": "band tee under $25",
        "wardrobe": "example",
        "criterion": 3,
    },

    # ── Criterion 4: fit card is 2-4 sentences, names item, price, platform ──
    # The same query five times (cache off) gives five fit cards for the same
    # item, which is what this criterion needs.
    {
        "name": "fit card, same item repeated",
        "query": "y2k baby tee under $20",
        "wardrobe": "example",
        "criterion": 4,
    },

    # ── Criterion 5: nothing returned is over max_price ──────────────────────
    # The search is deterministic, so repeating one query proves nothing. These
    # use different ceilings, including one exactly at a listing's price
    # (lst_002 is $18.0, so "under $18" should still include it).
    {
        "name": "price ceiling, boundary",
        "query": "graphic tee under $18",
        "wardrobe": "example",
        "criterion": 5,
    },
    {
        "name": "price ceiling, mid-range",
        "query": "denim jacket under $40",
        "wardrobe": "example",
        "criterion": 5,
    },
    {
        "name": "price ceiling, tight",
        "query": "vintage tee under $20",
        "wardrobe": "example",
        "criterion": 5,
    },

    # ── Diagnostic: not one of the five criteria ─────────────────────────────
    {
        "name": "empty wardrobe",
        "query": "denim jacket under $50",
        "wardrobe": "empty",
        "criterion": None,
    },
]

WARDROBES = ("example", "empty")


def validate() -> list[str]:
    """Complain about anything malformed, before a long run rather than during."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("query", "").strip():
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe {scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )
    return problems
