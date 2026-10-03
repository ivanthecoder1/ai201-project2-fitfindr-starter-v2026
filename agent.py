"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""
import re
import config
import trace
from tools import search_listings, suggest_outfit, create_fit_card
from generate import ModelUnavailable


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """A fresh session for one user interaction. Every tool result goes in here."""
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price from the query
        "searched": False,           # True once search_listings has run (even if empty)
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one chosen: goes into suggest_outfit
        "suggest_item_id": None,     # id of the item suggest_outfit actually received
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── query parsing (regex, no model call) ──────────────────────────────────────

_PRICE_RE = re.compile(
    r"\b(?:under|below|less than|max(?:imum)?|up to|at most|no more than)"
    r"\s*\$?\s*(\d+(?:\.\d+)?)",
    re.I,
)
_DOLLAR_RE = re.compile(r"\$\s*(\d+(?:\.\d+)?)")
_SIZE_RE = re.compile(
    r"\b(?:in\s+)?(?:size|sz)\s+([a-z0-9]+(?:/[a-z0-9]+)?(?:\s+l\d+)?)",
    re.I,
)


def parse_query(query: str) -> dict:
    """
    Pull size and max_price out of the query with regex; what's left is the
    description. Examples:
      "vintage graphic tee under $30, size M"
          -> {"description": "vintage graphic tee", "size": "M", "max_price": 30.0}
      "platform sneakers size 8"
          -> {"description": "platform sneakers", "size": "8", "max_price": None}
    """
    text = query or ""

    size = None
    m = _SIZE_RE.search(text)
    if m:
        size = m.group(1).strip().upper()
        text = text[: m.start()] + " " + text[m.end():]

    max_price = None
    m = _PRICE_RE.search(text) or _DOLLAR_RE.search(text)
    if m:
        max_price = float(m.group(1))
        text = text[: m.start()] + " " + text[m.end():]

    description = re.sub(r"[,;]+", " ", text)
    description = re.sub(r"\s+", " ", description).strip()
    return {"description": description, "size": size, "max_price": max_price}


# ── the empty-search message ──────────────────────────────────────────────────

def _empty_message(parsed: dict) -> str:
    """
    Say what was searched and what the user could change. Re-runs the search
    with one filter dropped to find out which filter is the blocker.
    """
    desc, size, max_price = parsed["description"], parsed["size"], parsed["max_price"]

    searched = f"'{desc}'"
    if size:
        searched += f", size {size}"
    if max_price is not None:
        searched += f", under ${max_price:g}"

    hints = []
    if size and search_listings(desc, None, max_price):
        hints.append(f"drop the size filter (size {size}); there are matches in other sizes")
    if max_price is not None and search_listings(desc, size, None):
        hints.append(f"raise your ${max_price:g} limit; there are matches above that price")
    if not hints:
        hints.append(
            "try different or fewer keywords (the item type alone, like 'jacket' "
            "or 'jeans', is the broadest search)"
        )

    return f"No listings matched {searched}. You could: " + "; or ".join(hints) + "."


# ── planning loop ─────────────────────────────────────────────────────────────

def _next_step(session: dict) -> str:
    """Look at the session and decide what to do next. This is the loop's brain."""
    if not session["parsed"]:
        return "parse"
    if not session["searched"]:
        return "search"
    if not session["search_results"]:
        return "stop_empty"          # THE BRANCH: search came back empty
    if session["selected_item"] is None:
        return "select"
    if session["outfit_suggestion"] is None:
        return "suggest"
    if session["fit_card"] is None:
        return "fit_card"
    return "done"


def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Branch rule: if search_listings returns [], put a message naming what to
    change in session["error"] and return without calling suggest_outfit or
    create_fit_card. Otherwise take the first result as session["selected_item"]
    and continue through suggest_outfit and create_fit_card.

    Check session["error"] first: if it isn't None, the run ended early.
    """
    session = new_session(query, wardrobe)

    count = 0
    while True:
        count += 1
        trace.check_iterations(count)

        step = _next_step(session)

        if step == "parse":
            session["parsed"] = parse_query(session["query"])

        elif step == "search":
            p = session["parsed"]
            session["search_results"] = search_listings(
                p["description"], p["size"], p["max_price"]
            )
            session["searched"] = True

        elif step == "stop_empty":
            session["error"] = _empty_message(session["parsed"])
            return session

        elif step == "select":
            session["selected_item"] = session["search_results"][0]

        elif step == "suggest":
            item = session["selected_item"]          # read back out of the session
            session["suggest_item_id"] = item["id"]  # record what the tool received
            session["outfit_suggestion"] = suggest_outfit(item, session["wardrobe"])

        elif step == "fit_card":
            session["fit_card"] = create_fit_card(
                session["outfit_suggestion"], session["selected_item"]
            )

        else:  # "done"
            return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
