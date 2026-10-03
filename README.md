# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->

FitFindr is a thrifting agent. A user types what they want in plain language,
like "vintage graphic tee under $30", and the agent parses out the item, size,
and price ceiling, searches a file of secondhand listings, and picks the best
match. It then suggests outfits that combine that item with the user's
wardrobe and writes a short social-media caption for the find. If nothing
matches, it stops and tells the user which filter to loosen instead of
generating an outfit for nothing.

---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Finds listings that match a text description, optionally
  filtered by size and a price ceiling, and returns the best matches first.
- **Inputs:** `description` (str, keywords like "vintage graphic tee"),
  `size` (str | None, None skips size filtering), `max_price` (float | None,
  inclusive, None skips price filtering).
- **Returns:** A list of at most `config.SEARCH_RESULT_LIMIT` listing dicts,
  sorted by keyword-overlap score, highest first. Each dict has id, title,
  description, category, style_tags, size, condition, price, colors, brand
  (may be None), platform. Size matching: <YOUR RULE, e.g. case-insensitive
  match against whole size tokens, so "M" matches "S/M" but not "US 9" or "XL">.
  Listings scoring zero keyword matches are dropped.
- **When it has nothing:** Returns `[]` (never None, never an exception).

### `suggest_outfit`

- **What it does:** Suggests one or two outfits combining the thrifted item
  with pieces from the user's wardrobe.
- **Inputs:** `new_item` (dict, one listing as returned by search_listings),
  `wardrobe` (dict with an `items` key holding a list of wardrobe item dicts;
  the list may be empty).
- **Returns:** A non-empty str of outfit suggestions that names specific
  wardrobe pieces by name.
- **When it has nothing:** If `wardrobe["items"]` is empty, returns a non-empty
  str of general styling advice for the item instead (no error, no "").

### `create_fit_card`

- **What it does:** Writes a short social-media-style caption about the find.
- **Inputs:** `outfit` (str, output of suggest_outfit), `new_item` (dict, the
  listing).
- **Returns:** A str of 2-4 sentences that mentions the item, its price, and
  its platform once each, and sounds like a real post.
- **When it has nothing:** If `outfit` is empty or whitespace, returns a
  str message such as "No outfit to caption yet" without calling the model.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

     If `search_listings` returns `[]`, store a message in the session naming what to change (size, price, keywords) and stop without calling `suggest_outfit`.
     Otherwise store the first result as `session["selected_item"]` and continue.

**Branch rule:** If `search_listings` returns `[]`, the loop puts a message in
`session["error"]` that names the search and what to change (drop the size
filter, raise the price limit, or use different keywords), then returns
without calling `suggest_outfit` or `create_fit_card`. Otherwise it selects
the first result as `session["selected_item"]` and continues through
`suggest_outfit` and `create_fit_card`.

**Where it lives:** `agent.py::run_agent`. The branch is the `stop_empty`
step, which `agent.py::_next_step` chooses by reading the session. The
message is built by `agent.py::_empty_message`, which re-runs the search with
one filter dropped to find out which filter was blocking results.

**How the query is parsed:** Regex, in `agent.py::parse_query`, with no model
call. One pattern pulls out the size ("size M"), one pulls out the price
ceiling ("under $30"), and what remains becomes the description.

**What moves through the session:** `query` -> `parsed` (description, size,
max_price) -> `searched` -> `search_results` -> `selected_item` ->
`suggest_item_id` (the id of the item `suggest_outfit` actually received) ->
`outfit_suggestion` -> `fit_card`. `error` is set only when the run ends
early. Each tool's result goes into the session, and the next step reads it
back out, so the state can be printed and checked.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'

  Found:    Graphic Tee — 2003 Tour Bootleg Style — $24.0 on depop

  Outfit:   Hey there! What an amazing find—that bootleg tee has the best lived-in vibe. Here are two ways to style it using your wardrobe:

**The Ultimate Grunge Look:** 
Pair the graphic tee with your baggy straight-leg jeans, and lace up the black combat boots for that effortless 90s edge. Layer your vintage black denim jacket on top, and finish the whole fit with your black crossbody bag. 

**Streetwear Contrast:** 
Tuck the tee into your wide-leg khaki trousers secured with the brown leather belt to balance the boxy fit. Throw your black cropped zip hoodie over your shoulders or wear it unzipped, and step into your chunky white sneakers, grabbing your black crossbody bag to run out the door.

  Fit card: Scored this 2003 tour bootleg tee on depop for $24 and I am never taking it off. It has the absolute best grunge fade and feels like it was stolen straight from the back of a real venue. Can't wait to style this with baggy denim and beat-up combat boots for maximum 90s slouch.

0 model calls this session, 2 served from cache
(.venv) 

```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"

```
[{'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.', 'category': 'tops', 'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'], 'size': 'L', 'condition': 'good', 'price': 24.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'description': 'Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'band tee', 'graphic tee', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 19.0, 'colors': ['grey', 'charcoal'], 'brand': None, 'platform': 'depop'}]
(.venv) 
```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, get_empty_wardrobe, load_listings; item = load_listings()[0]; print(suggest_outfit(item, get_example_wardrobe())); print('-----'); print(suggest_outfit(item, get_empty_wardrobe()))""

```
core! Those 501s are a total holy grail find. Here are two effortless ways to style them using your current wardrobe:

**The Off-Duty Streetwear Look:** Tuck your white ribbed tank top into the Vintage Levi's 501 Jeans — Medium Wash, cinch your waist with the brown leather belt, and layer the oversized grey crewneck sweatshirt on top. Finish the fit with chunky white sneakers and the black crossbody bag for a casual, classic vibe.

**The Edge & Denim Contrast:** Pair the Vintage Levi's 501 Jeans — Medium Wash with the black cropped zip hoodie layered under the vintage black denim jacket for a cool double-denim moment. Lace up your black combat boots and sling the black crossbody bag across your chest to lean into that grungy streetwear aesthetic.
-----
Great find! Those 501s are the holy grail of denim. They pair best with fitted or cropped silhouettes to balance the straight leg, and look amazing with earth tones, crisp whites, and vintage leather.

**Outfit 1: The Downtown Coffee Run**
Tuck a fitted ribbed white tank top into the jeans, layer an oversized forest green corduroy button-down worn open, and slip on some well-worn brown leather loafers or retro sneakers. Add a canvas tote and a simple silver pendant necklace to complete the effortless, cool-girl street style.

**Outfit 2: Retro Coffee & Vinyl**
Pair the denim with a tucked-in, black-and-white striped long-sleeve t-shirt and a cropped black leather biker jacket. Throw on chunky black combat boots and a mustard-yellow beanie for a pop of color that plays off the indigo wash.
(.venv) 
```
$ python -c "import config; config.CACHE_ENABLED = False; from tools import create_fit_card; from utils.data_loader import load_listings; item = load_listings()[0]; [print(create_fit_card('jeans and white sneakers', item), '\n-----') for _ in range(3)]"

```
Absolute score on these vintage Levi's 501s. They've got that perfect broken-in medium wash and fit like an absolute dream. Snagged them on depop for $38.00 and I'm basically going to live in them with my favorite white sneakers all fall. 
-----
Found these vintage Levi's 501 jeans on depop for $38 and I am never taking them off. They have that perfect, broken-in medium wash that looks amazing with just a basic white tee and fresh sneakers. Absolute secondhand gold. 
-----
Scored these medium wash vintage Levi's 501s for $38 on depop and they fit like an absolute dream. The wash has that perfect worn-in 90s vibe without looking try-hard. Just going to throw them on with my beat-up white sneakers and call it a day. 
-----
(.venv) 
---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* I asked Claude to write the three tools in tools.py from
  the starter stubs, and I tested search_listings with
  `search_listings('graphic tee', max_price=30)`.
- *What came back:* Nine results. Only three were graphic tees. The rest were
  a flannel, a polo, cargo pants, and a crewneck sweatshirt. The cause was a
  synonym map that expanded "tee" to "shirt", plus a rule where one matching
  keyword was enough to qualify a listing.
- *What I changed:* I removed the "shirt" synonym and required most of the
  query's keywords to match. A mesh top still slipped through because its
  description said "layering under a graphic tee", so I made keywords qualify
  a listing only when they appear in the title, tags, category, colors, or
  brand. The description now affects ranking only. The search returns exactly
  the three tees. The tradeoff is that phrasings only found in descriptions
  will miss, which is why criterion 1 targets 4 of 5.

**Moment 2**

- *What I asked for:* I tested create_fit_card three times on the same item.
- *What came back:* Three word-for-word identical captions. `TEMPERATURE` in
  config.py was 0.0 (and the cache was on). After I raised it, the captions
  varied, but two read as if the poster was selling the jeans ("I'm listing
  these on depop", "finally listed on my depop").
- *What I changed:* I raised TEMPERATURE to 0.9. I rewrote the caption
  system prompt to say the poster just bought the item, never to write as if
  they're selling it, and to name the platform as where it was found. All
  three new captions read as buyers.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
