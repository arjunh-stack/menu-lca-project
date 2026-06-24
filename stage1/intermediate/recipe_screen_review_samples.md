# Layer 25 — Recipe-test screen review samples

**Two-model classification on 113,925 canonicals**

- Gemini Flash judged all canonicals (KEEP / DROP).
- DeepSeek V4 Pro re-judged the 30,879 Gemini-DROPs (validation pass).
- KEEPs are trusted on Gemini alone since over-keeping is the safe direction.

| Bucket | Count | % | Sum menu rows |
|---|---|---|---|
| GEMINI_KEEP | 82,606 | 72.5% | 1,025,066 |
| BOTH_DROP | 20,904 | 18.3% | 78,888 |
| GEMINI_DROP_PRO_RESCUE | 9,975 | 8.8% | 59,804 |
| HAS_ERROR | 440 | 0.4% | 1,880 |

---

## BOTH_DROP — both models said DROP (drop candidates)

These are safe to drop — both models agreed. Spot-check below.

### Top 30 highest-count BOTH_DROP

| count | canonical | gemini reason | deepseek reason |
|---|---|---|---|
| 1497 | `chicken mixed` | vague | vague |
| 1469 | `burger dave` | possessive | possessive |
| 1006 | `bone wings` | generic | nonexistent |
| 810 | `tenders` | generic | generic |
| 785 | `burger jack` | vague | possessive |
| 546 | `friendly gluten original pancakes` | possessive | vague |
| 511 | `pizza sub wrap` | vague | vague-combo |
| 509 | `bowl pizza sub` | vague | vague-combo |
| 436 | `bowl famous spicy` | vague | vague |
| 404 | `feast sandwich` | vague | vague |
| 370 | `bbq house order ribs` | vague | instruction |
| 370 | `chipotle honey order ribs` | vague | instruction |
| 370 | `dry order ribs rub texas` | vague | instruction |
| 353 | `bun free gluten` | addon | modifier |
| 350 | `order original ribs` | addon | instruction |
| 349 | `bowl high protein` | vague | vague |
| 341 | `bowl paleo salad` | vague | vague |
| 339 | `bowl salad vegetarian` | vague | vague |
| 320 | `chick melt tater` | gibberish | ambiguous |
| 313 | `special stickball sub` | vague | unrecognizable |
| 311 | `chicken mike philly sub` | possessive | possessive |
| 308 | `four number sub` | code | code |
| 303 | `cancro special sub` | possessive | person |
| 286 | `house salad` | generic | vague-modifier |
| 282 | `jalape peppers` | gibberish | ingredient-only |
| 266 | `fillet fish` | generic | generic |
| 252 | `bowl sandwich warm` | vague | gibberish |
| 250 | `bowl salad warm` | vague | vague |
| 250 | `bowl mac soup warm` | vague | vague |
| 249 | `sour sweet` | vague | sauce |

### Random samples by gemini reason

#### `gemini_reason = gibberish` (8,008 drops)

| count | canonical | gemini | deepseek |
|---|---|---|---|
| 320 | `chick melt tater` | gibberish | ambiguous |
| 282 | `jalape peppers` | gibberish | ingredient-only |
| 195 | `baking gourmet pizza required vegetarian` | gibberish | instruction |
| 194 | `baking cowboy pizza required` | gibberish | instruction |
| 193 | `artichoke bacon baking chicken pizza required` | gibberish | instruction |
| 1 | `bao beef chicken chops com crushed grilled pork ribs rice tam` | gibberish | fragmented |
| 2 | `burger con fritas papas solas` | gibberish | gibberish |
| 1 | `cake chimney panini pork pulled smoked` | gibberish | incoherent |
| 1 | `burrito cochikuina` | gibberish | unrecognizable |
| 58 | `out pizza veg` | gibberish | vague |
| 2 | `chop korma` | gibberish | unclear |
| 1 | `all astice neri pasta spaghetti` | gibberish | gibberish |
| 1 | `dos para persona` | gibberish | generic |
| 2 | `burger che cheeseburger` | gibberish | gibberish |
| 1 | `alc asada enchilada fl` | gibberish | code |

#### `gemini_reason = vague` (6,888 drops)

| count | canonical | gemini | deepseek |
|---|---|---|---|
| 1497 | `chicken mixed` | vague | vague |
| 785 | `burger jack` | vague | possessive |
| 511 | `pizza sub wrap` | vague | vague-combo |
| 509 | `bowl pizza sub` | vague | vague-combo |
| 436 | `bowl famous spicy` | vague | vague |
| 2 | `king platter` | vague | generic |
| 3 | `deluxe sakura` | vague | vague |
| 1 | `madison sandwich` | vague | person |
| 6 | `express korner pizza` | vague | not-dish |
| 2 | `chafing combination dish seafood` | vague | generic |
| 1 | `noodles starch wheat` | vague | generic |
| 1 | `cup mango traditional` | vague | generic |
| 7 | `bowl tyler` | vague | person |
| 1 | `diavolo dish fra spicy` | vague | generic |
| 1 | `club game` | vague | unrelated |

#### `gemini_reason = possessive` (3,633 drops)

| count | canonical | gemini | deepseek |
|---|---|---|---|
| 1469 | `burger dave` | possessive | possessive |
| 546 | `friendly gluten original pancakes` | possessive | vague |
| 311 | `chicken mike philly sub` | possessive | possessive |
| 303 | `cancro special sub` | possessive | person |
| 188 | `alex burger fe santa` | possessive | person |
| 1 | `mark reuben` | possessive | possessive |
| 2 | `joaco pizza` | possessive | possessive |
| 1 | `big johnny sandwich` | possessive | person |
| 5 | `brews mr original pork pulled sandwich` | possessive | possessive |
| 1 | `lee melt patty sandwich` | possessive | possessive |
| 14 | `noah pizza` | possessive | possessive |
| 1 | `benedict grandma` | possessive | person |
| 1 | `christy jimmy sandwich` | possessive | proper-name |
| 4 | `chicken molly wrap` | possessive | proper |
| 2 | `anaya fettuccine grilled shrimp` | possessive | possessive |

#### `gemini_reason = generic` (1,475 drops)

| count | canonical | gemini | deepseek |
|---|---|---|---|
| 1006 | `bone wings` | generic | nonexistent |
| 810 | `tenders` | generic | generic |
| 286 | `house salad` | generic | vague-modifier |
| 266 | `fillet fish` | generic | generic |
| 249 | `chicken vegetables` | generic | generic |
| 1 | `instant noodles pasta sausage` | generic | unrecognizable |
| 1 | `pot skewers` | generic | generic |
| 2 | `orden tacos` | generic | vague |
| 1 | `set tofu` | generic | unrecognizable |
| 73 | `beef chicken` | generic | generic |
| 2 | `guacamole pint` | generic | quantity |
| 1 | `plate shrimp` | generic | generic |
| 1 | `clams only` | generic | instruction |
| 7 | `beef chicken pork` | generic | generic |
| 18 | `chicken potato` | generic | generic |

#### `gemini_reason = combo` (330 drops)

| count | canonical | gemini | deepseek |
|---|---|---|---|
| 246 | `chicken feast sandwiches steakburgers` | combo | vague-combo |
| 107 | `feast mac or sandwich soup` | combo | unrecognizable |
| 104 | `feast mac or soup` | combo | vague |
| 104 | `bacon biscuits gravy or sausage` | combo | choice |
| 77 | `cheese chicken honey mac pasta pepper tenders` | combo | vague |
| 1 | `biscuit butter cococash compote fruit` | combo | gibberish |
| 8 | `chips guacamole taco` | combo | gibberish |
| 1 | `beef filet mignon rice rock roll white` | combo | vague |
| 1 | `brown burrito golden pancakes strawberry` | combo | nonsense |
| 1 | `choice fillet rice salmon vegetable` | combo | generic |
| 1 | `buffalo drink pizzas ten wings` | combo | combo |
| 1 | `braised chicken mandarin or pork` | combo | vague |
| 1 | `beans charro cilantro corn cup one onions tacos` | combo | ingredients |
| 1 | `burger eggs toast` | combo | generic |
| 1 | `breast chicken hand noodles pasta pulled` | combo | gibberish |

#### `gemini_reason = addon` (298 drops)

| count | canonical | gemini | deepseek |
|---|---|---|---|
| 353 | `bun free gluten` | addon | modifier |
| 350 | `order original ribs` | addon | instruction |
| 103 | `bacon sliced thick` | addon | generic |
| 55 | `hummus pint` | addon | container |
| 40 | `free gluten vegetarian` | addon | tag |
| 1 | `cheese cut pizza to` | addon | gibberish |
| 2 | `bacon order taco` | addon | instruction |
| 1 | `cilantro extra onion taco` | addon | addon |
| 1 | `no rice salad spring` | addon | instruction |
| 1 | `extra huwaiian pizza` | addon | add-on |
| 1 | `cueritos flautas sin` | addon | instruction |
| 2 | `build calzone` | addon | instruction |
| 13 | `order sirloin taco` | addon | instruction |
| 1 | `barbecue quart sauce` | addon | quantity |
| 1 | `additional pancake` | addon | add-on |

#### `gemini_reason = code` (256 drops)

| count | canonical | gemini | deepseek |
|---|---|---|---|
| 308 | `four number sub` | code | code |
| 30 | `aac roll` | code | vague |
| 14 | `bowl cyob` | code | gibberish |
| 13 | `roll stp sushi` | code | code |
| 10 | `burger jcw` | code | vague |
| 1 | `va wrap` | code | vague |
| 1 | `burger dmcb` | code | gibberish |
| 2 | `dk pizza` | code | vague |
| 4 | `fs kan strips` | code | gibberish |
| 1 | `gyoza tc` | code | abbrev |
| 1 | `bowl mtc` | code | code |
| 1 | `plate sotx` | code | acronym |
| 1 | `aboca lunch plt sandwich` | code | gibberish |
| 5 | `hr spicy tuna` | code | code |
| 1 | `ch entree pasta temp` | code | unrecognizable |

#### `gemini_reason = regional` (15 drops)

| count | canonical | gemini | deepseek |
|---|---|---|---|
| 1 | `burger toulouse` | regional | regional |
| 1 | `fairhaven scramble` | regional | local |
| 1 | `galbraith quesadillas` | regional | possessive |
| 1 | `sandwich tuckahoe` | regional | location |
| 1 | `gyro jersey` | regional | location |
| 1 | `peppers sausage sweet vermont` | regional | vague |
| 1 | `la najera tortellini` | regional | proper |
| 1 | `camp north pizza` | regional | generic |
| 1 | `nizza pizza` | regional | unknown |
| 1 | `bao memphis` | regional | vague |
| 1 | `arlington burrito` | regional | local |
| 1 | `burger riverbend` | regional | local |
| 1 | `bao yorker` | regional | vague |
| 1 | `effingham sandwich` | regional | location |
| 1 | `burger rowdy` | regional | unknown |

#### `gemini_reason = special` (1 drops)

| count | canonical | gemini | deepseek |
|---|---|---|---|
| 1 | `burger junkie special` | special | vague |

---

## GEMINI_DROP_PRO_RESCUE — Gemini said DROP, Pro said KEEP

Pro's stronger reasoning rescued these from Gemini's over-aggression. Default: KEEP them.

### Top 30 highest-count rescues

| count | canonical | gemini said DROP because | deepseek said KEEP because |
|---|---|---|---|
| 1332 | `bowl menu power veggie` | vague | branded |
| 1211 | `bowl tuna` | generic | dish |
| 789 | `bowl patty veggie` | vague | recognizable |
| 759 | `caramel chocolate hot` | vague | recognizable |
| 748 | `avocado classic grilled oz sirloin` | vague | steak |
| 704 | `lover pizza veggie` | vague | dish |
| 674 | `bowl menu power` | vague | branded |
| 579 | `ew pad see` | gibberish | dish |
| 489 | `baconator burger son` | possessive | branded |
| 489 | `asiago chicken classic club ranch` | gibberish | recognizable |
| 487 | `asiago club ranch spicy` | gibberish | recognizable |
| 487 | `bacon big cheddar chicken grilled` | gibberish | recognizable |
| 486 | `asiago club grilled ranch` | gibberish | recognizable |
| 485 | `peas shrimp snow` | gibberish | recognizable |
| 478 | `cheese croissan egg ham wich` | gibberish | sandwich |
| 477 | `breast sub turkey` | generic | sandwich |
| 472 | `chicken peas snow` | gibberish | stir-fry |
| 384 | `sub super` | generic | sandwich |
| 384 | `fried house rice special` | vague | friedrice |
| 369 | `bean black chicken sauce` | generic | recognizable |
| 366 | `chicken mushroom` | generic | minimal |
| 337 | `chick cool fil wrap` | gibberish | branded |
| 315 | `favorite jersey shore sub` | possessive | branded |
| 314 | `famous mike philly sub` | possessive | branded |
| 308 | `roll vegetable` | generic | dish |
| 300 | `coney pound quarter` | vague | hotdog |
| 279 | `house lo mein special` | vague | dish |
| 277 | `french original our toast` | gibberish | dish |
| 270 | `moo shrimp shu` | gibberish | dish |
| 263 | `belgian friendly gluten waffle` | vague | waffle |

### Random sample of rescues (30)

| count | canonical | gemini | gem reason | deepseek | ds reason |
|---|---|---|---|---|---|
| 1332 | `bowl menu power veggie` | DROP | vague | KEEP | branded |
| 1211 | `bowl tuna` | DROP | generic | KEEP | dish |
| 789 | `bowl patty veggie` | DROP | vague | KEEP | recognizable |
| 759 | `caramel chocolate hot` | DROP | vague | KEEP | recognizable |
| 748 | `avocado classic grilled oz sirloin` | DROP | vague | KEEP | steak |
| 704 | `lover pizza veggie` | DROP | vague | KEEP | dish |
| 674 | `bowl menu power` | DROP | vague | KEEP | branded |
| 579 | `ew pad see` | DROP | gibberish | KEEP | dish |
| 489 | `baconator burger son` | DROP | possessive | KEEP | branded |
| 489 | `asiago chicken classic club ranch` | DROP | gibberish | KEEP | recognizable |
| 2 | `combination curry lo mein pasta` | DROP | combo | KEEP | fusion-noodle |
| 3 | `con pasta vegetales` | DROP | vague | KEEP | pasta |
| 1 | `meatballs pasta vegan vegetarian` | DROP | vague | KEEP | vegan |
| 1 | `cantinero molcajete super` | DROP | vague | KEEP | recognizable |
| 1 | `arroz de loca pupusa` | DROP | gibberish | KEEP | ethnic |
| 1 | `bento fried fry kimchi stir tofu` | DROP | combo | KEEP | bento |
| 1 | `marinara pasta spicy` | DROP | gibberish | KEEP | known-dish |
| 1 | `green meatball peppers sub` | DROP | gibberish | KEEP | ingredients |
| 1 | `garlic ricotta slice spinach` | DROP | generic | KEEP | pizza |
| 1 | `land molcajete sea` | DROP | vague | KEEP | recognizable |
| 1 | `aguachile bichi rosa tropical verde` | DROP | gibberish | KEEP | ethnic |
| 4 | `down pancake pineapple solo upside` | DROP | gibberish | KEEP | recognizable-dish |
| 1 | `goong shee shu` | DROP | gibberish | KEEP | ethnic |
| 2 | `combination fry noodle pasta plate stir` | DROP | generic | KEEP | stirfry |
| 8 | `chicken de fajita fajitas pollo` | DROP | gibberish | KEEP | fajita |
| 2 | `de mofongo platano` | DROP | gibberish | KEEP | mofongo |
| 2 | `crab fried legs` | DROP | generic | KEEP | recognizable |
| 5 | `ed garlic saut spinach` | DROP | gibberish | KEEP | sautéed-spinach |
| 1 | `buffalo burger meets south west` | DROP | vague | KEEP | dish |
| 1 | `focaccia hot pollo pressed sandwich` | DROP | gibberish | KEEP | sandwich |
