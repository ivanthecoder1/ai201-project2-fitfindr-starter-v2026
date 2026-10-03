"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import re

import config  # noqa: F401 — you'll use this in search_listings
from generate import generate
from utils.data_loader import load_listings


# ── Helpers ───────────────────────────────────────────────────────────────────

_STOPWORDS = {
    "a", "an", "the", "in", "on", "for", "and", "or", "with", "of", "to",
    "me", "i", "my", "want", "looking", "find", "show", "under", "below",
    "size", "max", "less", "than", "something", "some",
}

# Query word -> extra words it should also match in a listing.
_SYNONYMS = {
    "tee": {"tshirt"},
    "tshirt": {"tee"},
    "sneakers": {"trainers"},
    "sneaker": {"trainers"},
}


def _tokens(text: str) -> list[str]:
    """Lowercase alphanumeric tokens: "S/M" -> ["s", "m"]."""
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def _norm(word: str) -> str:
    """Crude plural stripping so "jeans" and "jean" match."""
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def _keywords(description: str) -> set[str]:
    return {
        _norm(t)
        for t in _tokens(description)
        if t not in _STOPWORDS and len(t) > 1
    }


def _size_matches(wanted: str, listing_size: str) -> bool:
    """
    Whole-token match, case-insensitive. Every token of the wanted size must
    appear as a whole token in the listing's size.
      "M"       matches "S/M", "M", "M/L"   but not "XM", "US 9"
      "S"       matches "S", "S/M"          but not "XS", "XL", "US 9"
      "W30 L30" matches "W30 L30"
      "9"       matches "US 9"
    """
    wanted_tokens = set(_tokens(wanted))
    if not wanted_tokens:
        return True
    return wanted_tokens <= set(_tokens(listing_size))


def _score(listing: dict, words: set[str]) -> tuple[int, int]:
    """
    Returns (distinct keywords matched, weighted score).
    A keyword only counts as matched if it appears in a structured field.
    The description adds to the score for ranking but can't qualify a listing
    on its own, because descriptions mention other items ("under a graphic tee").
    """
    # (weight, text, counts_toward_match)
    fields = [
        (3, listing.get("title"), True),
        (2, " ".join(listing.get("style_tags") or []), True),
        (2, listing.get("category"), True),
        (1, " ".join(listing.get("colors") or []), True),
        (1, listing.get("brand"), True),  # brand is often None
        (1, listing.get("description"), False),
    ]
    field_sets = [
        (weight, {_norm(t) for t in _tokens(text or "")}, counts)
        for weight, text, counts in fields
    ]
    matched, score = 0, 0
    for w in words:
        candidates = {w} | {_norm(s) for s in _SYNONYMS.get(w, set())}
        hit = False
        for weight, field_words, counts in field_sets:
            if candidates & field_words:
                score += weight
                if counts:
                    hit = True
        if hit:
            matched += 1
    return matched, score


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search listings by keyword description, optional size, optional price cap.

    Matching rules:
      - max_price is inclusive; None skips the price filter.
      - size is a case-insensitive whole-token match; None skips it.
      - A listing must contain every keyword (or all but one when the query
        has 3+ keywords). Results are sorted by weighted score, best first.

    Returns up to config.SEARCH_RESULT_LIMIT listing dicts.
    Returns [] when nothing matches (never None, never an exception).
    """
    words = _keywords(description)
    if not words:
        return []

    needed = len(words) if len(words) <= 2 else len(words) - 1
    scored = []

    for listing in load_listings():
        if max_price is not None and listing["price"] > max_price:
            continue
        if size is not None and not _size_matches(size, listing.get("size") or ""):
            continue
        matched, score = _score(listing, words)
        if matched >= needed:
            scored.append((score, listing))

    # sorted() is stable, so ties keep file order
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [listing for _, listing in scored[: config.SEARCH_RESULT_LIMIT]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

_OUTFIT_SYSTEM = (
    "You are a friendly thrift-store stylist. Be specific and concise. "
    "Suggest one or two outfits, each as a short paragraph."
)


def _describe_item(item: dict) -> str:
    return (
        f"{item.get('title')} ({item.get('category')}, size {item.get('size')}, "
        f"colors: {', '.join(item.get('colors') or [])}, "
        f"style: {', '.join(item.get('style_tags') or [])}). "
        f"{item.get('description', '')}"
    )


def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Returns a non-empty string of outfit suggestions. With an empty wardrobe,
    returns general styling advice instead.
    """
    items = (wardrobe or {}).get("items") or []

    if not items:
        prompt = (
            f"I just found this thrifted piece: {_describe_item(new_item)}\n\n"
            "I haven't told you what's in my wardrobe, so give general "
            "styling advice: what kinds of pieces and colors pair well with "
            "it, and one or two example outfits."
        )
    else:
        lines = [
            f"- {w.get('name')} ({w.get('category')}; "
            f"colors: {', '.join(w.get('colors') or [])}; "
            f"style: {', '.join(w.get('style_tags') or [])}"
            + (f"; {w['notes']}" if w.get("notes") else "")
            + ")"
            for w in items
        ]
        prompt = (
            f"I just found this thrifted piece: {_describe_item(new_item)}\n\n"
            "Here is my wardrobe:\n" + "\n".join(lines) + "\n\n"
            "Suggest one or two outfits that combine the new piece with "
            "items I already own. Name the wardrobe pieces exactly as listed."
        )

    result = generate(prompt, system=_OUTFIT_SYSTEM)
    # Never return "" even if the model comes back empty
    return result or "No outfit suggestions came back. Try again in a moment."


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

_CAPTION_SYSTEM = (
    "You write short social media captions for thrift finds. The poster just "
    "BOUGHT this item secondhand and is showing off their find. Never write "
    "as if they are selling or listing it. Sound like a real person posting, "
    "not a product description. Write 2 to 4 sentences. Mention the item, its "
    "price, and the platform once each, with the platform as where it was "
    "found or bought (for example 'found on depop'). Be specific about the "
    "vibe. No hashtag lists, no emoji walls."
)


def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Returns a 2-4 sentence caption. If `outfit` is empty or whitespace,
    returns a message instead of calling the model.
    """
    if not outfit or not outfit.strip():
        return "No outfit to caption yet. Get outfit suggestions first."

    prompt = (
        f"Item: {new_item.get('title')}\n"
        f"Price: ${new_item.get('price'):.2f}\n"
        f"Platform: {new_item.get('platform')}\n\n"
        f"Outfit idea:\n{outfit}\n\n"
        "Write the caption."
    )
    return generate(prompt, system=_CAPTION_SYSTEM)