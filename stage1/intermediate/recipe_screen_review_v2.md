# Layer 25 — Recipe-test 2-model review (v2)

**Two-model classification on 113,925 canonicals.**

- Gemini Flash judged all canonicals (KEEP / DROP).
- DeepSeek V4 Pro re-judged BOTH the Gemini-DROPs AND the Gemini-KEEPs.
- All disagreements surfaced — no model is auto-trusted.

## Bucket sizes

| Bucket | Count | % | Menu rows | Recommended action |
|---|---|---|---|---|
| BOTH_KEEP | 68,888 | 60.5% | 951,195 | KEEP |
| PRO_RESCUE | 9,975 | 8.8% | 59,804 | KEEP (Pro vetoed Gemini DROP) |
| BOTH_DROP | 20,904 | 18.3% | 78,888 | DROP |
| PRO_VETO | 13,696 | 12.0% | 73,829 | **SPOT-CHECK** (Pro vetoed Gemini KEEP — NEW) |
| HAS_ERROR | 462 | 0.4% | 1,922 | KEEP (safe) |

**If you accept all proposed drops (BOTH_DROP + PRO_VETO):**
- Canonicals dropped: 34,600
- Menu rows dropped: 152,717
- Projected v19 canonicals: 79,325

---

## PRO_VETO — Gemini said KEEP, Pro said DROP

**These are the new drop candidates that need your spot-check.** Pro thinks these names don't pass the recipe-search test even though Gemini did.

### Top 30 highest-count PRO_VETO

| count | canonical | gemini said KEEP because | pro said DROP because |
|---|---|---|---|
| 4658 | `cali fresh sandwich steak sub` | dish | branded-proper-noun |
| 4615 | `baja jack sandwich steak sub` | dish | branded-proper-noun |
| 1146 | `cheese egg` | generic | vague |
| 1093 | `bowl meat mozza` | dish | vague |
| 1092 | `bowl meats supreme` | dish | vague |
| 808 | `gai goo moo pan` | regional | unrecognizable-fragment |
| 702 | `pancakes` | dish | generic |
| 677 | `bowl keto salad` | dish | vague |
| 512 | `lover pepperoni pizza` | dish | vague-modifier |
| 459 | `burger meat whataburger` | branded | unrecognizable |
| 458 | `burger whataburger` | branded | unrecognizable |
| 458 | `burger meat whataburger whatameal` | branded | unrecognizable |
| 390 | `pasta spaghetti` | generic | vague |
| 378 | `fresh fruit seasonal` | dish | vague |
| 314 | `big cheese kahuna steak sub` | dish | vague |
| 296 | `beef pound roast` | dish | vague |
| 296 | `beef cheddar classic` | combo | vague |
| 294 | `beef cheddar pound` | combo | vague |
| 282 | `fried pasta rice` | combo | unrecognizable |
| 278 | `bacon omelette temptation` | dish | vague |
| 269 | `breakfast feast pancakes` | dish | vague |
| 269 | `bowl burrito chicken mexico` | combo | nonspecific |
| 267 | `breakfast feast french toast` | dish | vague |
| 264 | `cheeseburger mega monster` | dish | vague |
| 262 | `breakfast feast waffles` | dish | vague |
| 261 | `bacon creations feast pancake` | combo | vague |
| 258 | `flatbread pizza salad` | combo | combo |
| 257 | `flatbread pizza sandwich` | combo | combo |
| 257 | `creations feast pancake sausage` | combo | vague |
| 256 | `bbq cowboy` | dish | vague |

### Random samples by Pro's DROP reason

#### `pro_reason = vague` (5,582 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1146 | `cheese egg` | generic | vague |
| 1093 | `bowl meat mozza` | dish | vague |
| 1092 | `bowl meats supreme` | dish | vague |
| 677 | `bowl keto salad` | dish | vague |
| 390 | `pasta spaghetti` | generic | vague |
| 45 | `corn taco` | dish | vague |
| 1 | `burrito meat mexico` | combo | vague |
| 11 | `burger jungle` | dish | vague |
| 1 | `indian pizza trail` | dish | vague |
| 1 | `hawaiian veggie` | dish | vague |
| 1 | `blossom fried rice` | dish | vague |
| 2 | `alabama burger monster` | dish | vague |
| 1 | `bowl crunch mountain` | dish | vague |
| 1 | `country hill sausage texas` | regional | vague |
| 1 | `krab salad super` | dish | vague |

#### `pro_reason = generic` (1,144 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 702 | `pancakes` | dish | generic |
| 195 | `cashew nut` | generic | generic |
| 182 | `broccoli steamed` | dish | generic |
| 177 | `breakfast filets` | dish | generic |
| 166 | `bowl chicken` | dish | generic |
| 2 | `mex sausage` | generic | generic |
| 3 | `assortment sashimi` | dish | generic |
| 1 | `grilled noodles shrimp steamed` | dish | generic |
| 1 | `beef ham roast specialty sub turkey` | combo | generic |
| 1 | `fresh oyster` | generic | generic |
| 1 | `bowl meatloaf potato` | dish | generic |
| 4 | `noodle soup tofu vegetable` | dish | generic |
| 2 | `orzo pasta` | dish | generic |
| 2 | `ham lunch sandwich` | dish | generic |
| 2 | `fried waffle` | dish | generic |

#### `pro_reason = unrecognizable` (811 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 459 | `burger meat whataburger` | branded | unrecognizable |
| 458 | `burger whataburger` | branded | unrecognizable |
| 458 | `burger meat whataburger whatameal` | branded | unrecognizable |
| 282 | `fried pasta rice` | combo | unrecognizable |
| 253 | `mac salad soup` | combo | unrecognizable |
| 1 | `noodle pork pot tagine` | combo | unrecognizable |
| 2 | `chicken pasta penne toriado` | dish | unrecognizable |
| 1 | `stew yam` | dish | unrecognizable |
| 2 | `broiled captains platter steak` | combo | unrecognizable |
| 1 | `dhannia hara kumb` | regional | unrecognizable |
| 2 | `bean curd pasta stick` | combo | unrecognizable |
| 1 | `kush master sandwich` | dish | unrecognizable |
| 1 | `famous fish fry saz tavern` | dish | unrecognizable |
| 1 | `las torta vueltas` | regional | unrecognizable |
| 1 | `brisket chopped sandwich sausage` | dish | unrecognizable |

#### `pro_reason = gibberish` (567 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 216 | `chicken fried pasta rice` | combo | gibberish |
| 191 | `burger cheeseburger texas` | dish | gibberish |
| 187 | `fried pasta rice shrimp` | combo | gibberish |
| 130 | `beyond burger wraptor` | branded | gibberish |
| 89 | `don sushi unagi` | regional | gibberish |
| 1 | `beef chamoula plate souvlaki` | regional | gibberish |
| 3 | `curry fried pasta rice shrimp thai` | combo | gibberish |
| 2 | `curry fried seafood stir vp` | dish | gibberish |
| 1 | `andprosciutto asparagus grilled` | dish | gibberish |
| 8 | `burrito chimichanga fajita` | combo | gibberish |
| 1 | `arroz fritas papas pollo` | combo | gibberish |
| 1 | `bacon barbecue burger cheeseburger qweenss` | burger | gibberish |
| 3 | `beef grilled pork` | combo | gibberish |
| 2 | `asian fried pasta pineapple rice` | combo | gibberish |
| 1 | `camaron de lo mein` | dish | gibberish |

#### `pro_reason = combo` (372 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 258 | `flatbread pizza salad` | combo | combo |
| 257 | `flatbread pizza sandwich` | combo | combo |
| 229 | `burger whataburger whatameal` | branded | combo |
| 229 | `sandwich whatachick whatameal` | branded | combo |
| 229 | `chicken grilled sandwich whatameal` | branded | combo |
| 1 | `beans beef cheese enchilada refried rice` | combo | combo |
| 2 | `chicken sandwich smoked wings` | combo | combo |
| 1 | `beef brisket chicken homemade leg link quarter` | dish | combo |
| 1 | `chicken flatbread pizza southwest wings` | combo | combo |
| 1 | `beef sandwich soup` | combo | combo |
| 2 | `beef grilled jasmine rice shrimp steam` | combo | combo |
| 1 | `dirty etouffee leg rice shrimp turkey` | dish | combo |
| 1 | `burrito one quesadilla taco` | combo | combo |
| 1 | `bass chilean sea shrimp` | dish | combo |
| 1 | `chimichanga enchilada pork tamal` | combo | combo |

#### `pro_reason = unclear` (251 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 42 | `cheese cheetos crunchy hot` | dish | unclear |
| 40 | `bun taco` | dish | unclear |
| 22 | `bfg burger pound` | dish | unclear |
| 20 | `burger cheeseburger gyro` | combo | unclear |
| 16 | `burger chicken out` | dish | unclear |
| 10 | `crawfish fried pasta rice` | combo | unclear |
| 1 | `chicken sandwich taquito` | combo | unclear |
| 1 | `chow foo fried rice style` | dish | unclear |
| 1 | `egg noodle quall roast` | dish | unclear |
| 1 | `calazone ll pepe pizza` | dish | unclear |
| 1 | `pasta ravioli spanish` | dish | unclear |
| 3 | `beef imperial shrimp` | combo | unclear |
| 3 | `classic egg oh toast` | combo | unclear |
| 1 | `coctel menudo` | regional | unclear |
| 1 | `camarones popeye` | dish | unclear |

#### `pro_reason = proprietary` (241 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 44 | `pasta voodoo` | dish | proprietary |
| 21 | `fat maverick sandwich` | dish | proprietary |
| 21 | `fat gorbies sandwich` | dish | proprietary |
| 21 | `fat sandwich slob` | dish | proprietary |
| 21 | `fat sandwich wondergem` | dish | proprietary |
| 6 | `classic pizza red robbers roost sauce` | dish | proprietary |
| 2 | `pizza specialty warpath` | dish | proprietary |
| 1 | `croisalmon sandwich` | dish | proprietary |
| 2 | `cheesesteak hammerhead sandwich` | dish | proprietary |
| 1 | `afterburner burger` | dish | proprietary |
| 3 | `lucky roll sushi thai` | dish | proprietary |
| 2 | `el fajita ranchito` | regional | proprietary |
| 1 | `curry mongkolchai` | regional | proprietary |
| 3 | `brooklyn nonna pizza square` | dish | proprietary |
| 1 | `gemini pizza vegan` | vegan | proprietary |

#### `pro_reason = vague-modifier` (205 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 512 | `lover pepperoni pizza` | dish | vague-modifier |
| 173 | `bowl brown hash scramble` | combo | vague-modifier |
| 55 | `burrito lunch` | dish | vague-modifier |
| 38 | `burrito epic fresh guacamole` | dish | vague-modifier |
| 27 | `bbq plate` | dish | vague-modifier |
| 5 | `chic filet spicy sub` | dish | vague-modifier |
| 2 | `cheese craft grilled sandwich` | dish | vague-modifier |
| 1 | `cheesesteak signature` | dish | vague-modifier |
| 3 | `chicken club sandwich yummy` | dish | vague-modifier |
| 1 | `bean cheese nachos nino` | combo | vague-modifier |
| 5 | `pepperoni pizza presto` | dish | vague-modifier |
| 2 | `deluxe mixed vegetable vg` | dish | vague-modifier |
| 1 | `bowl demeter` | dish | vague-modifier |
| 1 | `benedict meat` | dish | vague-modifier |
| 1 | `buffalo cauliflower pizza vegan vibration` | dish | vague-modifier |

#### `pro_reason = proper-noun` (190 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 30 | `club logan sandwich` | dish | proper-noun |
| 27 | `choice juliet pizza` | dish | proper-noun |
| 14 | `michelangelo pasta tortellini` | dish | proper-noun |
| 6 | `calzone chicago fire` | dish | proper-noun |
| 6 | `apollo mediterranean pizza` | dish | proper-noun |
| 1 | `campesino el steak` | dish | proper-noun |
| 1 | `ceviche japanese jc` | combo | proper-noun |
| 3 | `caramelized down hill kalamata meatball mushrooms olives onions peppers roasted sausage wild` | dish | proper-noun |
| 2 | `meatball nonnie sub` | dish | proper-noun |
| 3 | `la patrona torta` | regional | proper-noun |
| 2 | `fajita las rocas trio` | dish | proper-noun |
| 2 | `kellie quesadilla shrimp` | combo | proper-noun |
| 3 | `basil caramelized extra kalamata merritt oil olive olives onions pkwy prosciutto virgin` | dish | proper-noun |
| 1 | `burrito chepe` | regional | proper-noun |
| 1 | `chicken reginas` | dish | proper-noun |

#### `pro_reason = incoherent` (189 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 50 | `pasta tofu yakisoba` | dish | incoherent |
| 23 | `bacon burger cheese pizza` | dish | incoherent |
| 17 | `bbq fried pasta pork rice` | combo | incoherent |
| 17 | `beef chow fun mei pasta` | dish | incoherent |
| 12 | `filet mignon salmon` | dish | incoherent |
| 4 | `chicken eggroll entree grilled` | combo | incoherent |
| 3 | `fried pasta rice tom yum` | combo | incoherent |
| 1 | `cheese chicken platter steak` | combo | incoherent |
| 5 | `beef ribs tempura teriyaki vegetable` | combo | incoherent |
| 1 | `chicken spiedini steak` | dish | incoherent |
| 4 | `chicken or sandwich southwest wrap` | combo | incoherent |
| 1 | `ball fish noodles pasta pulled` | dish | incoherent |
| 1 | `beef casserole fried ginger onion stir` | dish | incoherent |
| 5 | `eggs wings` | combo | incoherent |
| 1 | `chirashi donburi pasta` | combo | incoherent |

#### `pro_reason = ambiguous` (184 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 244 | `burrito egg normous` | burrito | ambiguous |
| 177 | `club sandwich steak sub` | combo | ambiguous |
| 28 | `tenders wings` | combo | ambiguous |
| 23 | `chicken pieces seven spicy wings` | combo | ambiguous |
| 18 | `chow fun mei pasta shrimp` | dish | ambiguous |
| 1 | `calzone chicken feta grilled mozzarella spinach stromboli` | dish | ambiguous |
| 1 | `beef beyond ltt taco` | dish | ambiguous |
| 3 | `classic pizza york` | dish | ambiguous |
| 1 | `beef chicken noodle pasta` | combo | ambiguous |
| 1 | `flank pizza steak` | dish | ambiguous |
| 2 | `buff chowmein` | regional | ambiguous |
| 2 | `burger chicken crispy fried sandwich spicy` | dish | ambiguous |
| 1 | `garlic grate wings` | dish | ambiguous |
| 1 | `chicken steak taco torta` | combo | ambiguous |
| 2 | `reuben salad sandwich` | dish | ambiguous |

#### `pro_reason = unknown` (153 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 36 | `memphian sandwich` | regional | unknown |
| 34 | `border bowl grilled steak` | dish | unknown |
| 12 | `roll sounder sushi` | dish | unknown |
| 11 | `chicken cremora` | dish | unknown |
| 11 | `apollo fish` | regional | unknown |
| 1 | `platter shawarmini` | dish | unknown |
| 1 | `chicken lazatdar` | regional | unknown |
| 2 | `ellington meatloaf` | dish | unknown |
| 1 | `roll suffolk` | regional | unknown |
| 3 | `roll unplugged` | dish | unknown |
| 1 | `bluebonnet roll sushi` | dish | unknown |
| 2 | `chicken mawal style` | regional | unknown |
| 3 | `backfire burger` | dish | unknown |
| 1 | `sausage sheriff taco wrap` | dish | unknown |
| 1 | `burger gosh mighty` | dish | unknown |

#### `pro_reason = possessive` (152 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 23 | `big murphy pizza stuffed` | dish | possessive |
| 19 | `breakfast juan tacos` | dish | possessive |
| 11 | `bbq burger butch wild` | dish | possessive |
| 10 | `bistec de panchos` | regional | possessive |
| 10 | `basket daddy fried oyster` | dish | possessive |
| 1 | `crust lovers meat piara pizza thin` | dish | possessive |
| 1 | `daddy sandwich waffle` | dish | possessive |
| 2 | `club maggie sandwich turkey` | dish | possessive |
| 1 | `ribs woo` | regional | possessive |
| 1 | `farm glenmary grilled ribeye` | dish | possessive |
| 1 | `charritos nachos` | regional | possessive |
| 1 | `greek pizza ricco stromboli` | dish | possessive |
| 2 | `maverick taco` | dish | possessive |
| 2 | `camarones luis` | possessive | possessive |
| 1 | `crepes leonardo pasta` | dish | possessive |

#### `pro_reason = proper` (150 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 42 | `chicken fried luann steak` | dish | proper |
| 13 | `little pigs pizza` | dish | proper |
| 4 | `franklin sandwich` | dish | proper |
| 4 | `camarones el patron` | regional | proper |
| 4 | `capitan el nachos` | regional | proper |
| 1 | `panini passionate pig sandwich` | dish | proper |
| 1 | `bender buffalo house wings` | possessive | proper |
| 1 | `lobster roll smokin sushi` | dish | proper |
| 1 | `burrito degollado plaza` | regional | proper |
| 2 | `brisket luckenbach prime texas` | regional | proper |
| 1 | `avemaria pizza` | dish | proper |
| 2 | `cart la street taco` | dish | proper |
| 1 | `burger don hamburguesa pollo` | dish | proper |
| 1 | `diaz plate tampiquena` | regional | proper |
| 1 | `biryani paneer paradise` | combo | proper |

#### `pro_reason = vague-name` (108 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 47 | `deluxe italian` | dish | vague-name |
| 47 | `big cheese` | dish | vague-name |
| 41 | `burger rocket` | dish | vague-name |
| 39 | `loco taco` | dish | vague-name |
| 35 | `gourmet lover meat pizza` | dish | vague-name |
| 1 | `chicken hunters` | dish | vague-name |
| 1 | `bowl combination rice` | combo | vague-name |
| 1 | `burger husky super` | dish | vague-name |
| 1 | `chicken crystal` | dish | vague-name |
| 1 | `burger django thick` | dish | vague-name |
| 1 | `bacon breakfast spinach` | combo | vague-name |
| 1 | `egg roll scrambled` | combo | vague-name |
| 1 | `bean flavorous vermicelli` | dish | vague-name |
| 1 | `classic sushi` | dish | vague-name |
| 12 | `love roll` | vague | vague-name |

#### `pro_reason = obscure` (106 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 165 | `buffalitos chicken grilled wrap` | dish | obscure |
| 51 | `hawaiian roll sushi` | dish | obscure |
| 26 | `pasta rattlesnake` | dish | obscure |
| 25 | `burger bypass` | dish | obscure |
| 21 | `bone boom wings` | dish | obscure |
| 1 | `lapa molcajete` | regional | obscure |
| 1 | `guiso la marina` | regional | obscure |
| 1 | `plantation quail` | dish | obscure |
| 1 | `corral del molcajete` | regional | obscure |
| 1 | `hokie roll` | regional | obscure |
| 3 | `burrito colita de pavo` | regional | obscure |
| 4 | `burger hippo mexican` | dish | obscure |
| 4 | `burger hawaiian hippo` | dish | obscure |
| 16 | `orleans roll` | dish | obscure |
| 1 | `monterosso pizza` | dish | obscure |

#### `pro_reason = ingredient` (98 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 74 | `butt pork shoulder` | dish | ingredient |
| 51 | `gulf shrimp` | generic | ingredient |
| 47 | `chicken thighs` | generic | ingredient |
| 45 | `alaska salmon wild` | combo | ingredient |
| 34 | `alabama catfish farm raised` | dish | ingredient |
| 1 | `boar genoa head salami` | dish | ingredient |
| 2 | `idli rava` | regional | ingredient |
| 3 | `chili paste thai` | dish | ingredient |
| 1 | `sausage summer` | dish | ingredient |
| 4 | `carne de hamburguesa` | regional | ingredient |
| 1 | `boar cheese head swiss` | dish | ingredient |
| 1 | `boar head prosciutto` | dish | ingredient |
| 1 | `chicken italian sausage` | combo | ingredient |
| 1 | `cheese cream dill` | dish | ingredient |
| 1 | `heritage pork` | dish | ingredient |

#### `pro_reason = fragment` (97 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 98 | `shrimp stuffed` | dish | fragment |
| 18 | `de jam torta` | gibberish | fragment |
| 17 | `burrito carne de` | dish | fragment |
| 16 | `bigt burger` | gibberish | fragment |
| 16 | `camarones de ensalada` | dish | fragment |
| 1 | `bng kashmiri kebab` | regional | fragment |
| 2 | `menudo oz` | regional | fragment |
| 1 | `cheese dz jalape tamales` | regional | fragment |
| 1 | `broccoli cashew chicken or` | combo | fragment |
| 1 | `fried ink pasta rice squid` | dish | fragment |
| 1 | `bun each pasta steamed stuffed` | combo | fragment |
| 1 | `burrito lr steak wrap` | burrito | fragment |
| 1 | `harabara murg tikka` | dish | fragment |
| 3 | `chorizo con` | combo | fragment |
| 1 | `chicharron de ma taco` | regional | fragment |

#### `pro_reason = vague-combo` (94 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 27 | `bone chop pork steak` | dish | vague-combo |
| 26 | `chinese pork vegetable` | dish | vague-combo |
| 10 | `chicken shrimp vegetables` | combo | vague-combo |
| 7 | `salad sushi` | dish | vague-combo |
| 7 | `chicken fried salad sandwich` | combo | vague-combo |
| 1 | `burger italian prego sandwich` | combo | vague-combo |
| 1 | `bacon crepe pesto turkey` | combo | vague-combo |
| 1 | `burrito cactus potato sweet` | dish | vague-combo |
| 1 | `enchiladas fajita taco` | combo | vague-combo |
| 1 | `bacon buttermilk pancakes slices` | dish | vague-combo |
| 1 | `pasta pork potsticker seasoned` | combo | vague-combo |
| 1 | `baby corn shrimp vegetable` | dish | vague-combo |
| 1 | `china fried grill rice` | dish | vague-combo |
| 1 | `barbecue plate ranch` | dish | vague-combo |
| 1 | `burger chicken fried waffle` | dish | vague-combo |

#### `pro_reason = nonstandard` (92 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 26 | `bbq thigh wings` | dish | nonstandard |
| 25 | `crunch wings` | dish | nonstandard |
| 11 | `pizza zydeco` | dish | nonstandard |
| 8 | `gyro kabob sandwich` | combo | nonstandard |
| 8 | `gyro shawarma wrap` | dish | nonstandard |
| 1 | `chicken general pasta plate rice tso` | combo | nonstandard |
| 1 | `alfredos asada carne` | dish | nonstandard |
| 1 | `sushi tarantula` | dish | nonstandard |
| 2 | `bacon cheese egg grits melt` | dish | nonstandard |
| 1 | `beef burrito cured suizo` | dish | nonstandard |
| 2 | `chips reuben sandwich` | combo | nonstandard |
| 1 | `salmon sushi tekka` | dish | nonstandard |
| 1 | `pizzadilla taco` | combo | nonstandard |
| 1 | `chicken pizzawich sandwich` | dish | nonstandard |
| 1 | `arepa novios` | regional | nonstandard |

#### `pro_reason = choice` (77 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 24 | `beef burrito chicken or` | combo | choice |
| 21 | `bacon ham or sausage stack` | dish | choice |
| 14 | `chicken fajita or shrimp` | dish | choice |
| 14 | `french or plain strawberry toast` | dish | choice |
| 13 | `breaded chicken fried hand or sized steak texas` | dish | choice |
| 1 | `chicken dumplings fried or pork` | combo | choice |
| 2 | `crispy noodle or soft tofu` | dish | choice |
| 1 | `beef grilled or sandwich shrimp` | combo | choice |
| 3 | `chicken or philly pizza steak` | combo | choice |
| 2 | `burrito or torta` | combo | choice |
| 3 | `cheese or pasta ravioli tortellini` | combo | choice |
| 1 | `chicken momo or steam veg` | regional | choice |
| 1 | `burrito lengua or tripa` | regional | choice |
| 1 | `fish masala or shrimp` | dish | choice |
| 1 | `beef fun lo mei mein or` | dish | choice |

#### `pro_reason = person` (75 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 37 | `chang chicken spicy` | dish | person |
| 30 | `burrito jose san` | regional | person |
| 10 | `beef luann roast` | dish | person |
| 10 | `bbq chicken jim pizza smokin sweet` | combo | person |
| 6 | `paul reubens sandwich` | dish | person |
| 1 | `cheesesteak millbilly` | dish | person |
| 1 | `linguine marco pasta` | dish | person |
| 2 | `kim son steak` | possessive | person |
| 3 | `burger don pablo` | regional | person |
| 4 | `daddy mac pizza` | dish | person |
| 2 | `goat josh` | regional | person |
| 2 | `dimaria linguine pasta` | dish | person |
| 1 | `makeda tibs` | regional | person |
| 1 | `angela roll sushi` | dish | person |
| 1 | `ala lorenzo pollo` | regional | person |

#### `pro_reason = unrecognized` (72 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 30 | `logan steak` | dish | unrecognized |
| 8 | `chili fish mustard` | dish | unrecognized |
| 8 | `deli pizza york` | dish | unrecognized |
| 8 | `evil pizza ways` | dish | unrecognized |
| 5 | `pizza regina` | dish | unrecognized |
| 1 | `burrito ogden` | dish | unrecognized |
| 4 | `broccoli hsiang yu` | regional | unrecognized |
| 1 | `sushi tabico` | regional | unrecognized |
| 1 | `grilled pounder salmon sandwich` | dish | unrecognized |
| 1 | `paddy sandwich` | dish | unrecognized |
| 2 | `cowboy island sandwich` | dish | unrecognized |
| 1 | `gotalo paneer` | regional | unrecognized |
| 1 | `boka salad salmon` | combo | unrecognized |
| 1 | `scallops sub` | dish | unrecognized |
| 2 | `de pepena tacos` | regional | unrecognized |

#### `pro_reason = redundant` (59 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 9 | `burger cheeseburger veggie` | combo | redundant |
| 9 | `house pasta yakisoba` | combo | redundant |
| 7 | `basil pasta spaghetti` | dish | redundant |
| 7 | `hot wing wings` | dish | redundant |
| 6 | `camaron shrimp taco` | dish | redundant |
| 1 | `donburi gyudon` | regional | redundant |
| 1 | `daikon kimchi pickled` | dish | redundant |
| 2 | `chow mein noodle pasta` | dish | redundant |
| 1 | `gooksu kal pasta` | regional | redundant |
| 1 | `bacon blt` | dish | redundant |
| 2 | `pasta vegetable vermicelli` | dish | redundant |
| 1 | `pasta sandwich spaghetti` | combo | redundant |
| 1 | `egg roll rolls spring` | dish | redundant |
| 2 | `chicken fire wing wings` | combo | redundant |
| 1 | `fried rib ribs sandwich` | dish | redundant |

#### `pro_reason = propernoun` (58 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 8 | `amore pizza` | dish | propernoun |
| 6 | `capitan el pastor` | regional | propernoun |
| 6 | `capitan el vegetarian` | regional | propernoun |
| 6 | `biryani lamb lane spice` | regional | propernoun |
| 6 | `curry lamb lane spice` | regional | propernoun |
| 3 | `belmont burger chicken` | possessive | propernoun |
| 1 | `burrito el fortach` | regional | propernoun |
| 2 | `arugula leonardo pizza prosciutto` | combo | propernoun |
| 1 | `frances sandwich` | dish | propernoun |
| 1 | `barbacoa beef fe plato santa` | regional | propernoun |
| 3 | `barn chicago dog` | dish | propernoun |
| 5 | `chimino puntas steak` | regional | propernoun |
| 5 | `burger preston trail` | dish | propernoun |
| 1 | `pachalas steak` | regional | propernoun |
| 1 | `hoover sandwich` | dish | propernoun |

#### `pro_reason = fusion` (56 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 17 | `nachos quesadilla` | combo | fusion |
| 16 | `bbq chicken quesadilla taco` | combo | fusion |
| 10 | `calzone gyro` | dish | fusion |
| 8 | `bun cha gio pasta` | combo | fusion |
| 5 | `burrito enchiladas poblanas` | combo | fusion |
| 1 | `pasta suyuk tang` | regional | fusion |
| 2 | `bourbon chicken flatbread mac pizza` | combo | fusion |
| 1 | `caldo de res sandwich` | regional | fusion |
| 2 | `kung pao pork shrimp sour sweet` | dish | fusion |
| 1 | `bhaji fondue pav` | regional | fusion |
| 1 | `calzone mexican stromboli` | combo | fusion |
| 1 | `adobo fried pasta pork rice` | combo | fusion |
| 1 | `burrito unagi` | dish | fusion |
| 1 | `burrito ribeye sliced soy sweet` | dish | fusion |
| 2 | `bowl greek teriyaki` | dish | fusion |

#### `pro_reason = restaurant-specific` (52 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 16 | `arandas desayuno` | regional | restaurant-specific |
| 12 | `mazatlan pollo` | dish | restaurant-specific |
| 7 | `burrito costa la` | regional | restaurant-specific |
| 6 | `burger la tejana` | dish | restaurant-specific |
| 4 | `biryani theory veg` | dish | restaurant-specific |
| 1 | `burger classic kitchen` | dish | restaurant-specific |
| 1 | `astor dish greek souflaki steak` | regional | restaurant-specific |
| 1 | `adobo chicken la pasta villa` | combo | restaurant-specific |
| 1 | `pancho parrillada villa` | regional | restaurant-specific |
| 2 | `chicken curry special swagath` | regional | restaurant-specific |
| 1 | `breakfast sandwich tenampa` | regional | restaurant-specific |
| 4 | `biryani chicken theory` | dish | restaurant-specific |
| 1 | `biryani paneer sitara` | regional | restaurant-specific |
| 1 | `amigos cheese pizza` | dish | restaurant-specific |
| 2 | `burger hamburgesa jalisco la` | burger | restaurant-specific |

#### `pro_reason = modifier` (51 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 36 | `basket popcorn shrimp` | dish | modifier |
| 11 | `biryani chicken chunky` | dish | modifier |
| 7 | `chicken teriyaki white` | dish | modifier |
| 7 | `hangout hawaiian pizza` | dish | modifier |
| 7 | `buffalo haus wings` | dish | modifier |
| 1 | `gf salmon shoyu` | dish | modifier |
| 3 | `garlic lighter shrimp` | dish | modifier |
| 3 | `chicharron only` | dish | modifier |
| 1 | `chicken cholula sandwich works` | dish | modifier |
| 1 | `avocado basket burger california` | dish | modifier |
| 4 | `con jamon queso` | dish | modifier |
| 4 | `fajitas style` | dish | modifier |
| 1 | `chophouse pasta signature` | dish | modifier |
| 4 | `americanas fajitas` | dish | modifier |
| 3 | `burrito el especial` | dish | modifier |

#### `pro_reason = combination` (51 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 17 | `burrito enchilada taco` | combo | combination |
| 13 | `belgian eggs waffle` | dish | combination |
| 10 | `bean enchilada tostada` | combo | combination |
| 5 | `gyoza sushi` | dish | combination |
| 4 | `fajita nachos quesadilla` | combo | combination |
| 1 | `brisket sausage wings` | combo | combination |
| 1 | `bbq chicken fajita grilled pork ribs` | combo | combination |
| 2 | `beef chile con enchiladas queso tacos` | dish | combination |
| 3 | `applesauce battered chips fish fried` | dish | combination |
| 3 | `camarones carnitas` | dish | combination |
| 1 | `asada carne pollo zamora` | regional | combination |
| 1 | `chicken diana steak` | dish | combination |
| 3 | `pollo ranchero steak` | dish | combination |
| 2 | `beef braised ribs steak tomahawk` | dish | combination |
| 1 | `angus beef burger pasta` | combo | combination |

#### `pro_reason = restaurant` (46 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 49 | `italian pizza works` | dish | restaurant |
| 12 | `casa de enchiladas la` | regional | restaurant |
| 5 | `pizza village` | dish | restaurant |
| 5 | `el mexicano plate` | regional | restaurant |
| 3 | `spaghetti works` | dish | restaurant |
| 1 | `casa jalisco molcajete` | regional | restaurant |
| 1 | `biryani palace` | dish | restaurant |
| 1 | `el rodeo steak` | dish | restaurant |
| 1 | `lo mein palace` | dish | restaurant |
| 1 | `happy hunan` | regional | restaurant |
| 1 | `el ranchero soft tacos` | dish | restaurant |
| 1 | `asian buffet king roll sushi` | combo | restaurant |
| 1 | `bbq la ma pork szechuan` | regional | restaurant |
| 2 | `asado beef escondida la` | regional | restaurant |
| 1 | `antlers bacon bread cheese garlic` | dish | restaurant |

#### `pro_reason = nonsensical` (45 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 10 | `arroz de pupusas` | regional | nonsensical |
| 9 | `sandwich shrimp taco` | combo | nonsensical |
| 8 | `flying garlic pizza` | dish | nonsensical |
| 8 | `brown fried pasta rice` | combo | nonsensical |
| 6 | `coconut fried pasta rice` | dish | nonsensical |
| 1 | `fried pasta rice sticky stir` | combo | nonsensical |
| 1 | `chicken congee pasta` | dish | nonsensical |
| 1 | `pasta roll spring vietnamese` | dish | nonsensical |
| 1 | `pupusas sandwich` | dish | nonsensical |
| 2 | `basket corn dog sandwich` | combo | nonsensical |
| 3 | `breaded shrimp wings` | dish | nonsensical |
| 2 | `burrito chicken sandwich` | combo | nonsensical |
| 2 | `chicken jambalaya sausage steak` | combo | nonsensical |
| 1 | `jive turkey wrap` | dish | nonsensical |
| 3 | `bacon basket cheeseburger` | combo | nonsensical |

#### `pro_reason = branded` (42 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 176 | `wicked wings` | dish | branded |
| 46 | `magnifico pepperoni` | dish | branded |
| 8 | `beyond bibimbap bowl` | dish | branded |
| 6 | `burger cheeseburger paradise` | dish | branded |
| 5 | `calzone meatster` | dish | branded |
| 1 | `mealbox saag` | combo | branded |
| 2 | `el scorcho taco` | dish | branded |
| 1 | `apple ciroc maple wings` | dish | branded |
| 3 | `hen house little waffle` | dish | branded |
| 1 | `chopstix fried rice` | dish | branded |
| 1 | `piaggio pizza` | dish | branded |
| 1 | `barbecue burger ole virginia` | combo | branded |
| 3 | `bellacino pizza super` | dish | branded |
| 1 | `city gyro windy` | dish | branded |
| 2 | `burger give kiss me mushroom swiss` | dish | branded |

#### `pro_reason = list` (42 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 34 | `burger pizza sandwich` | combo | list |
| 34 | `taco tamales` | combo | list |
| 17 | `burger eggs steak` | combo | list |
| 11 | `fillets fish fried shrimp` | dish | list |
| 4 | `deep dish lasagna pasta ravioli` | dish | list |
| 1 | `cheese chicken enchilada flauta guacamole tostada` | combo | list |
| 2 | `burrito chalupa chile chimichanga enchilada or relleno taco tamale tostada` | combo | list |
| 1 | `brisket chicken leg quarter rib` | combo | list |
| 1 | `arroz chuzo kabob or shish` | combo | list |
| 2 | `beans beef enchilada fried mexican one rice taco` | combo | list |
| 1 | `beans burrito quesadilla tamale` | combo | list |
| 2 | `beef boti chicken kabob malai seekh tikka` | dish | list |
| 2 | `chorizo quesadilla taco` | dish | list |
| 1 | `ramen sushi yakisoba` | combo | list |
| 1 | `bbq chicken fried noodles or pan pasta pork` | combo | list |

#### `pro_reason = ingredients` (37 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 10 | `gruyere ham` | dish | ingredients |
| 6 | `filets fish shrimp` | combo | ingredients |
| 5 | `cheese egg jalapeno patty sausage` | combo | ingredients |
| 4 | `beef noodle pasta starch wheat` | dish | ingredients |
| 2 | `butter cinnamon sugar` | combo | ingredients |
| 1 | `bacon cheese goat` | dish | ingredients |
| 2 | `breast provolone turkey` | dish | ingredients |
| 1 | `cheddar cheese chorizo fresh jalapenos tomato` | combo | ingredients |
| 1 | `cascabel la puerco` | regional | ingredients |
| 1 | `cucumber garlic spicy` | dish | ingredients |
| 1 | `almonds beef cranberry` | dish | ingredients |
| 1 | `hashbrown pizza taleggio` | combo | ingredients |
| 1 | `cheddar cheese chili onion` | combo | ingredients |
| 1 | `custom fusilli pasta penne` | combo | ingredients |
| 1 | `chicken crab egg imitation noodles pork shrimp squid` | combo | ingredients |

#### `pro_reason = contradictory` (35 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 7 | `chicken mixed vegetables vegetarian` | dish | contradictory |
| 4 | `beef crispy vegetarian` | dish | contradictory |
| 3 | `chicken fried rotisserie` | dish | contradictory |
| 2 | `chicken hunan vegan` | dish | contradictory |
| 2 | `curry duck vegetarian` | combo | contradictory |
| 2 | `chicken sour sweet vegetarian` | combo | contradictory |
| 1 | `baked cod free gluten steak` | dish | contradictory |
| 1 | `beef empanada vegan` | combo | contradictory |
| 1 | `beef plate rice vegetarian` | combo | contradictory |
| 1 | `fried pork rice vegan` | dish | contradictory |
| 1 | `fish fried gulf torta vegan` | dish | contradictory |
| 1 | `curry ham tofu vegetarian` | dish | contradictory |
| 1 | `chicken jerk vegan wings` | dish | contradictory |
| 1 | `beef chicken grilled katsu` | combo | contradictory |
| 2 | `belly bowl pork rice roasted vegan` | dish | contradictory |

#### `pro_reason = nonsense` (33 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 91 | `fried pasta pineapple rice` | dish | nonsense |
| 12 | `sammie soup` | combo | nonsense |
| 9 | `chop house suey` | dish | nonsense |
| 6 | `chicken madras murgun` | regional | nonsense |
| 3 | `dutch sashimi yellowtail` | dish | nonsense |
| 1 | `bone fried shrimp` | dish | nonsense |
| 1 | `chilibbean pirate sandwich` | dish | nonsense |
| 1 | `caught pickle sandwich` | dish | nonsense |
| 1 | `cheese cheesesteak plain steak` | dish | nonsense |
| 2 | `curry fish goal goan` | regional | nonsense |
| 2 | `fried noodle pan pasta rice seafood vegetables` | combo | nonsense |
| 1 | `burger sandwich tournament` | combo | nonsense |
| 1 | `taco wako` | dish | nonsense |
| 1 | `duck mushroom pumpkin vegetarian` | dish | nonsense |
| 2 | `beans beef cheese enchilada fried mexican one rice` | combo | nonsense |

#### `pro_reason = incoherent-combo` (32 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 15 | `burger chicken philly sandwich` | combo | incoherent-combo |
| 15 | `grilled noodle pasta pork vermicelli` | dish | incoherent-combo |
| 15 | `fried shrimp steak` | dish | incoherent-combo |
| 15 | `beef lo mein or shrimp` | combo | incoherent-combo |
| 11 | `fire grilled pasta ribeye` | dish | incoherent-combo |
| 1 | `carbonara corn empanadas sweet` | combo | incoherent-combo |
| 1 | `bulgogi salmon shrimp` | combo | incoherent-combo |
| 1 | `curry figs kofta paneer` | dish | incoherent-combo |
| 9 | `beef plate quesadilla` | dish | incoherent-combo |
| 1 | `nachos waffle` | dish | incoherent-combo |
| 1 | `duck rainbow vegetarian` | dish | incoherent-combo |
| 1 | `shrimp tenderloin` | dish | incoherent-combo |
| 9 | `bacon burger chicken` | combo | incoherent-combo |
| 3 | `butternut eggplant risotto spicy squash` | dish | incoherent-combo |
| 3 | `bbq burger chicken club fried` | combo | incoherent-combo |

#### `pro_reason = fragmented` (32 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 12 | `chicken fried or steak` | dish | fragmented |
| 7 | `bistro burger sandwich steak` | combo | fragmented |
| 2 | `buffalo spud tender` | dish | fragmented |
| 2 | `eggs gyro meat two` | dish | fragmented |
| 2 | `garlic grilled salmon sauce` | dish | fragmented |
| 1 | `doble el mix taco` | combo | fragmented |
| 1 | `pasta plain soba soup` | dish | fragmented |
| 1 | `barbacoa bistec gordita taco` | combo | fragmented |
| 1 | `baby broccoli pok tofu` | dish | fragmented |
| 1 | `bean beef black noodle pasta rice sauce` | combo | fragmented |
| 1 | `chay com dau gan hu mi rau xao` | regional | fragmented |
| 1 | `banh bo cha dau ga hu lua mi nuong sandwich thit trung` | regional | fragmented |
| 1 | `shrimp sushi tempura udon` | combo | fragmented |
| 1 | `egg four harlem omelette spanish` | dish | fragmented |
| 1 | `burrito chilango taco` | combo | fragmented |

#### `pro_reason = proper-name` (32 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 7 | `cabrona la taco` | regional | proper-name |
| 6 | `bacon burger cheeseburger ennis` | dish | proper-name |
| 6 | `bbq chicken gourmet marias pizza` | dish | proper-name |
| 5 | `drunken jae noodle` | dish | proper-name |
| 5 | `chilaquiles joe taco` | regional | proper-name |
| 1 | `davos spaghetti` | dish | proper-name |
| 2 | `de largo pesto pizza` | regional | proper-name |
| 1 | `burger darbytown` | dish | proper-name |
| 1 | `breakfast burrito huck` | dish | proper-name |
| 1 | `kennedy sandwich` | dish | proper-name |
| 1 | `mi platter tierra` | regional | proper-name |
| 2 | `abduction burger jalapeno` | dish | proper-name |
| 1 | `reuben richmond` | dish | proper-name |
| 1 | `bozena platter shiro wot` | regional | proper-name |
| 1 | `bacon burger cheese roland` | dish | proper-name |

#### `pro_reason = descriptive` (31 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 5 | `beef tangy` | dish | descriptive |
| 4 | `fajita gordo plato` | regional | descriptive |
| 3 | `biscuit wich` | dish | descriptive |
| 2 | `cheeselicious pizza` | dish | descriptive |
| 2 | `barbecue fillet salmon scottish steak` | combo | descriptive |
| 1 | `chili free garlic gluten mushroom pasta spinach` | dish | descriptive |
| 1 | `burrito con crema de fajita pollo queso` | dish | descriptive |
| 1 | `combination fajitas plate specialty` | combo | descriptive |
| 1 | `chicken sunburned` | dish | descriptive |
| 1 | `dried egg feta sandwich spinach sun tomato white wrap` | dish | descriptive |
| 1 | `el sandwich verde` | dish | descriptive |
| 1 | `carnitas ricas` | regional | descriptive |
| 1 | `chicken naan tandoori` | dish | descriptive |
| 1 | `barbacoa huevos plate` | dish | descriptive |
| 1 | `bean curd fresh grilled pork rice served shrimp steamed vegetables wrapped` | dish | descriptive |

#### `pro_reason = local` (30 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 29 | `bayside burger` | dish | local |
| 15 | `austin roll` | regional | local |
| 5 | `cheesesteak schuylkill` | regional | local |
| 4 | `beaverton roll` | regional | local |
| 4 | `katy roll` | regional | local |
| 1 | `burger con fritas papas vegetariano waldos` | dish | local |
| 1 | `azuma house salad` | dish | local |
| 2 | `burger iola island thousand` | combo | local |
| 2 | `burger roanoke` | dish | local |
| 2 | `burger fairview turkey` | dish | local |
| 1 | `pizza thrive veggie` | dish | local |
| 1 | `greensboro roll` | regional | local |
| 2 | `chicken luau mountain pineapple pizza` | dish | local |
| 1 | `ballard roll sushi` | dish | local |
| 1 | `mckinney roll` | dish | local |

#### `pro_reason = code` (30 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 12 | `asiago oz peppercorn sirloin steak` | dish | code |
| 9 | `blackened caesar chicken gs` | dish | code |
| 8 | `cobb gs salad` | dish | code |
| 6 | `chicken curry mp` | gibberish | code |
| 5 | `deluxe gourmet pizza shrimp zz` | pizza | code |
| 2 | `beef italian sandwich show` | combo | code |
| 4 | `chicken crusted parmesan pp` | dish | code |
| 2 | `cf cheese egg omelet sausage three` | dish | code |
| 2 | `amaravati biryani chicken pk` | regional | code |
| 2 | `grilled mp pork` | vague | code |
| 2 | `reuben sandwich tg` | dish | code |
| 1 | `blanco burrito camaron zz` | regional | code |
| 1 | `basket burger classic wz` | burger | code |
| 2 | `beef grilled mp` | vague | code |
| 1 | `paneer sizzler tikka vkr` | dish | code |

#### `pro_reason = vague-description` (30 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 7 | `fried spinach stir` | dish | vague-description |
| 2 | `chicken shredded spicy` | dish | vague-description |
| 2 | `chicken decker grilled` | dish | vague-description |
| 2 | `breaded mexican style` | dish | vague-description |
| 2 | `salty shrimp spicy` | combo | vague-description |
| 1 | `cheese grilled sandwich shrimp` | dish | vague-description |
| 1 | `boneless chicken chili sauce` | dish | vague-description |
| 1 | `day fire grilled steak` | dish | vague-description |
| 1 | `buttery garlicky roll shrimp` | dish | vague-description |
| 1 | `beef grass lemon noodles` | dish | vague-description |
| 1 | `bullfrog casserole fresh garlic` | dish | vague-description |
| 1 | `celery fried fungus pan` | dish | vague-description |
| 1 | `beef mushrooms seasoned veggies` | dish | vague-description |
| 1 | `bbq la mexicana plate` | dish | vague-description |
| 1 | `broccoli chicken rabe sandwich` | dish | vague-description |

#### `pro_reason = garbled` (29 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 100 | `beef chow fun mei` | dish | garbled |
| 5 | `lo mein pad pasta` | combo | garbled |
| 4 | `carnivore inch pizza` | dish | garbled |
| 3 | `eye pepper ribeye steak` | combo | garbled |
| 3 | `barn chili frito potato` | dish | garbled |
| 1 | `diablo entree fra shrimp` | dish | garbled |
| 1 | `blood duck noodles pasta pot rice` | dish | garbled |
| 1 | `chicken fun lo mei mein or` | dish | garbled |
| 1 | `from noodle pad pasta thai wok` | combo | garbled |
| 1 | `beef curry peas withsnow` | dish | garbled |
| 1 | `de fried huevos skillet` | regional | garbled |
| 2 | `katsu tonkasu` | regional | garbled |
| 2 | `plate steak york` | dish | garbled |
| 2 | `de ndwich pastrami` | dish | garbled |
| 1 | `burger calan cheeseburger` | dish | garbled |

#### `pro_reason = sauce` (29 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 16 | `alfredo pasta sauce` | dish | sauce |
| 12 | `chicken fried gravy` | dish | sauce |
| 11 | `butter cream paneer sauce` | dish | sauce |
| 6 | `chimichurri` | dish | sauce |
| 6 | `broccoli garlic sauce spicy` | dish | sauce |
| 2 | `butter lemon pepper sauce` | combo | sauce |
| 1 | `barbecue beef sauce` | dish | sauce |
| 1 | `cucumber feta gyro sauce` | dish | sauce |
| 4 | `general sauce tso` | dish | sauce |
| 1 | `dan dan sauce` | regional | sauce |
| 1 | `curry sauce sauteed` | dish | sauce |
| 1 | `florentine pesto` | dish | sauce |
| 2 | `alfredo homemade` | dish | sauce |
| 4 | `curry pork sauce` | dish | sauce |
| 1 | `curry sauce thai` | dish | sauce |

#### `pro_reason = instruction` (28 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 188 | `bacon burger just` | dish | instruction |
| 145 | `baking chicago pizza required stuffed style` | dish | instruction |
| 62 | `beef broccoli gf` | dish | instruction |
| 4 | `grilled only shrimp` | dish | instruction |
| 4 | `catfish only sandwich` | dish | instruction |
| 2 | `bacon egg orden taco` | dish | instruction |
| 1 | `baba ghanoush gyro plate topped` | dish | instruction |
| 1 | `cauliflower ginger soy tempura without` | dish | instruction |
| 1 | `menudo only weekend` | dish | instruction |
| 1 | `chicken gizzards only` | dish | instruction |
| 3 | `easy over` | dish | instruction |
| 1 | `beans burrito no sirloin` | dish | instruction |
| 1 | `beans frita mojarra no` | regional | instruction |
| 2 | `brisket only sandwich` | dish | instruction |
| 1 | `bento pick premium roll sushi` | combo | instruction |

#### `pro_reason = brand` (28 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 44 | `gf original pei shrimp wei` | branded | brand |
| 43 | `del taco` | branded | brand |
| 10 | `freshetta pizza` | branded | brand |
| 6 | `gf pizza works` | dish | brand |
| 4 | `barn burger original` | dish | brand |
| 1 | `pesto pizza thrive vegan` | combo | brand |
| 1 | `boar cheese head muenster` | dish | brand |
| 1 | `cremora entree parmigiana veal` | dish | brand |
| 1 | `green harvest mixed salad tomatoes urban` | dish | brand |
| 1 | `fabuloso tamales` | dish | brand |
| 1 | `beyond roll sushi veggie` | dish | brand |
| 2 | `bacon bbq roadies sandwich` | dish | brand |
| 1 | `hook pasta penne pesto red shrimp` | dish | brand |
| 2 | `boar head pastrami` | dish | brand |
| 1 | `aroma chicken salad sandwich taco` | dish | brand |

#### `pro_reason = fragments` (27 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 145 | `burger chicken sandwich wild` | combo | fragments |
| 23 | `chicken chow fun mei pasta` | combo | fragments |
| 14 | `crispy fried noodles pan pasta` | dish | fragments |
| 14 | `burji curry egg` | regional | fragments |
| 2 | `fried rice wah wing xo` | dish | fragments |
| 1 | `egg paste rolls shrimp sugarcane vermicelli wrapped` | dish | fragments |
| 1 | `cai hu rau soup tieu` | regional | fragments |
| 1 | `baked chicken cream or over pasta rice sauce spaghetti` | combo | fragments |
| 1 | `fried hu noodles pasta rice stir tieu xao` | regional | fragments |
| 1 | `bean black chicken fried noodle pasta rice sauce stir` | pasta | fragments |
| 1 | `chop egg grilled meatloaf pork shredded skin steamed` | combo | fragments |
| 1 | `catfish fried original our recipe shores signature ski` | dish | fragments |
| 1 | `ham milanosa tinga trompo` | regional | fragments |
| 1 | `brisket carta ench` | dish | fragments |
| 1 | `chicken cooked dumplings meni pel` | regional | fragments |

#### `pro_reason = options` (27 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 90 | `apples biscuits casserole fried hashbrown meat or` | combo | options |
| 90 | `apples bacon casserole fried hashbrown or sausage` | combo | options |
| 4 | `beef burrito chicken or potato` | combo | options |
| 4 | `beef chicken fajitas or plate` | combo | options |
| 4 | `beef chicken fajita or taco` | combo | options |
| 1 | `beef chicken kung or pao scallop shrimp` | combo | options |
| 2 | `bangkok bowl burrito or shrimp` | dish | options |
| 1 | `burger cheese chicken or steak sub` | combo | options |
| 1 | `chow fun mein or pasta seafood` | combo | options |
| 1 | `marinara or shrimp squid` | combo | options |
| 2 | `enchilada or taco tamale tostada` | combo | options |
| 1 | `barbecue beef chicken or pizza` | combo | options |
| 1 | `en enchiladas mole roja salsa verde` | dish | options |
| 1 | `beijing noodle or pasta rice tofu` | dish | options |
| 2 | `beans chimichanga fried or rice soft taco` | dish | options |

#### `pro_reason = incomplete` (27 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 22 | `fried ginger stir` | dish | incomplete |
| 21 | `cashew nut pad` | dish | incomplete |
| 7 | `carne con` | dish | incomplete |
| 6 | `tikka` | regional | incomplete |
| 5 | `scampi` | dish | incomplete |
| 1 | `mu shu style` | dish | incomplete |
| 1 | `sesame style` | dish | incomplete |
| 1 | `bbq brisket sliced topped` | dish | incomplete |
| 2 | `al pesto` | dish | incomplete |
| 1 | `cheese grilled hot philly sandwich` | dish | incomplete |
| 1 | `combination flat noodles or pasta sauce without` | combo | incomplete |
| 1 | `bacon chile con` | dish | incomplete |
| 2 | `bean black style` | generic | incomplete |
| 4 | `carne chaufa con` | regional | incomplete |
| 2 | `authentic philly` | dish | incomplete |

#### `pro_reason = multiple` (23 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 236 | `calzone stromboli` | dish | multiple |
| 3 | `don eel sushi` | regional | multiple |
| 2 | `deep dish lasagna meat pasta ravioli` | dish | multiple |
| 2 | `angel beef hair noodles pasta rice singapore` | combo | multiple |
| 1 | `burrito taco tamale` | combo | multiple |
| 1 | `chicken crab general shell soft tso` | dish | multiple |
| 1 | `beans beef burrito one refried rice taco` | combo | multiple |
| 1 | `chinese chop chow mein or pork suey` | dish | multiple |
| 1 | `low mein noodle or pasta shrimp war` | dish | multiple |
| 1 | `blt club sandwich soup` | combo | multiple |
| 1 | `blt classic or sandwich wings wrap` | combo | multiple |
| 1 | `beef burrito chicken el loco or shredded` | dish | multiple |
| 1 | `cheese chicken chimichanga enchilada onion steak` | combo | multiple |
| 1 | `crepes crispy hand roll vietnamese` | regional | multiple |
| 1 | `beef low mein noodle or pasta war` | dish | multiple |

#### `pro_reason = location` (22 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 10 | `steak teriyaki york` | dish | location |
| 10 | `austin pizza south` | dish | location |
| 5 | `bacon bbq burger tribeca` | combo | location |
| 4 | `aeropuerto` | regional | location |
| 4 | `el paso tacos` | regional | location |
| 1 | `mumbai pizza veg` | dish | location |
| 1 | `midtown pokirrito` | combo | location |
| 1 | `burger club country riverside` | combo | location |
| 2 | `cozumel plate quesadilla` | regional | location |
| 3 | `cheesesteak riverfront sandwich` | dish | location |
| 2 | `guaynabita la pizza` | regional | location |
| 2 | `pizza supreme yonkers` | dish | location |
| 1 | `bacon cheeseburger ixtapa` | combo | location |
| 1 | `de esquina flautas la` | regional | location |
| 1 | `crepes north point` | dish | location |

#### `pro_reason = non-standard` (22 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 5 | `burrito ruleta` | regional | non-standard |
| 5 | `crazy fajita` | dish | non-standard |
| 5 | `antojo burrito` | dish | non-standard |
| 3 | `big dipper pizza` | dish | non-standard |
| 3 | `big pizza yorker` | dish | non-standard |
| 2 | `camaron con pechuga` | regional | non-standard |
| 1 | `chicken irie jerk vibes` | dish | non-standard |
| 2 | `bengali jalfrezi vegetable` | regional | non-standard |
| 1 | `chicago pizza steak` | combo | non-standard |
| 2 | `burger klasic krazy` | dish | non-standard |
| 3 | `meats mediana pizza` | dish | non-standard |
| 3 | `kabob pasha plate` | dish | non-standard |
| 2 | `maki roll utimo` | dish | non-standard |
| 2 | `buddy roll sushi` | dish | non-standard |
| 1 | `borracho steak` | dish | non-standard |

#### `pro_reason = named` (21 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 14 | `amore meat pizza` | dish | named |
| 12 | `chicken luigi` | dish | named |
| 12 | `buffalo pizza soldier` | dish | named |
| 5 | `burger husky` | dish | named |
| 3 | `burger kraken` | dish | named |
| 3 | `corleone sandwich` | dish | named |
| 1 | `mt rushmore sandwich` | dish | named |
| 1 | `kayaker panini river sandwich` | dish | named |
| 3 | `burger shroomer` | dish | named |
| 1 | `burrito la trinidad` | regional | named |
| 2 | `dante peak pizza` | dish | named |
| 1 | `abuelita enchiladas la` | regional | named |
| 1 | `back draft pizza` | dish | named |
| 1 | `calzone capone` | dish | named |
| 1 | `cargada mula quesadilla` | regional | named |

#### `pro_reason = category` (20 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `chicken entr tempura` | combo | category |
| 2 | `lunch tempura` | generic | category |
| 2 | `entree sashimi sushi` | dish | category |
| 2 | `entree gyro shawarma` | combo | category |
| 2 | `combination fried noodles or pasta rice` | combo | category |
| 1 | `assorted breakfast burritos tacos` | combo | category |
| 1 | `entree etouffee` | dish | category |
| 1 | `chilean sandwich` | regional | category |
| 1 | `asada con nopal platillos` | regional | category |
| 1 | `entree moussaka` | dish | category |
| 1 | `all cooked sushi` | dish | category |
| 1 | `caldos grandes` | regional | category |
| 1 | `chargrill entrees kafta` | regional | category |
| 1 | `cold deli sandwiches wraps` | combo | category |
| 1 | `continental desayuno` | regional | category |

#### `pro_reason = vague-fragments` (20 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `bowl bun tofu` | dish | vague-fragments |
| 2 | `breast chicken marinated steak` | dish | vague-fragments |
| 2 | `crispy eggplant hb tacos` | dish | vague-fragments |
| 2 | `en filete jalapena salsa` | regional | vague-fragments |
| 2 | `egg fried noodle pasta sauce soya stir` | combo | vague-fragments |
| 1 | `beef chicken choice fried or pork rice vegetable` | combo | vague-fragments |
| 2 | `beef big fat fried noodle pasta stir` | combo | vague-fragments |
| 2 | `beef chi fried rice` | dish | vague-fragments |
| 2 | `beef flat noodle pasta rice satay sauce` | combo | vague-fragments |
| 2 | `beans chile enchilada fried mexican one relleno rice` | combo | vague-fragments |
| 2 | `beef charbroiled egg peanut roasted roll vegetable` | combo | vague-fragments |
| 2 | `beef free gluten noodles pasta rice singapore` | combo | vague-fragments |
| 2 | `egg fried loaf meat pork rice shredded` | combo | vague-fragments |
| 1 | `dry egg fried ginger pasta rice scallop white` | combo | vague-fragments |
| 1 | `chicken chiles fried gravy jalapeno pickled smoked steak` | combo | vague-fragments |

#### `pro_reason = unrecognizable-fragment` (18 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 808 | `gai goo moo pan` | regional | unrecognizable-fragment |
| 3 | `mar plate tierra` | regional | unrecognizable-fragment |
| 2 | `burger diablo dog` | combo | unrecognizable-fragment |
| 2 | `bom burger diablo` | combo | unrecognizable-fragment |
| 2 | `oz shrimp steak` | dish | unrecognizable-fragment |
| 2 | `bowl bulgogi king kong` | dish | unrecognizable-fragment |
| 1 | `peeshda plate` | regional | unrecognizable-fragment |
| 1 | `hand meatball pizza tossed` | dish | unrecognizable-fragment |
| 1 | `enchiladas ruchos` | dish | unrecognizable-fragment |
| 2 | `cuban dk sandwich` | dish | unrecognizable-fragment |
| 2 | `chicken lt tikka` | gibberish | unrecognizable-fragment |
| 1 | `boar bologna head` | dish | unrecognizable-fragment |
| 2 | `burrito deluxe enchilada manadero` | dish | unrecognizable-fragment |
| 1 | `battered fish rock sandwich` | dish | unrecognizable-fragment |
| 1 | `chicken hot pamp sandwich` | combo | unrecognizable-fragment |

#### `pro_reason = abbreviation` (18 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 6 | `bacon bbq burger cheddar gs` | combo | abbreviation |
| 6 | `avocado chicken gs salad spinach` | combo | abbreviation |
| 4 | `cab sencilla torta` | regional | abbreviation |
| 4 | `cab normal torta` | regional | abbreviation |
| 2 | `catfish grilled lf` | dish | abbreviation |
| 1 | `breakfast cf steak` | combo | abbreviation |
| 2 | `bur burrito pltr shrimp` | dish | abbreviation |
| 1 | `breakfast burrito bw portobello` | dish | abbreviation |
| 1 | `gf salads` | generic | abbreviation |
| 1 | `aop spaghetti` | dish | abbreviation |
| 1 | `pesto pizza sic sl` | dish | abbreviation |
| 1 | `bw citrus salad sandwich` | combo | abbreviation |
| 1 | `elote med vegan` | dish | abbreviation |
| 1 | `baked pasta pepp ziti` | dish | abbreviation |
| 1 | `chipotle mx pasta` | dish | abbreviation |

#### `pro_reason = platter` (18 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `beef chicken platter` | combo | platter |
| 2 | `fried platter seafood steak` | combo | platter |
| 2 | `beef gyro lamb platter rice` | combo | platter |
| 2 | `broiled fisherman platter steak` | dish | platter |
| 1 | `pupusa trio` | dish | platter |
| 1 | `beans beef chimichanga ground rice` | combo | platter |
| 1 | `kung pao platter` | dish | platter |
| 1 | `nepali platter` | regional | platter |
| 1 | `broiled char chicken eggroll grass lemon rice vermicelli` | combo | platter |
| 1 | `beef fajita mexican plate steak style` | dish | platter |
| 1 | `beef chicken fajita mixed parrillada sausage shrimp` | combo | platter |
| 1 | `cheese grilled melt sandwich trio` | dish | platter |
| 1 | `braised platter ribs rice spare` | dish | platter |
| 1 | `beef grilled lemongrass platter rice` | dish | platter |
| 1 | `deluxe house sushi tray` | dish | platter |

#### `pro_reason = ingredient-list` (18 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `bean cheese guacamole` | combo | ingredient-list |
| 2 | `clam red sauce shrimp` | combo | ingredient-list |
| 2 | `blackened catfish gulf shrimp` | dish | ingredient-list |
| 2 | `dumpling pasta pork soup` | combo | ingredient-list |
| 2 | `chicken fish hotpot salted tofu` | combo | ingredient-list |
| 1 | `bittermelon jalapeno` | dish | ingredient-list |
| 1 | `cheese enchilada sauce` | dish | ingredient-list |
| 1 | `bamboo chili sauce shoots shredded` | dish | ingredient-list |
| 1 | `chicken ribs steak` | combo | ingredient-list |
| 1 | `chorizo eggs ham` | combo | ingredient-list |
| 1 | `bbq cheese onion` | combo | ingredient-list |
| 1 | `beef brisket eye flank rib steak tendon tripe` | combo | ingredient-list |
| 1 | `berkwood farms loin pork` | dish | ingredient-list |
| 1 | `beans ham rice smoked topped` | combo | ingredient-list |
| 1 | `beef chicken rice shrimp soup squid steam` | combo | ingredient-list |

#### `pro_reason = option` (17 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 7 | `bbq beef brisket chicken grilled or outdoor sub` | combo | option |
| 3 | `chicken lo mein or pork` | dish | option |
| 2 | `crispy fish or steamed` | dish | option |
| 2 | `noodles or rice salad` | generic | option |
| 2 | `baby bok choy gailan or` | regional | option |
| 1 | `ham omelet or sausage smoked` | combo | option |
| 1 | `bison ground or sirloin steak` | dish | option |
| 1 | `hard or soft taco` | dish | option |
| 1 | `beef chicken fried noodle or pan shrimp` | combo | option |
| 1 | `build gyro` | dish | option |
| 1 | `chow customized fried mein or rice` | chow_mein | option |
| 1 | `beef chicken combination or pork` | combo | option |
| 1 | `fried or sesame steamed tofu` | dish | option |
| 1 | `chicken curry lemongrass or pasta tofu` | combo | option |
| 1 | `fish fry or shrimp` | combo | option |

#### `pro_reason = misspelling` (17 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `italian parmesan sauage` | dish | misspelling |
| 2 | `phish sandwich` | dish | misspelling |
| 2 | `chirachi platter` | dish | misspelling |
| 2 | `chicken chille` | dish | misspelling |
| 2 | `foccasia pizza` | dish | misspelling |
| 1 | `egg omelet plate shakshcukah` | dish | misspelling |
| 1 | `chow kan mein pasta seafood yee` | combo | misspelling |
| 1 | `shrimp warmein` | regional | misspelling |
| 2 | `de guisado purerco` | regional | misspelling |
| 1 | `curry lamb lane spice spinach` | dish | misspelling |
| 1 | `lazatdar paneer` | regional | misspelling |
| 1 | `peral pizza white` | dish | misspelling |
| 2 | `chill dog sandwich` | dog | misspelling |
| 1 | `beef burger fried honey mustard onions vension` | combo | misspelling |
| 1 | `alla arrogosta salmone` | regional | misspelling |

#### `pro_reason = vague-modifiers` (17 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `burger fiesta french turkey` | dish | vague-modifiers |
| 1 | `cup garlic rice spicy` | dish | vague-modifiers |
| 1 | `cheese creamy garlic pasta` | dish | vague-modifiers |
| 1 | `chicken classic sandwich spicy` | dish | vague-modifiers |
| 1 | `bowl noodle pasta teriyaki` | combo | vague-modifiers |
| 1 | `dip sandwich steak tip` | dish | vague-modifiers |
| 1 | `charbroiled chicken sandwich western` | dish | vague-modifiers |
| 1 | `chicken chili diced spicy` | dish | vague-modifiers |
| 1 | `sandwich shrimper sub` | dish | vague-modifiers |
| 1 | `bites buffalo chicken stuffed` | dish | vague-modifiers |
| 1 | `chicken entree jalapeno spicy` | combo | vague-modifiers |
| 1 | `burger onion relish sauce tangy` | dish | vague-modifiers |
| 1 | `pizza thrive vegan veggie` | combo | vague-modifiers |
| 1 | `chinese seafood sizzling vegetables` | dish | vague-modifiers |
| 1 | `roll sushi sweet yuzu` | dish | vague-modifiers |

#### `pro_reason = unsearchable` (16 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 13 | `burger cheese smashmouth` | dish | unsearchable |
| 13 | `noodles pad pasta rice thai` | combo | unsearchable |
| 7 | `chowder lobster mobster pernod soup` | dish | unsearchable |
| 5 | `gazpacho taco` | dish | unsearchable |
| 3 | `cottage curry green` | dish | unsearchable |
| 3 | `burrito dirty donkey` | dish | unsearchable |
| 2 | `fare fish tacos` | dish | unsearchable |
| 2 | `pasta ramyun` | combo | unsearchable |
| 1 | `foil spinach wrap` | dish | unsearchable |
| 1 | `bacon bbq bone candied chop glazed pork` | dish | unsearchable |
| 2 | `el mochitense sushi` | regional | unsearchable |
| 2 | `fare state sub` | dish | unsearchable |
| 1 | `beef satay saute` | dish | unsearchable |
| 3 | `eggs pork ribs` | dish | unsearchable |
| 3 | `arizona sandwich turkey` | dish | unsearchable |

#### `pro_reason = gimmick` (16 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 5 | `burger namaste` | regional | gimmick |
| 5 | `pizza southpaw` | regional | gimmick |
| 4 | `burger eggvolution` | dish | gimmick |
| 3 | `beef volcano` | dish | gimmick |
| 3 | `blast butter chicken curry` | dish | gimmick |
| 1 | `bacon burger cheese pizza zilla` | combo | gimmick |
| 2 | `pepperoni philosophy pizza` | dish | gimmick |
| 1 | `pizza unkissable` | dish | gimmick |
| 1 | `veginator weenies` | dish | gimmick |
| 1 | `pizza spectacular veganation` | dish | gimmick |
| 2 | `candy cane sushi` | dish | gimmick |
| 1 | `lava pulao` | dish | gimmick |
| 1 | `angry bird sandwich` | dish | gimmick |
| 1 | `biryani paan` | regional | gimmick |
| 2 | `naan naughty paneer saag` | regional | gimmick |

#### `pro_reason = nondish` (16 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 4 | `chicken garlic lunch sauce` | dish | nondish |
| 3 | `burger maker vegan` | dish | nondish |
| 3 | `beef brown fried pasta rice` | combo | nondish |
| 3 | `brown fried pasta rice shrimp` | combo | nondish |
| 3 | `brown fried pasta rice vegetables` | combo | nondish |
| 2 | `crema de quesadilla` | dish | nondish |
| 2 | `bread garlic spaghetti` | dish | nondish |
| 1 | `burger cheese intentional sandwich smoke` | dish | nondish |
| 1 | `curry lassi mango` | combo | nondish |
| 1 | `alfredo fettucine pasta pesto` | dish | nondish |
| 1 | `parmesan pretty wings` | dish | nondish |
| 1 | `bar shawarma` | dish | nondish |
| 1 | `bowl rama` | regional | nondish |
| 1 | `abalone chicken congee pasta` | combo | nondish |
| 2 | `burrito ropa sin` | dish | nondish |

#### `pro_reason = not` (16 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `calzone house thai` | combo | not |
| 2 | `chicken pizza tipsy` | combo | not |
| 2 | `burrito fajita taco` | combo | not |
| 2 | `calzone chicken tandoori` | combo | not |
| 2 | `cab prime sirloin` | dish | not |
| 2 | `chicken flautas steak` | combo | not |
| 1 | `intestine pasta pork` | dish | not |
| 1 | `dual kebab` | dish | not |
| 1 | `gaucho steak taco` | dish | not |
| 1 | `flaming jack salmon` | dish | not |
| 2 | `hibachi sushi wings` | combo | not |
| 1 | `deluxe firehouse pizza` | dish | not |
| 1 | `sushi swamp thing` | dish | not |
| 2 | `gyoza japanese sushi` | combo | not |
| 1 | `blt paddler sammie` | dish | not |

#### `pro_reason = creative` (16 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `pad samurai thai` | regional | creative |
| 2 | `angry chicken wrap` | dish | creative |
| 2 | `calzone endless summer` | dish | creative |
| 2 | `big bird sub` | dish | creative |
| 2 | `alaskan burrito raw sunrise` | burrito | creative |
| 1 | `fields salmon strawberry` | dish | creative |
| 1 | `roadrunner sandwich` | dish | creative |
| 1 | `boy peaux swamp thang` | regional | creative |
| 2 | `calzone fantasy forager` | dish | creative |
| 1 | `dancing roll` | dish | creative |
| 1 | `chili ole omelette` | dish | creative |
| 2 | `bowl hogzilla pork spicy` | dish | creative |
| 1 | `firefighter roll` | dish | creative |
| 1 | `outkast taco` | dish | creative |
| 1 | `roll sunburst` | dish | creative |

#### `pro_reason = size` (15 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 47 | `alfredo chicken pasta size` | dish | size |
| 12 | `mediana pizza` | dish | size |
| 6 | `menudo quart` | regional | size |
| 6 | `menudo pint` | regional | size |
| 5 | `biryani chicken size` | dish | size |
| 1 | `chinese mix quart vegetable` | dish | size |
| 1 | `molcajete qrt salsa` | dish | size |
| 1 | `chilaquiles grand` | dish | size |
| 1 | `cheese pizza xlg` | dish | size |
| 3 | `plate ribeye steak` | dish | size |
| 1 | `pizza veggie xlg` | dish | size |
| 1 | `grandes tostones` | dish | size |
| 1 | `artichoke chicken pizza size` | dish | size |
| 1 | `mega milanesa` | dish | size |
| 2 | `big one pizza` | dish | size |

#### `pro_reason = custom` (15 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 21 | `bacon bean black burger smash` | combo | custom |
| 21 | `bacon bbq bean black burger cheddar` | combo | custom |
| 21 | `avocado bacon bean black burger club` | combo | custom |
| 5 | `custom enchilada plate` | dish | custom |
| 3 | `custom pasta spaghetti` | dish | custom |
| 1 | `custom flatbread pizza` | dish | custom |
| 1 | `custom oven pizza wood` | dish | custom |
| 1 | `station sub supreme` | dish | custom |
| 1 | `burger byo chicken kofta` | combo | custom |
| 1 | `burger patriot prime` | dish | custom |
| 1 | `ala carta taco` | dish | custom |
| 1 | `free garlic gluten pesto pizza roasted supreme` | dish | custom |
| 3 | `california kama kani roll sushi` | dish | custom |
| 3 | `egg fried no pork rice veggie` | dish | custom |
| 3 | `egg fried no rice shrimp veggie` | dish | custom |

#### `pro_reason = hybrid` (15 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 13 | `burrito torta` | combo | hybrid |
| 8 | `chicken general teriyaki tso` | combo | hybrid |
| 6 | `camarones la mexicana steak` | regional | hybrid |
| 4 | `cajun sour sweet wings` | dish | hybrid |
| 3 | `giant quesadilla taco` | dish | hybrid |
| 1 | `burger fish taco` | combo | hybrid |
| 1 | `burger carnitas pork torta` | combo | hybrid |
| 2 | `pasta risotto seafood` | combo | hybrid |
| 2 | `club quesadilla sandwich` | combo | hybrid |
| 1 | `burger burrito tofu vegan` | combo | hybrid |
| 1 | `breakfast loaded sandwich taco` | combo | hybrid |
| 1 | `de hongos huarache quesadilla` | regional | hybrid |
| 1 | `steak taco torta` | dish | hybrid |
| 2 | `alfredo arrabiata pasta` | dish | hybrid |
| 1 | `cheese empanadas spinach taco` | combo | hybrid |

#### `pro_reason = quantity` (15 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 10 | `dos tacos` | dish | quantity |
| 10 | `buffalo hundred pieces wings` | dish | quantity |
| 4 | `carnitas pound` | dish | quantity |
| 2 | `catfish lb nuggets` | dish | quantity |
| 2 | `bbq pork pound` | dish | quantity |
| 1 | `dos taquitos` | dish | quantity |
| 1 | `koobideh naan one skewer` | regional | quantity |
| 1 | `chicharron pound` | dish | quantity |
| 1 | `koobideh naan skewers two` | dish | quantity |
| 1 | `asiago cheese gallon ravioli` | dish | quantity |
| 2 | `fried quart rice vegetable` | dish | quantity |
| 1 | `nine oysters shrimp` | combo | quantity |
| 2 | `catfish fried shrimp six` | combo | quantity |
| 1 | `pound smoked turkey` | dish | quantity |
| 1 | `de docena tamales` | regional | quantity |

#### `pro_reason = condiment` (15 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 6 | `bbq fashioned jar old sauce` | dish | condiment |
| 5 | `bean garlic paste` | dish | condiment |
| 5 | `green salsa spicy` | dish | condiment |
| 4 | `katsu sauce` | dish | condiment |
| 4 | `chili crunch garlic` | dish | condiment |
| 1 | `bacon jam` | dish | condiment |
| 2 | `curried ketchup` | dish | condiment |
| 2 | `dutch mayo` | dish | condiment |
| 2 | `chili sauce sweet thai` | dish | condiment |
| 1 | `beef dog sauce` | dish | condiment |
| 3 | `fish sauce spicy` | dish | condiment |
| 1 | `blt creamy cucumber sandwich spread` | dish | condiment |
| 1 | `basil cream fresh pesto` | dish | condiment |
| 1 | `chili cucumber sauce` | dish | condiment |
| 1 | `duck sauce szechuan` | dish | condiment |

#### `pro_reason = description` (15 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `brisket moist sliced` | dish | description |
| 2 | `bean breakfast cut egg potatoes sausage tortillas` | combo | description |
| 1 | `calzone herbavore` | dish | description |
| 1 | `camarones carta la` | regional | description |
| 1 | `barbecue entre shrimp` | combo | description |
| 1 | `con parrillada vegetales` | regional | description |
| 1 | `all breakfast burrito day` | dish | description |
| 1 | `brisket plate portion reduced` | dish | description |
| 1 | `azteca con hongos huitlacoche tamal` | regional | description |
| 1 | `chicken marinated or pork` | combo | description |
| 1 | `natural pork pulled sauced` | dish | description |
| 1 | `lasagna pans pasta sized` | dish | description |
| 1 | `hot plate sauce tilapia` | dish | description |
| 1 | `cheese crunchy pizza thick` | dish | description |
| 1 | `curry non traditional veg` | dish | description |

#### `pro_reason = nonspecific` (14 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 269 | `bowl burrito chicken mexico` | combo | nonspecific |
| 9 | `cheese cheesesteak` | dish | nonspecific |
| 5 | `burrito tipicos` | regional | nonspecific |
| 5 | `beef broccoli chicken` | combo | nonspecific |
| 4 | `calzone cheeze zone` | gibberish | nonspecific |
| 1 | `pizza vamos` | dish | nonspecific |
| 1 | `crunch dog sandwich texas` | dish | nonspecific |
| 2 | `abstract eggplant` | dish | nonspecific |
| 1 | `gladiator wrap` | dish | nonspecific |
| 1 | `reuben sandwich square time` | dish | nonspecific |
| 1 | `chicken quarter sandwich` | dish | nonspecific |
| 1 | `french panini quarter sandwich` | dish | nonspecific |
| 1 | `avocado burger home sweet` | dish | nonspecific |
| 1 | `big burrito original sucker` | dish | nonspecific |

#### `pro_reason = vague-combination` (14 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 5 | `classic fried pasta rice` | dish | vague-combination |
| 2 | `grilled steak tofu` | dish | vague-combination |
| 2 | `greens mustard pork` | dish | vague-combination |
| 1 | `bacon mushroom oyster` | combo | vague-combination |
| 1 | `cream pico tilapia` | dish | vague-combination |
| 1 | `bowl bun shrimp` | combo | vague-combination |
| 1 | `meatloaf pasta slider` | dish | vague-combination |
| 1 | `beef combination flavor orange` | combo | vague-combination |
| 1 | `beef pasta rice sauteed vegetables` | combo | vague-combination |
| 1 | `fish noodles pasta pulled sliced` | dish | vague-combination |
| 1 | `braised butter eggplant shrimp` | dish | vague-combination |
| 1 | `fajita meat nachos taco` | combo | vague-combination |
| 1 | `clear hot noodle pasta pot shrimp` | dish | vague-combination |
| 1 | `noodles pasta rice shrimp taiwan` | combo | vague-combination |

#### `pro_reason = not-dish` (14 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `fried pickles wings` | combo | not-dish |
| 3 | `bar chow mein pork` | dish | not-dish |
| 3 | `andouille by cajun go meat pound sausage to` | regional | not-dish |
| 2 | `burger city` | dish | not-dish |
| 2 | `burger canyon` | dish | not-dish |
| 1 | `crab shack` | dish | not-dish |
| 2 | `burger queen` | dish | not-dish |
| 1 | `bap tofu waffle` | combo | not-dish |
| 1 | `fried rice studio` | dish | not-dish |
| 1 | `drunken hash rib` | dish | not-dish |
| 1 | `ceviche green pozole` | combo | not-dish |
| 1 | `beef heart tube` | dish | not-dish |
| 1 | `omelet yorkshire` | dish | not-dish |
| 1 | `filet mignon red snapper` | combo | not-dish |

#### `pro_reason = jumble` (13 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 117 | `chicken pasta queensland ribs shrimp` | combo | jumble |
| 11 | `chicken noodle pasta ramen soup` | combo | jumble |
| 4 | `enchiladas shrimp taco` | combo | jumble |
| 2 | `bolognese chicken parmigiana ziti` | combo | jumble |
| 2 | `burrito frijoles gorditas refritos` | combo | jumble |
| 1 | `noodle pasta pork rice stewed` | combo | jumble |
| 1 | `corn eggs fajita fried tortilla` | dish | jumble |
| 1 | `chicken gyro hummus meat or` | combo | jumble |
| 1 | `mex press shawarma tex wrap` | combo | jumble |
| 2 | `filet hibachi mignon squid` | combo | jumble |
| 2 | `balti do plaza shrimp` | regional | jumble |
| 1 | `bruschetta mac pizza tramezzino` | combo | jumble |
| 1 | `bo pasta pho soup vien` | regional | jumble |

#### `pro_reason = descriptor` (13 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 11 | `colossal shrimp` | dish | descriptor |
| 11 | `catfish farm raised usa` | dish | descriptor |
| 4 | `catfish farm raised` | dish | descriptor |
| 1 | `grouper gulf` | dish | descriptor |
| 1 | `flats wings` | dish | descriptor |
| 1 | `bread crazy garlic` | dish | descriptor |
| 1 | `chicken pungent` | dish | descriptor |
| 1 | `chicken frozen tamales` | dish | descriptor |
| 1 | `fantastic fungi sandwich` | dish | descriptor |
| 1 | `carnitas de libra madia` | regional | descriptor |
| 1 | `frita tipo tostada` | regional | descriptor |
| 1 | `sashimi style` | dish | descriptor |
| 1 | `plate rib teriyaki` | dish | descriptor |

#### `pro_reason = personal` (13 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 4 | `arquito burger` | dish | personal |
| 4 | `pochos taco` | dish | personal |
| 4 | `burger willie` | dish | personal |
| 4 | `dillinger pizza` | dish | personal |
| 4 | `burrito panfilo` | regional | personal |
| 1 | `alla baked gino ziti` | dish | personal |
| 2 | `beef bubba chili chop` | combo | personal |
| 2 | `burger el pollon` | regional | personal |
| 1 | `sandwich shelton sirloin` | dish | personal |
| 1 | `alla giulia pizza schiacciata` | combo | personal |
| 1 | `fried george rice st` | possessive | personal |
| 2 | `burger chicken fried lill` | dish | personal |
| 1 | `chicken chipotle honey johnny sandwich` | dish | personal |

#### `pro_reason = specific` (13 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 4 | `burger chopshop classic` | dish | specific |
| 2 | `sushi tsunami` | dish | specific |
| 2 | `brooklyn grilled heights pasta sausage` | dish | specific |
| 1 | `molcajete rompemares` | regional | specific |
| 1 | `breakfast brewtown sandwich` | dish | specific |
| 1 | `brisas las tostada` | regional | specific |
| 1 | `broad cheesesteak street` | dish | specific |
| 1 | `longview roll sushi` | dish | specific |
| 1 | `caliente navolato roll sushi` | regional | specific |
| 1 | `chuck frito pie sub wagon` | dish | specific |
| 1 | `roll sushi takamaki` | dish | specific |
| 1 | `around de island roti` | regional | specific |
| 1 | `sandwich wrap zorba` | dish | specific |

#### `pro_reason = uncommon` (13 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `hibachi yuba` | regional | uncommon |
| 2 | `cerveza fajita` | dish | uncommon |
| 1 | `duck sticks` | dish | uncommon |
| 1 | `bacon patty` | generic | uncommon |
| 1 | `rice tostadas` | combo | uncommon |
| 1 | `beef brisket soup sour` | dish | uncommon |
| 1 | `grape leaves sandwich` | dish | uncommon |
| 1 | `fish musubi` | dish | uncommon |
| 1 | `borscht sandwich ukrainian` | regional | uncommon |
| 1 | `mountain oreo waffle` | dish | uncommon |
| 1 | `bites shark` | dish | uncommon |
| 1 | `falafel pasta` | dish | uncommon |
| 1 | `cheese salmon steak` | dish | uncommon |

#### `pro_reason = typo` (13 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `cheesesteak freely philly` | dish | typo |
| 1 | `calazone calzone` | dish | typo |
| 1 | `lamp pide` | regional | typo |
| 1 | `hambak steak` | regional | typo |
| 1 | `hambutger kabob sandwich` | dish | typo |
| 1 | `beef child enchilada plate` | combo | typo |
| 1 | `beef ed flat noodles pasta saut` | combo | typo |
| 1 | `chicken fried merican steak` | dish | typo |
| 1 | `bowl char chicken gram grilled lemin vermicelli` | dish | typo |
| 1 | `deep dish giant lovers meat piara pizza` | dish | typo |
| 1 | `bbq jasmice ribs rice` | dish | typo |
| 1 | `fried rib ribs salad` | dish | typo |
| 1 | `leng taco` | regional | typo |

#### `pro_reason = name` (12 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 16 | `melt moby sandwich` | dish | name |
| 16 | `joojeh moby sandwich` | dish | name |
| 3 | `la quesosa` | regional | name |
| 1 | `angelo churrasco sant` | dish | name |
| 1 | `burger medina` | regional | name |
| 1 | `pasta spring vito` | dish | name |
| 1 | `asia lover roll sushi` | dish | name |
| 1 | `bbq buffalo burger rocky` | combo | name |
| 1 | `chiva especial parrilladas` | regional | name |
| 1 | `bowl olo poke shoyu` | dish | name |
| 1 | `primo schwartzie sub turkey` | dish | name |
| 1 | `capulet chicken pizza` | dish | name |

#### `pro_reason = jumbled` (12 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 16 | `beef hunan shrimp style` | combo | jumbled |
| 6 | `rancheros taco taquitos` | combo | jumbled |
| 2 | `chicken karahi masala tikka` | combo | jumbled |
| 1 | `buffalo mac pizza tramezzino` | combo | jumbled |
| 1 | `burger cheesy dog queso` | combo | jumbled |
| 1 | `don katsu pasta udon yaki` | combo | jumbled |
| 1 | `beans burrito cheese fried mexican rice` | combo | jumbled |
| 1 | `baked buffalo chicken oil olive potato salt sea stuffed wings` | dish | jumbled |
| 1 | `bai biryani mutton pasta veetu` | combo | jumbled |
| 1 | `baby bbq brisket cheese egg sandwich` | combo | jumbled |
| 1 | `chips dog hot noodle ramyon` | combo | jumbled |
| 1 | `beef birria de noodle soup taco` | dish | jumbled |

#### `pro_reason = fanciful` (12 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 6 | `chicken phoenix` | dish | fanciful |
| 3 | `chicken cielo pizza` | dish | fanciful |
| 2 | `little pigs pizza three` | dish | fanciful |
| 1 | `burger rickshaw` | dish | fanciful |
| 1 | `furious roll` | dish | fanciful |
| 1 | `adam eve roll sushi` | dish | fanciful |
| 1 | `cochiloco taco` | regional | fanciful |
| 1 | `chevre roast` | dish | fanciful |
| 1 | `fantabulous roll` | dish | fanciful |
| 1 | `milagrosa parrillada` | regional | fanciful |
| 1 | `burger crusader` | dish | fanciful |
| 1 | `angels swimming tofu` | dish | fanciful |

#### `pro_reason = marketing` (11 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 9 | `salmon slammin` | dish | marketing |
| 8 | `pepperoni pizza smackdown` | dish | marketing |
| 3 | `chicken craveable parm pasta` | dish | marketing |
| 2 | `bbq chubby duck` | dish | marketing |
| 1 | `crave wrap` | dish | marketing |
| 1 | `award hand pizza tossed winning` | dish | marketing |
| 1 | `adobada chicken craver` | dish | marketing |
| 1 | `extravaganza pizza veggie` | dish | marketing |
| 1 | `chicken crazy crispy sandwich` | dish | marketing |
| 1 | `sandwich sensational steak` | dish | marketing |
| 1 | `chicken famous skinless` | dish | marketing |

#### `pro_reason = pun` (11 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 5 | `cod father` | dish | pun |
| 4 | `pizza poultrygeist` | dish | pun |
| 4 | `calzone roni zone` | gibberish | pun |
| 3 | `fun guy pizza` | dish | pun |
| 2 | `eggcellent taco` | dish | pun |
| 1 | `fun guy hot pizza` | dish | pun |
| 1 | `phish wrap` | dish | pun |
| 1 | `big fat greek my omelette` | dish | pun |
| 2 | `besto pasta pesto` | dish | pun |
| 1 | `naan wiser` | regional | pun |
| 1 | `out roll sushi veg` | gibberish | pun |

#### `pro_reason = gimmicky` (11 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 4 | `frenzy tuna` | dish | gimmicky |
| 4 | `explosion quesadilla salad` | combo | gimmicky |
| 2 | `chicken grill omg spicy wrap` | dish | gimmicky |
| 1 | `cyclops gyro` | dish | gimmicky |
| 1 | `faux jita taco` | dish | gimmicky |
| 1 | `eggrolls philly willy` | combo | gimmicky |
| 1 | `blueberry kush sandwich` | dish | gimmicky |
| 1 | `hasta la pasta shrimp` | dish | gimmicky |
| 1 | `lamborghini linguine pasta` | dish | gimmicky |
| 1 | `basket eat it seafood` | dish | gimmicky |
| 1 | `attack heart meatball pizza` | dish | gimmicky |

#### `pro_reason = combo-plate` (10 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 31 | `chips fish taco` | combo | combo-plate |
| 3 | `enchiladas plate taco` | combo | combo-plate |
| 2 | `beans enchilada mexican rice taco` | combo | combo-plate |
| 2 | `bean beef plate taco tostada` | combo | combo-plate |
| 1 | `mariachi plate` | dish | combo-plate |
| 1 | `beef fajita ribs sausage` | combo | combo-plate |
| 1 | `cheese chicken enchiladas flauta salad taco` | combo | combo-plate |
| 1 | `beef combination plate shrimp` | combo | combo-plate |
| 1 | `cameron la plancha steak` | regional | combo-plate |
| 1 | `noodle ribs rice steamed` | dish | combo-plate |

#### `pro_reason = component` (10 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 27 | `corn tortillas` | dish | component |
| 3 | `broth pho` | dish | component |
| 3 | `asada cebolla` | dish | component |
| 2 | `bleu cheese crust` | dish | component |
| 2 | `bacon burger patties` | combo | component |
| 1 | `falafel patty` | dish | component |
| 1 | `chimichangas gravy` | dish | component |
| 1 | `caulilflower crust` | dish | component |
| 1 | `gravy lamb spicy` | dish | component |
| 2 | `breaded chicken pattie` | dish | component |

#### `pro_reason = contradiction` (10 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 6 | `chicken piccata steak` | dish | contradiction |
| 3 | `bowl chicken fajita fried southwest` | dish | contradiction |
| 2 | `beef curry malaysian red vegetarian` | regional | contradiction |
| 1 | `chicken crispy vegetarian` | dish | contradiction |
| 1 | `roll tuna vegetarian` | dish | contradiction |
| 1 | `fried ham rice vegetarian` | dish | contradiction |
| 1 | `breakfast egg sandwich vegan` | dish | contradiction |
| 1 | `breaded chick parmesan pizza vegetarian` | dish | contradiction |
| 1 | `fish lemongrass tuna vegan` | dish | contradiction |
| 1 | `cod fish spicy thai vegan` | dish | contradiction |

#### `pro_reason = portion` (10 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 4 | `chicken quarter white` | dish | portion |
| 2 | `baby pho` | dish | portion |
| 2 | `cup jambalaya` | dish | portion |
| 2 | `jambalaya plate` | dish | portion |
| 2 | `encebollado plato` | regional | portion |
| 1 | `french pieces three toast` | dish | portion |
| 1 | `chicken fajita para persona una` | regional | portion |
| 1 | `french kiddie toast` | dish | portion |
| 1 | `enchiladas triples` | dish | portion |
| 1 | `bean burrito kiddie` | dish | portion |

#### `pro_reason = mashup` (10 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `chicken general orange` | dish | mashup |
| 2 | `chow mein noodle pad pasta` | combo | mashup |
| 2 | `lad na noodle pad pasta` | combo | mashup |
| 1 | `fajitas mexicanas nachos` | combo | mashup |
| 1 | `nachos pozole verde` | dish | mashup |
| 1 | `kaju masala tikka` | regional | mashup |
| 1 | `cheesesteak pizza sub` | combo | mashup |
| 1 | `brisket cheese macaroni pizza skillet` | combo | mashup |
| 1 | `burger chicken jambalaya pasta` | combo | mashup |
| 1 | `corndog sandwich tx wagyu` | dish | mashup |

#### `pro_reason = vague-ingredients` (9 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 133 | `beef green pepper` | dish | vague-ingredients |
| 6 | `chicken mixed tvp vegetables` | dish | vague-ingredients |
| 2 | `bacon cheese grilled guacamole` | dish | vague-ingredients |
| 2 | `egg garlic hot plant sauce` | combo | vague-ingredients |
| 1 | `burger protein soy` | dish | vague-ingredients |
| 1 | `bacon cheese diced eggs scrambled` | dish | vague-ingredients |
| 1 | `cabbage chinese fish grilled pickled` | dish | vague-ingredients |
| 1 | `beef homemade link` | dish | vague-ingredients |
| 1 | `jam queso sandwich` | dish | vague-ingredients |

#### `pro_reason = invented` (9 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 17 | `fajita gordita` | dish | invented |
| 4 | `curry monsoon yellow` | dish | invented |
| 4 | `curry panang typhoon` | dish | invented |
| 3 | `forager pizza` | dish | invented |
| 3 | `holy pepperoni pizza` | dish | invented |
| 1 | `burger porkanator` | dish | invented |
| 1 | `raven sandwich` | dish | invented |
| 1 | `shabu shabu skewer spicy` | regional | invented |
| 1 | `killa macadilla pizza vegan` | combo | invented |

#### `pro_reason = vagueness` (9 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 8 | `chicken tofu` | dish | vagueness |
| 8 | `roll steak` | dish | vagueness |
| 8 | `clams mussels` | combo | vagueness |
| 3 | `blt blue super true` | dish | vagueness |
| 1 | `hondureno plato` | regional | vagueness |
| 1 | `egg patty pork sandwich sausage` | dish | vagueness |
| 1 | `plato pollo` | regional | vagueness |
| 1 | `fried noodles pasta szechuan veggie` | dish | vagueness |
| 1 | `broiled cheese` | dish | vagueness |

#### `pro_reason = novelty` (9 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 7 | `attack burger godzilla` | dish | novelty |
| 4 | `calzone cheeseburg zone` | gibberish | novelty |
| 3 | `roadkill skewers` | dish | novelty |
| 1 | `bubblegum sushi` | regional | novelty |
| 1 | `donkey taco` | dish | novelty |
| 1 | `chicago dog pizza style` | dish | novelty |
| 1 | `hindenburg sub` | regional | novelty |
| 1 | `cheese chicken fried monster roaring sandwich` | dish | novelty |
| 1 | `anaconda pasta` | vague | novelty |

#### `pro_reason = playful` (9 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 4 | `calzone twilight zone` | dish | playful |
| 4 | `chicken chow down` | dish | playful |
| 3 | `burger kudasai ranch` | dish | playful |
| 2 | `calzone italian stallion` | dish | playful |
| 1 | `beast benedict` | dish | playful |
| 1 | `piggylicious taco` | dish | playful |
| 1 | `bao crab daddy` | dish | playful |
| 1 | `curry maniac` | dish | playful |
| 1 | `alotta muffuletta` | dish | playful |

#### `pro_reason = mixed` (9 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `breakfast burrito chili sandwich` | combo | mixed |
| 1 | `arroz fideua negro` | regional | mixed |
| 1 | `chicken club satay` | combo | mixed |
| 1 | `enchiladas quesadilla vegetable verde` | combo | mixed |
| 1 | `bean chicken enchilada taco` | combo | mixed |
| 1 | `chicken curry fried hummus plate` | combo | mixed |
| 1 | `king pepper salmon seared tuna` | combo | mixed |
| 1 | `beef chicken fingers sticks teriyaki` | combo | mixed |
| 1 | `chicken lo mein pasta teriyaki` | dish | mixed |

#### `pro_reason = serving` (9 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `basket falafel` | dish | serving |
| 2 | `basket gizzard` | dish | serving |
| 2 | `bowl chicken wings` | dish | serving |
| 2 | `bowl chicken nuggets` | dish | serving |
| 1 | `platter taquito` | dish | serving |
| 1 | `bratwurst pair` | dish | serving |
| 1 | `cheesesteak tray` | dish | serving |
| 1 | `fajita for la parrilla two` | dish | serving |
| 1 | `ceviche tray` | dish | serving |

#### `pro_reason = hybrid-gibberish` (8 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 10 | `pupusas taco` | combo | hybrid-gibberish |
| 9 | `corn dog sandwich slider` | combo | hybrid-gibberish |
| 3 | `empanadas sandwich` | combo | hybrid-gibberish |
| 3 | `chirashi pasta` | combo | hybrid-gibberish |
| 1 | `falafel sandwich souvlaki` | combo | hybrid-gibberish |
| 1 | `egg fried pan papas taco` | dish | hybrid-gibberish |
| 1 | `alfredo chicken farfalle grilled pizza` | combo | hybrid-gibberish |
| 1 | `chicken fish hibachi japanese white` | dish | hybrid-gibberish |

#### `pro_reason = not-standard` (8 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 5 | `punk rock roll` | dish | not-standard |
| 4 | `chicken gyoza katsu` | combo | not-standard |
| 4 | `gulf mexico quesadilla` | regional | not-standard |
| 1 | `pizza zereshk` | regional | not-standard |
| 1 | `burger killer` | dish | not-standard |
| 1 | `dirty rice sandwich` | combo | not-standard |
| 1 | `fried kaizen rice` | dish | not-standard |
| 1 | `chickpea polenta roasted wrap` | dish | not-standard |

#### `pro_reason = generic-combo` (8 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `mixed rice vegetables` | dish | generic-combo |
| 3 | `bacon basket burger cheese` | combo | generic-combo |
| 2 | `burger cheeseburger chicken` | combo | generic-combo |
| 2 | `bbq chicken shrimp` | combo | generic-combo |
| 2 | `chicken lamb rice` | combo | generic-combo |
| 1 | `chicken mango veggie` | combo | generic-combo |
| 2 | `combinaci mediana pizza` | combo | generic-combo |
| 1 | `cheddar chop mashed pork potatoes` | dish | generic-combo |

#### `pro_reason = special` (7 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 37 | `chicken homestyle sunday` | dish | special |
| 2 | `del dia pescado` | regional | special |
| 1 | `chicken daily enchiladas` | dish | special |
| 1 | `chercher house special tibs` | regional | special |
| 1 | `mexico plate steak viva` | regional | special |
| 1 | `bawarchi fried fusion noodles rice special` | regional | special |
| 1 | `beef orange sauce special steak` | dish | special |

#### `pro_reason = presentation` (7 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 30 | `basket chicken wing` | combo | presentation |
| 19 | `boat sushi` | dish | presentation |
| 4 | `bento teriyaki tofu` | combo | presentation |
| 2 | `boat kyoto sushi` | combo | presentation |
| 1 | `sushi yacht` | dish | presentation |
| 1 | `falafel tower` | dish | presentation |
| 1 | `bowl bread masala murg naan tikka` | combo | presentation |

#### `pro_reason = multi` (7 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 27 | `loaded spud steak` | dish | multi |
| 1 | `chicken chinese chow egg fried mein rice roll vegetarian` | dish | multi |
| 1 | `ca chien dau fish fried hu tofu vien` | regional | multi |
| 1 | `amarillos churrasco con de guayaba rollitos salsa` | combo | multi |
| 1 | `angus beef brand certified filet scampi shrimp steak tenderloin` | dish | multi |
| 1 | `chicken chien com fried ga lac luc rice sizzling` | regional | multi |
| 1 | `bamboo chicken clear dried meat noodle pasta rice soup` | combo | multi |

#### `pro_reason = person-name` (7 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 21 | `eugene pizza supreme` | dish | person-name |
| 2 | `asada carne cristobal` | regional | person-name |
| 2 | `bacon braedynn cheeseburger pizza` | dish | person-name |
| 1 | `burger miss piggie` | dish | person-name |
| 1 | `abu ali chicken style` | dish | person-name |
| 1 | `leonardo martinelli pasta rigatoni` | dish | person-name |
| 1 | `amado carrillo roll sushi` | regional | person-name |

#### `pro_reason = unit` (7 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 14 | `beef fajita lb` | dish | unit |
| 14 | `bacon bourbon hickory oz sirloin steak` | dish | unit |
| 10 | `carnitas lb` | dish | unit |
| 5 | `oz steak teriyaki` | dish | unit |
| 5 | `beef chopped pound` | dish | unit |
| 2 | `beef brisket butter lbs` | dish | unit |
| 1 | `ounces ribeye steak` | dish | unit |

#### `pro_reason = confusing` (7 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 9 | `nachos pork taco` | combo | confusing |
| 2 | `alicha lamb wot` | regional | confusing |
| 2 | `barbecue noodle pasta pork soup` | combo | confusing |
| 1 | `sizzling steak teriyaki tilapia` | combo | confusing |
| 1 | `curry non red thai vegetable` | dish | confusing |
| 1 | `angel hair noodles pasta pork rice singapore` | combo | confusing |
| 1 | `chicken grilled pasta ramen shoyu` | combo | confusing |

#### `pro_reason = ingredient-only` (7 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 7 | `atlantic fresh salmon` | dish | ingredient-only |
| 5 | `cheese slice swiss` | dish | ingredient-only |
| 5 | `american cheese slice` | dish | ingredient-only |
| 1 | `japanese kurobuta` | regional | ingredient-only |
| 1 | `bun green onion` | dish | ingredient-only |
| 1 | `chicken dark meat wings` | dish | ingredient-only |
| 1 | `american beef kobe usda` | dish | ingredient-only |

#### `pro_reason = vague_modifier` (7 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 7 | `con queso steak` | dish | vague_modifier |
| 2 | `oscar style` | dish | vague_modifier |
| 2 | `chicken lunch taco` | combo | vague_modifier |
| 2 | `chorizo lunch taco` | combo | vague_modifier |
| 2 | `carnitas lunch taco` | combo | vague_modifier |
| 1 | `crown pizza` | dish | vague_modifier |
| 1 | `boardwalk philly sandwich style` | dish | vague_modifier |

#### `pro_reason = sampler` (7 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 5 | `flight taco` | dish | sampler |
| 2 | `duo italian sampler` | combo | sampler |
| 2 | `italian sampler trio` | combo | sampler |
| 1 | `fillet fish sampler` | dish | sampler |
| 1 | `sampler special tandoori` | combo | sampler |
| 1 | `chickpea curry potato pumpkin sampler spinach veggie` | combo | sampler |
| 1 | `breakfast cosmo sampler` | combo | sampler |

#### `pro_reason = fusion-gibberish` (7 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 4 | `gyudon pasta` | combo | fusion-gibberish |
| 2 | `pasta tori udon` | combo | fusion-gibberish |
| 1 | `cheesesteak hibachi` | dish | fusion-gibberish |
| 1 | `palabok sandwich` | combo | fusion-gibberish |
| 1 | `chilaquiles toast` | dish | fusion-gibberish |
| 1 | `beans black burrito jollof` | regional | fusion-gibberish |
| 1 | `banh fish mi spicy tacos` | combo | fusion-gibberish |

#### `pro_reason = branded-term` (7 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `concrete kiwi strawberry` | dish | branded-term |
| 2 | `concrete kreme krispy` | dish | branded-term |
| 2 | `concrete kiwi mango` | dish | branded-term |
| 2 | `concrete maple walnut` | dish | branded-term |
| 2 | `concrete orange pineapple` | dish | branded-term |
| 2 | `butter concrete peanut` | dish | branded-term |
| 2 | `concrete mango peach` | dish | branded-term |

#### `pro_reason = notdish` (7 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `blt hummus` | dish | notdish |
| 1 | `calzone taco` | dish | notdish |
| 1 | `hayburner sandwich` | dish | notdish |
| 1 | `lasagna spaghetti` | combo | notdish |
| 1 | `hottie pizza` | dish | notdish |
| 1 | `burrito pillow` | dish | notdish |
| 1 | `fried rice station train` | combo | notdish |

#### `pro_reason = unique` (6 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 91 | `burger madlove` | dish | unique |
| 20 | `mariner roll sushi` | dish | unique |
| 1 | `bucklebuster sandwich` | dish | unique |
| 1 | `notorious pig pizza` | dish | unique |
| 1 | `caribbean crunch gourmet pizza` | dish | unique |
| 1 | `caribbean cheese crunch pizza` | dish | unique |

#### `pro_reason = generic-ingredients` (6 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 15 | `beef ground vegetables` | generic | generic-ingredients |
| 10 | `beans cheese pork` | dish | generic-ingredients |
| 10 | `biscuit buttermilk grilled` | dish | generic-ingredients |
| 3 | `burrito de harina tortilla` | dish | generic-ingredients |
| 3 | `breakfast egg meat toast` | combo | generic-ingredients |
| 3 | `eggs links pancakes sausage` | combo | generic-ingredients |

#### `pro_reason = incomplete-name` (6 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 15 | `pad see` | regional | incomplete-name |
| 15 | `basil fried stir` | vague | incomplete-name |
| 8 | `baleada carne con` | regional | incomplete-name |
| 7 | `avocado fried stuffed` | dish | incomplete-name |
| 2 | `fried southern` | dish | incomplete-name |
| 2 | `chef cut steak strip york` | dish | incomplete-name |

#### `pro_reason = cut` (6 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `chicken dark quarter` | dish | cut |
| 2 | `chuck sirloin steak` | dish | cut |
| 2 | `farms river sirloin snake steak top wagyu` | dish | cut |
| 1 | `cap sirloin top` | dish | cut |
| 1 | `mahi mahi slab` | dish | cut |
| 1 | `beef certified filet hereford mignon` | dish | cut |

#### `pro_reason = meal` (6 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `chicken lemon lunch` | combo | meal |
| 3 | `chicken lunch mongolian` | combo | meal |
| 3 | `chicken garlic lunch` | combo | meal |
| 3 | `chicken lunch szechuan` | combo | meal |
| 1 | `galbi lunch` | regional | meal |
| 1 | `lunch teriyaki` | dish | meal |

#### `pro_reason = menu-code` (6 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `fajita for sampler two` | combo | menu-code |
| 1 | `gf linguine` | dish | menu-code |
| 1 | `aop pasta` | dish | menu-code |
| 1 | `bistek bowl stk` | dish | menu-code |
| 1 | `gf grilled salmon` | dish | menu-code |
| 1 | `blackened grilled or salmon` | dish | menu-code |

#### `pro_reason = generic-name` (6 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `brazos burger` | dish | generic-name |
| 2 | `revolver steak` | dish | generic-name |
| 2 | `cowtown steak` | dish | generic-name |
| 2 | `bricktown burger` | dish | generic-name |
| 2 | `legend pizza` | dish | generic-name |
| 1 | `cortes de mar` | regional | generic-name |

#### `pro_reason = vague-descriptor` (6 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `fragrant ribs` | dish | vague-descriptor |
| 2 | `pizza roasted vegetarian` | dish | vague-descriptor |
| 2 | `oysters shrimp tails` | combo | vague-descriptor |
| 2 | `la parrillada playa` | regional | vague-descriptor |
| 2 | `big chili easy shrimp sweet` | dish | vague-descriptor |
| 1 | `taco yummy` | dish | vague-descriptor |

#### `pro_reason = vague-special` (6 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `fried scallop special` | vague | vague-special |
| 2 | `fish fried special` | vague | vague-special |
| 1 | `kathmandu naan special` | vague | vague-special |
| 1 | `beef ginger noodle special` | combo | vague-special |
| 1 | `beans egg special taco` | combo | vague-special |
| 1 | `noodles pasta special vietnamese` | regional | vague-special |

#### `pro_reason = plate` (5 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 82 | `kielbasa plate sausage` | dish | plate |
| 9 | `barbacoa de plato` | regional | plate |
| 2 | `beef cheese enchilada one taco` | combo | plate |
| 1 | `bisteak chorizo plate quesadilla` | combo | plate |
| 1 | `crawfish fish fried plate` | dish | plate |

#### `pro_reason = vague-fragment` (5 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 56 | `bites chicken` | dish | vague-fragment |
| 56 | `beef shredded` | dish | vague-fragment |
| 4 | `asparagus pad` | dish | vague-fragment |
| 3 | `bean beef burrito or` | combo | vague-fragment |
| 1 | `drunken fried spicy stir` | dish | vague-fragment |

#### `pro_reason = generic-ingredient` (5 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 31 | `chicken sausage` | dish | generic-ingredient |
| 10 | `baby clam` | generic | generic-ingredient |
| 7 | `fresh salmon` | generic | generic-ingredient |
| 2 | `boiled peeled shrimp` | dish | generic-ingredient |
| 1 | `grain salad` | dish | generic-ingredient |

#### `pro_reason = components` (5 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 22 | `rice sashimi sushi` | combo | components |
| 2 | `bread hummus pita zaatar` | dish | components |
| 2 | `browns egg hash omelet toast` | combo | components |
| 1 | `barbacoa guacamole` | combo | components |
| 1 | `eggs grits sausages` | combo | components |

#### `pro_reason = proper_noun` (5 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 14 | `ground kabob lamb moby sandwich` | dish | proper_noun |
| 2 | `burger cheeseburger chipotle ferris` | combo | proper_noun |
| 2 | `broiled chicken kostas scampi souvlaki` | combo | proper_noun |
| 1 | `christie roll sushi` | dish | proper_noun |
| 1 | `blue burger star veggie` | dish | proper_noun |

#### `pro_reason = sauce-only` (5 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 12 | `mushroom pasta sauce` | generic | sauce-only |
| 2 | `caribbean honey orange sriracha` | combo | sauce-only |
| 1 | `beef bolognese sauce` | dish | sauce-only |
| 1 | `butter garlic teriyaki` | combo | sauce-only |
| 1 | `chicken chipotle fajita sauce` | dish | sauce-only |

#### `pro_reason = measurement` (5 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 6 | `brisket pound` | dish | measurement |
| 2 | `oz prime rib` | dish | measurement |
| 2 | `blue cheese oz wings` | dish | measurement |
| 1 | `pernil pound` | dish | measurement |
| 1 | `birria lb` | dish | measurement |

#### `pro_reason = notstandard` (5 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 5 | `pasta singapore` | dish | notstandard |
| 1 | `chilaquiles rellenos` | regional | notstandard |
| 1 | `frontier omelet` | dish | notstandard |
| 1 | `ranchero toast` | dish | notstandard |
| 1 | `nacho squid` | dish | notstandard |

#### `pro_reason = slang` (5 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 5 | `nashville og sandwich` | dish | slang |
| 1 | `crack pizza` | dish | slang |
| 1 | `shroom steak taco` | dish | slang |
| 1 | `bacon burger thicc` | dish | slang |
| 1 | `shroom taco town` | dish | slang |

#### `pro_reason = combo-platter` (5 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 4 | `chicken chow mein pork roast` | dish | combo-platter |
| 1 | `enchiladas sope taco` | combo | combo-platter |
| 1 | `mahi mahi scallops steak` | combo | combo-platter |
| 1 | `cheese enchilada one tacos` | combo | combo-platter |
| 1 | `chalupa chile choice enchilada or relleno tamal` | combo | combo-platter |

#### `pro_reason = personal-name` (5 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `caivano pizza` | dish | personal-name |
| 1 | `djan fried rice` | regional | personal-name |
| 1 | `roll sara sushi` | sushi | personal-name |
| 1 | `chicken cullen ranch roasted` | dish | personal-name |
| 1 | `colletti panini sandwich` | dish | personal-name |

#### `pro_reason = unusual` (5 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `cheese chocolate sandwich` | dish | unusual |
| 1 | `corn creamy sandwich` | dish | unusual |
| 1 | `marmalade orange taco` | combo | unusual |
| 1 | `braised cumin ribs vanilla` | dish | unusual |
| 1 | `beef egg jerky taco` | dish | unusual |

#### `pro_reason = creative-name` (5 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `night roll tokyo` | dish | creative-name |
| 2 | `maki papi roll` | dish | creative-name |
| 1 | `heartbreaker pizza` | dish | creative-name |
| 1 | `pizza wrangler` | dish | creative-name |
| 1 | `pizza shark` | dish | creative-name |

#### `pro_reason = restaurant-name` (5 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `bbq chicken gourmet maria pizza` | dish | restaurant-name |
| 1 | `afghan kabob village` | regional | restaurant-name |
| 1 | `chorillana don pollo` | regional | restaurant-name |
| 1 | `china chow garden mein` | regional | restaurant-name |
| 1 | `fish ginger ruang thai` | dish | restaurant-name |

#### `pro_reason = proprietary-name` (5 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `grilled isabella shrimp` | dish | proprietary-name |
| 1 | `bowl perseus` | dish | proprietary-name |
| 1 | `alamo club sandwich` | dish | proprietary-name |
| 1 | `canoer panini river sandwich` | dish | proprietary-name |
| 1 | `chicago cleopatra deep dish med pizza style` | combo | proprietary-name |

#### `pro_reason = propername` (5 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `brooklyn heights pizza ultimate` | dish | propername |
| 2 | `breast leonardo sandwich smoked turkey` | combo | propername |
| 1 | `cream sergio shrimp tomato` | dish | propername |
| 1 | `pizza sals specialty stuffed` | dish | propername |
| 1 | `burger cheese rocky` | combo | propername |

#### `pro_reason = house` (5 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `cilantro house lamb meatball` | combo | house |
| 1 | `acacia burger` | dish | house |
| 1 | `charmthai fried rice` | regional | house |
| 1 | `house mango rolls` | dish | house |
| 1 | `casa fajita parrillada real` | regional | house |

#### `pro_reason = incongruous` (5 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `belly garlic noodles pork roasted vegan` | dish | incongruous |
| 1 | `beef congee pasta` | dish | incongruous |
| 1 | `cheese katsu pasta udon` | combo | incongruous |
| 1 | `cheese katsu pasta soba` | combo | incongruous |
| 1 | `dried fried pasta rice scallop shrimp` | dish | incongruous |

#### `pro_reason = creation` (5 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `arepa volcano` | regional | creation |
| 1 | `chili crab toast` | dish | creation |
| 1 | `burrito lomo morita` | dish | creation |
| 1 | `fiesta roll salmon` | dish | creation |
| 1 | `de hamburguesa pernil sandwich` | regional | creation |

#### `pro_reason = unconventional` (5 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `banana burritos` | dish | unconventional |
| 1 | `butter oreo peanut sandwich` | dish | unconventional |
| 1 | `beef crispy jerky spaghetti` | dish | unconventional |
| 1 | `cheese goat sashimi tuna` | dish | unconventional |
| 1 | `curry fish fried hummus plate` | dish | unconventional |

#### `pro_reason = menu` (5 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chargrill entrees salmon` | dish | menu |
| 1 | `entree saffron salmon` | dish | menu |
| 1 | `combination sushi tempura` | combo | menu |
| 1 | `burger classic fw sandwich tg` | combo | menu |
| 1 | `bbq buffalo chicken med or pizza` | combo | menu |

#### `pro_reason = vague-list` (5 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `burger chicken salad taco` | combo | vague-list |
| 1 | `bacon burger cheese franks` | combo | vague-list |
| 1 | `bacon cheddar chicken steak` | combo | vague-list |
| 1 | `bacon burger cheddar pizza` | dish | vague-list |
| 1 | `beans rice salad sausage steak` | combo | vague-list |

#### `pro_reason = bowl` (4 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 35 | `bowl shrimp tempura` | dish | bowl |
| 2 | `bowl buffalo wings` | dish | bowl |
| 2 | `bowl pasta salmon` | dish | bowl |
| 1 | `bowl meatballs mushroom portobello zucchini` | dish | bowl |

#### `pro_reason = bare` (4 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 32 | `ravioli` | dish | bare |
| 21 | `crepes` | dish | bare |
| 21 | `egg omelette` | dish | bare |
| 21 | `chicken leg` | generic | bare |

#### `pro_reason = generic-side` (4 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 24 | `steamed vegetables` | dish | generic-side |
| 6 | `grilled onions` | generic | generic-side |
| 1 | `baked potatoes veggie` | dish | generic-side |
| 1 | `diet mixed steamed vegetable` | dish | generic-side |

#### `pro_reason = location-name` (4 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 12 | `cancun chicken` | dish | location-name |
| 1 | `roll sushi wilmington` | regional | location-name |
| 1 | `breakfast sandwich soho` | dish | location-name |
| 1 | `avocado north point toast` | dish | location-name |

#### `pro_reason = method` (4 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 10 | `bun fried pan` | dish | method |
| 7 | `la plancha` | regional | method |
| 2 | `chili green pan seared` | dish | method |
| 1 | `burger patty skillet` | dish | method |

#### `pro_reason = chain` (4 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 10 | `burger king` | branded | chain |
| 3 | `french toast works` | dish | chain |
| 3 | `golden waffle works` | dish | chain |
| 1 | `napulella pizza` | regional | chain |

#### `pro_reason = vague-plate` (4 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 9 | `brisket plate taco` | dish | vague-plate |
| 1 | `breakfast papa plate` | dish | vague-plate |
| 1 | `chiles plate quesadilla rellenos` | dish | vague-plate |
| 1 | `asada plate taco` | dish | vague-plate |

#### `pro_reason = branded-gibberish` (4 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 9 | `burger pounder` | dish | branded-gibberish |
| 2 | `lettucewich wich wicked` | branded | branded-gibberish |
| 1 | `pacman pizza` | dish | branded-gibberish |
| 1 | `bam crust free gluten mammoth pizza thank vegan wham you` | dish | branded-gibberish |

#### `pro_reason = garbled-name` (4 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 8 | `breast chicken fried stir` | dish | garbled-name |
| 8 | `beans chicken steamed string` | dish | garbled-name |
| 5 | `breast co morgan sauce smoked turkey` | dish | garbled-name |
| 5 | `chicken fried ol potato snacker` | dish | garbled-name |

#### `pro_reason = style` (4 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 6 | `milanese` | dish | style |
| 4 | `szechwan` | regional | style |
| 4 | `athenian` | regional | style |
| 3 | `crust pizza thin traditional` | dish | style |

#### `pro_reason = house-special` (4 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 5 | `kanihama roll` | regional | house-special |
| 1 | `chinampa special torta` | regional | house-special |
| 1 | `golden roll trio` | dish | house-special |
| 1 | `casa della lasagnette pasta` | dish | house-special |

#### `pro_reason = whimsical` (4 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 4 | `magic mushroom pizza` | dish | whimsical |
| 2 | `flour sweetheart taco` | dish | whimsical |
| 1 | `hasta la pasta steak` | dish | whimsical |
| 1 | `arepa del gato la` | regional | whimsical |

#### `pro_reason = promotional` (4 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `bracket buster wings` | dish | promotional |
| 3 | `sixteen sweet wings` | dish | promotional |
| 2 | `greek limited only time wrap` | dish | promotional |
| 1 | `festival mariscada` | regional | promotional |

#### `pro_reason = fusion-vague` (4 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `chicken philly tacos` | dish | fusion-vague |
| 1 | `chicken gyro msakhen` | regional | fusion-vague |
| 1 | `con huanca lomo na risotto saltado` | regional | fusion-vague |
| 1 | `cheese chicken grill philly steak tandoori` | dish | fusion-vague |

#### `pro_reason = product` (4 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `afang frozen soup` | regional | product |
| 1 | `frozen lasagna` | dish | product |
| 1 | `unchicken vegan` | dish | product |
| 1 | `basil chicken dumplings frozen` | dish | product |

#### `pro_reason = mishmash` (4 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `cajun fried pasta rice shrimp` | dish | mishmash |
| 2 | `alfredo calzone chicken spinach stromboli` | combo | mishmash |
| 2 | `blazing chicken noodles pasta shrimp udon` | combo | mishmash |
| 1 | `bhaji dosa masala pav` | regional | mishmash |

#### `pro_reason = two-items` (4 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `calzone panzerotti` | combo | two-items |
| 1 | `chicken fillets fish wings` | combo | two-items |
| 1 | `de elote pupusas tamal` | regional | two-items |
| 1 | `buffalo calzone spicy stromboli` | combo | two-items |

#### `pro_reason = made-up` (4 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `burricarne burrito` | dish | made-up |
| 1 | `burripleta burrito` | gibberish | made-up |
| 1 | `beef burger fed grass recovery sandwich` | dish | made-up |
| 1 | `big burger cheese chili faced messy open ugly` | dish | made-up |

#### `pro_reason = coined` (4 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `burrito spamminator` | gibberish | coined |
| 1 | `gyro overload` | dish | coined |
| 1 | `chicken rollrrito` | gibberish | coined |
| 1 | `fishilicious taco` | dish | coined |

#### `pro_reason = non-specific` (4 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `copenhagen pizza` | dish | non-specific |
| 1 | `berlin burger` | dish | non-specific |
| 1 | `duo taco vegan` | combo | non-specific |
| 1 | `salmon three ways` | dish | non-specific |

#### `pro_reason = vaguename` (4 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `glow pacific pizza` | pizza | vaguename |
| 1 | `coqui roll sushi` | regional | vaguename |
| 1 | `chicken grilled perfecto` | dish | vaguename |
| 1 | `barrio burrito el` | regional | vaguename |

#### `pro_reason = vague-generic` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 27 | `bowl steak` | dish | vague-generic |
| 1 | `all day sandwich vegan` | dish | vague-generic |
| 1 | `bowl famous loaded rice` | dish | vague-generic |

#### `pro_reason = location-specific` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 21 | `mt rainier roll sushi` | dish | location-specific |
| 1 | `cheeseburger seatown` | dish | location-specific |
| 1 | `archer avenue chicken strip` | dish | location-specific |

#### `pro_reason = serving-style` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 19 | `carnitas plate taco` | combo | serving-style |
| 12 | `platter potsticker` | dish | serving-style |
| 1 | `basket bites chicken rotisserie style` | dish | serving-style |

#### `pro_reason = too-generic` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 16 | `beef rice` | combo | too-generic |
| 3 | `fried pasta rice stir veggies` | combo | too-generic |
| 1 | `beef french steak style` | dish | too-generic |

#### `pro_reason = ambiguous-combo` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 14 | `calzone cheese steak stromboli` | combo | ambiguous-combo |
| 4 | `beef chicken mongolian shrimp style` | combo | ambiguous-combo |
| 4 | `bacon beyond burger cheese turkey` | combo | ambiguous-combo |

#### `pro_reason = alphabetized-gibberish` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 10 | `camaron de empanadas` | regional | alphabetized-gibberish |
| 10 | `barbacoa de gorditas` | regional | alphabetized-gibberish |
| 1 | `biscuits sugar` | dish | alphabetized-gibberish |

#### `pro_reason = fusion-mashup` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 9 | `pasta salmon teriyaki` | dish | fusion-mashup |
| 3 | `birria ramen soup taco` | dish | fusion-mashup |
| 1 | `creole garlic mushroom plate rice saltado vegan` | regional | fusion-mashup |

#### `pro_reason = confused` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 7 | `calzone chicken grilled stromboli` | combo | confused |
| 2 | `beef flat mixed noodle pasta rice vegetables` | combo | confused |
| 1 | `espada tenderloin` | dish | confused |

#### `pro_reason = vague_description` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 7 | `shrimp steamed veggie` | combo | vague_description |
| 7 | `burger nacho sandwich` | combo | vague_description |
| 7 | `bowl egg ham` | combo | vague_description |

#### `pro_reason = adjective` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 4 | `tejano` | regional | adjective |
| 2 | `catfish succulent` | dish | adjective |
| 1 | `chingon guacamole` | regional | adjective |

#### `pro_reason = incompatible` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `salmon sandwich taco` | combo | incompatible |
| 1 | `gumbo salisbury steak` | combo | incompatible |
| 1 | `hot nashville sandwich wings` | dish | incompatible |

#### `pro_reason = nontraditional` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `ham pad thai` | dish | nontraditional |
| 1 | `pig poke` | dish | nontraditional |
| 1 | `sirloin yakitori` | dish | nontraditional |

#### `pro_reason = phrase` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `best carnitas pork town` | dish | phrase |
| 1 | `nombre sin taco` | dish | phrase |
| 1 | `burrito con ganas` | regional | phrase |

#### `pro_reason = not_standard` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `chesapeake pasta` | dish | not_standard |
| 1 | `piggy torta` | dish | not_standard |
| 1 | `big boy jack sandwich` | dish | not_standard |

#### `pro_reason = nonexistent` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `falafel skewer` | dish | nonexistent |
| 1 | `egg sashimi` | dish | nonexistent |
| 1 | `blue drip waffles` | combo | nonexistent |

#### `pro_reason = place-modifier` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `fajita merida` | regional | place-modifier |
| 2 | `fajita uxmal` | regional | place-modifier |
| 2 | `chelem fajita` | regional | place-modifier |

#### `pro_reason = typo-gibberish` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `fired pizza wood` | dish | typo-gibberish |
| 1 | `bowl grilled striper` | dish | typo-gibberish |
| 1 | `breast chicken mushroom` | dish | typo-gibberish |

#### `pro_reason = brandless` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `palapa parrillada pollo` | regional | brandless |
| 1 | `sopes tacologia` | regional | brandless |
| 1 | `bear naked sausage smoked` | combo | brandless |

#### `pro_reason = disjunction` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `burrito chimichanga or` | dish | disjunction |
| 1 | `calzone or pizza stromboli` | combo | disjunction |
| 1 | `cacciatore chicken eggplant or` | combo | disjunction |

#### `pro_reason = composite` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `bibimbap bulgogi hot pot` | combo | composite |
| 1 | `asparagus steak` | dish | composite |
| 1 | `beef chile con enchilada queso tacos two wih` | combo | composite |

#### `pro_reason = multi-item` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `bacon eggs taco taquito` | taco | multi-item |
| 2 | `beans chalupa chile refried relleno` | combo | multi-item |
| 1 | `bacon basket bbq burger cheeseburger` | combo | multi-item |

#### `pro_reason = conflicting` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `chicken curried noodles pasta tomato` | dish | conflicting |
| 2 | `barbecue fried pasta pork rice` | combo | conflicting |
| 2 | `beef egg noodle pasta stew` | combo | conflicting |

#### `pro_reason = vague-phrase` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `pepper steak xanh` | dish | vague-phrase |
| 2 | `greek toast` | dish | vague-phrase |
| 1 | `con desayuno especial huevos` | regional | vague-phrase |

#### `pro_reason = modification` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `non noodles pad thai veg` | dish | modification |
| 1 | `alfredo meat no pasta` | dish | modification |
| 1 | `egg fried rice veggie without` | dish | modification |

#### `pro_reason = brand-name` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `bratwurst klements` | branded | brand-name |
| 1 | `cheeseburger hearsay sandwich wagyu` | dish | brand-name |
| 1 | `caesar camarones con longhorn salad` | salad | brand-name |

#### `pro_reason = madeup` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `dumpsterdilla quesadilla` | dish | madeup |
| 1 | `rollrrito tuna` | gibberish | madeup |
| 1 | `head monkey roll sushi` | dish | madeup |

#### `pro_reason = subjective` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `delicious meatloaf` | dish | subjective |
| 1 | `best burger ever veggie` | dish | subjective |
| 1 | `best chicken masala spicy` | dish | subjective |

#### `pro_reason = generic-description` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `flatbread greek sandwich` | dish | generic-description |
| 1 | `gruesa hamburguesa sandwich` | dish | generic-description |
| 1 | `flour meat quesadillas` | dish | generic-description |

#### `pro_reason = local-term` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `fuego roll vegan` | dish | local-term |
| 1 | `iris roll sushi` | dish | local-term |
| 1 | `daffodil roll sushi` | dish | local-term |

#### `pro_reason = selection` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `beef chicken or pineapple` | combo | selection |
| 1 | `beef or potato ribs sliced` | combo | selection |
| 1 | `beef ham or roast sliced turkey` | combo | selection |

#### `pro_reason = pricing` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `brisket per pound sliced` | dish | pricing |
| 1 | `bbq chicken per pound` | dish | pricing |
| 1 | `chicken grilled naan per pound` | dish | pricing |

#### `pro_reason = odd` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chow fun pasta toasted` | combo | odd |
| 1 | `alfredo garlic shrimp toast` | combo | odd |
| 1 | `pad pasta shrimps tempura thai` | dish | odd |

#### `pro_reason = conjunction` (3 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `cashew or shrimp vegetables` | combo | conjunction |
| 1 | `or ravioli shrimp tortellini` | combo | conjunction |
| 1 | `or ranchero sauce shrimp tomatillo` | combo | conjunction |

#### `pro_reason = branded-proper-noun` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 4658 | `cali fresh sandwich steak sub` | dish | branded-proper-noun |
| 4615 | `baja jack sandwich steak sub` | dish | branded-proper-noun |

#### `pro_reason = non-iconic-brand` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 23 | `crepe la madeleine` | regional | non-iconic-brand |
| 2 | `breakfast eggs green luxe sandwich` | combo | non-iconic-brand |

#### `pro_reason = pseudo-name` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 22 | `burrito huevorito` | regional | pseudo-name |
| 22 | `bacorito burrito` | dish | pseudo-name |

#### `pro_reason = menu-instruction` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 15 | `for porterhouse steak two` | dish | menu-instruction |
| 2 | `barbacoa by lb` | addon | menu-instruction |

#### `pro_reason = seasoning` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 13 | `lemon pepper` | dish | seasoning |
| 1 | `curry lemon pepper` | combo | seasoning |

#### `pro_reason = snack` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 10 | `cheese cheetos hot` | combo | snack |
| 1 | `bbq chips kettle` | dish | snack |

#### `pro_reason = vague-sandwich` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 10 | `beef cold roast sandwich` | dish | vague-sandwich |
| 1 | `hot melt ny sandwich` | dish | vague-sandwich |

#### `pro_reason = generic-pasta` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 9 | `classico pasta spaghetti` | dish | generic-pasta |
| 1 | `fresh parmesan pasta tomatoes` | dish | generic-pasta |

#### `pro_reason = generic-pizza` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 9 | `pepperoni pizza round` | dish | generic-pizza |
| 1 | `bacon cheese pizza six` | dish | generic-pizza |

#### `pro_reason = vague-category` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 8 | `free gluten pizza specialty` | dish | vague-category |
| 1 | `chimichanga specialties` | dish | vague-category |

#### `pro_reason = add-on` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 8 | `de harina orden taco` | regional | add-on |
| 2 | `beef biryani size` | dish | add-on |

#### `pro_reason = mismatch` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 7 | `bun cha gio nuong pasta thit` | regional | mismatch |
| 7 | `chow fun mei pasta pork roast` | regional | mismatch |

#### `pro_reason = nonsensical-combo` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 7 | `prime rib ribs` | dish | nonsensical-combo |
| 1 | `beef chicken nuggets` | combo | nonsensical-combo |

#### `pro_reason = generic-list` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 6 | `beef chicken shrimp` | combo | generic-list |
| 1 | `beef chicken fried shrimp udon vegetable` | combo | generic-list |

#### `pro_reason = concept` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 6 | `byo pasta spaghetti` | dish | concept |
| 3 | `flight lobster roll` | dish | concept |

#### `pro_reason = chain-specific` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 6 | `big boy hawaiian pizza` | dish | chain-specific |
| 6 | `big boy pizza supreme` | dish | chain-specific |

#### `pro_reason = not-searchable` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 6 | `bacon bbq big boy chicken pizza` | dish | not-searchable |
| 6 | `bacon big boy pizza roma spinach` | dish | not-searchable |

#### `pro_reason = unrecognizable-combo` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 5 | `curry fried green pasta rice` | combo | unrecognizable-combo |
| 1 | `gourmet neapolitan pizza york` | dish | unrecognizable-combo |

#### `pro_reason = place` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 4 | `palenque` | regional | place |
| 2 | `hong kong` | regional | place |

#### `pro_reason = flavor-only` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 4 | `chipotle southwest` | regional | flavor-only |
| 1 | `blazin buffalo ranch` | dish | flavor-only |

#### `pro_reason = arbitrary` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 4 | `astro roll` | dish | arbitrary |
| 4 | `border south wrap` | dish | arbitrary |

#### `pro_reason = venue` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 4 | `burrito taco truck` | dish | venue |
| 1 | `best chicken curry pub` | dish | venue |

#### `pro_reason = meal-type` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 4 | `chicken hunan lunch` | dish | meal-type |
| 4 | `chicken curry lunch` | dish | meal-type |

#### `pro_reason = generic-entree` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 4 | `beef entree grilled` | dish | generic-entree |
| 4 | `chicken entree lemongrass` | dish | generic-entree |

#### `pro_reason = basket` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 4 | `basket dog hot` | dish | basket |
| 3 | `basket chicken finger sandwich` | combo | basket |

#### `pro_reason = signature` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 4 | `presidente signature taco` | signature | signature |
| 1 | `acai bowl pura vida` | dish | signature |

#### `pro_reason = vague-word` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 4 | `chicken fajita lunch` | dish | vague-word |
| 4 | `chicken hunan plate` | dish | vague-word |

#### `pro_reason = generic-descriptor` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `sausage spicy` | dish | generic-descriptor |
| 2 | `burger handmade` | dish | generic-descriptor |

#### `pro_reason = timing` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `lunch manicotti` | dish | timing |
| 3 | `lasagna lunch` | dish | timing |

#### `pro_reason = promo` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `big burger time` | dish | promo |
| 1 | `hour lamb sandwich sliders` | dish | promo |

#### `pro_reason = vague-proper` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `backcountry breakfast burrito` | dish | vague-proper |
| 3 | `bbq pizza uptown` | dish | vague-proper |

#### `pro_reason = generic-plate` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `enchiladas plato traditional` | dish | generic-plate |
| 1 | `pattie plate pork` | dish | generic-plate |

#### `pro_reason = choice-list` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `beef broccoli chicken or shrimp` | combo | choice-list |
| 1 | `asada carne or pastor` | combo | choice-list |

#### `pro_reason = option-list` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `beef chicken gyro lamb or` | combo | option-list |
| 3 | `nabe or pasta soba udon yaki` | regional | option-list |

#### `pro_reason = generic-platter` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `melitzano platter` | regional | generic-platter |
| 1 | `breakfast meat platter premium` | dish | generic-platter |

#### `pro_reason = libra` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `carnitas libra` | regional | libra |
| 2 | `libra pastor` | regional | libra |

#### `pro_reason = generic-item` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `protein wrap` | dish | generic-item |
| 1 | `burger roller` | dish | generic-item |

#### `pro_reason = generic-count` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `four wings` | dish | generic-count |
| 1 | `corn tacos three tortilla` | dish | generic-count |

#### `pro_reason = vague-location` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `taco westside` | dish | vague-location |
| 1 | `jersey steak wrap` | dish | vague-location |

#### `pro_reason = assortment` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `inari nigiri sushi` | dish | assortment |
| 2 | `assortment for sashimi sushi three` | combo | assortment |

#### `pro_reason = set` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `maki rolls set` | dish | set |
| 1 | `lunch nigiri set sushi` | dish | set |

#### `pro_reason = vague-style` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `cantonese chicken style` | dish | vague-style |
| 1 | `home style torta tortilla` | dish | vague-style |

#### `pro_reason = house-roll` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `roll sushi tampico` | regional | house-roll |
| 2 | `big daddy roll` | dish | house-roll |

#### `pro_reason = gibberish-combo` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `don pasta yakiniku` | combo | gibberish-combo |
| 1 | `chicken hibachi pork` | combo | gibberish-combo |

#### `pro_reason = weird` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `beignets chicken fried` | dish | weird |
| 2 | `la mode pepperoni pizza` | dish | weird |

#### `pro_reason = geographic` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `curry red sea` | dish | geographic |
| 1 | `kerkyra pizza` | regional | geographic |

#### `pro_reason = variety` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `di formaggi italiani variet` | regional | variety |
| 1 | `balls grilled meat pasta pork skewer` | combo | variety |

#### `pro_reason = choice-option` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `chicken crispy grilled or salad` | combo | choice-option |
| 1 | `chicken lemongrass or pork` | dish | choice-option |

#### `pro_reason = modifier-only` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `fried gmo non rice tofu` | dish | modifier-only |
| 1 | `behemoth blt sandwich` | dish | modifier-only |

#### `pro_reason = combo-meal` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `bean burrito chalupa cheese quesadilla` | combo | combo-meal |
| 2 | `beef chicken crispy enchilada taco` | combo | combo-meal |

#### `pro_reason = not_single_dish` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `butter jollof or peanut rice stew` | regional | not_single_dish |
| 2 | `linguine marinara or pasta sauce spaghetti ziti` | combo | not_single_dish |

#### `pro_reason = ingredients-list` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `black italian mozzarella olives pancetta pepperoni pizza` | dish | ingredients-list |
| 1 | `bean black green pepper` | dish | ingredients-list |

#### `pro_reason = side` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chili slaw` | dish | side |
| 1 | `corn entree sauteed sweet` | combo | side |

#### `pro_reason = themed` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `seahawks wrap` | dish | themed |
| 1 | `burger chicago sox white` | combo | themed |

#### `pro_reason = vague-cut` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `peppercorn strip` | dish | vague-cut |
| 1 | `butcher chop cut pork` | dish | vague-cut |

#### `pro_reason = acronym` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `acp tacos` | combo | acronym |
| 1 | `acp steak` | combo | acronym |

#### `pro_reason = mythical` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chupacabra taco` | regional | mythical |
| 1 | `boar calydonian taco` | dish | mythical |

#### `pro_reason = unlikely` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `burger verbena` | dish | unlikely |
| 1 | `buffalo elk sandwich venison` | dish | unlikely |

#### `pro_reason = too` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `grilled pollo` | dish | too |
| 1 | `chickpea plate rice` | dish | too |

#### `pro_reason = bread` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `sandwich sourdough` | dish | bread |
| 1 | `bolillo or pocket subs` | dish | bread |

#### `pro_reason = generic-burger` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `bovine burger` | dish | generic-burger |
| 1 | `burger cheese lettuce mayonnaise tomato` | dish | generic-burger |

#### `pro_reason = personname` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `elvis hand roll` | dish | personname |
| 1 | `cosmo mortadella sandwich` | dish | personname |

#### `pro_reason = vague-dish` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `lamb sacha sauce` | dish | vague-dish |
| 1 | `beef chili preserved` | dish | vague-dish |

#### `pro_reason = category-tag` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chicken entree sausage` | combo | category-tag |
| 1 | `entree forest veal` | dish | category-tag |

#### `pro_reason = vague-brand` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `burger classic flames` | dish | vague-brand |
| 1 | `roll sushi tray waraku` | dish | vague-brand |

#### `pro_reason = combination-plate` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `grilled lobster ribeye` | combo | combination-plate |
| 1 | `beans omelette plate potatoes` | combo | combination-plate |

#### `pro_reason = drink` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chico mexicano refresco` | regional | drink |
| 1 | `bebida carne de lasagna res` | dish | drink |

#### `pro_reason = brand-specific` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `carpaccio serafina` | dish | brand-specific |
| 1 | `boru roll signature sushi` | dish | brand-specific |

#### `pro_reason = vague-basket` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `basket bbq bun sandwich` | dish | vague-basket |
| 1 | `basket rib tip wings` | combo | vague-basket |

#### `pro_reason = generic-sandwich` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `bun cheese italian turkey` | dish | generic-sandwich |
| 1 | `bun italian salad tuna` | dish | generic-sandwich |

#### `pro_reason = nondescript` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `burrito california choice taco` | combo | nondescript |
| 1 | `beans bread cream french` | combo | nondescript |

#### `pro_reason = combo-not-dish` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chicken pasta tenders tots` | combo | combo-not-dish |
| 1 | `cup fish gumbo sandwich shrimp` | combo | combo-not-dish |

#### `pro_reason = mixed-items` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chili pasta shrimp wonton` | combo | mixed-items |
| 1 | `alaskan baked halibut pasta salad` | dish | mixed-items |

#### `pro_reason = section` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `bel entrees moujadra riz` | regional | section |
| 1 | `angus prime ribeye signatures` | dish | section |

#### `pro_reason = base` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `base for paella valencian` | dish | base |
| 1 | `base for ink paella squid` | regional | base |

#### `pro_reason = nonstandard-name` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chicken chop fajita rotisserie` | dish | nonstandard-name |
| 1 | `bowl chicken hopped up` | dish | nonstandard-name |

#### `pro_reason = mismatched` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `filet mahi mahi mignon` | dish | mismatched |
| 1 | `beef ground kabob salmon` | combo | mismatched |

#### `pro_reason = vague-choice` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `curry goat lamb or shrimp` | combo | vague-choice |
| 1 | `chicken eggplant or primavera shrimp` | combo | vague-choice |

#### `pro_reason = mixed-proteins` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chicken quail rice roasted shrimp` | combo | mixed-proteins |
| 1 | `fish frog head pepper sauteed sichuan spicy` | regional | mixed-proteins |

#### `pro_reason = order` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `cheese chile one quesadilla relleno rice` | combo | order |
| 1 | `blue cheese one pieces ten wings` | wings | order |

#### `pro_reason = mixed-dishes` (2 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chicken chow fun mein or pasta pork roast` | dish | mixed-dishes |
| 1 | `chicken lo mein or pasta pork roast vegetables` | combo | mixed-dishes |

#### `pro_reason = generic-category` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 231 | `breakfast sandwich` | dish | generic-category |

#### `pro_reason = combined` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 80 | `calzone pepperoni stromboli` | combo | combined |

#### `pro_reason = side-topping` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 41 | `habanero onions` | dish | side-topping |

#### `pro_reason = bento` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 34 | `bento shrimp tempura` | dish | bento |

#### `pro_reason = unclear-combo` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 36 | `egg fried pasta rice` | dish | unclear-combo |

#### `pro_reason = chef` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 34 | `club newk sandwich` | dish | chef |

#### `pro_reason = plain` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 29 | `dog plain` | generic | plain |

#### `pro_reason = vague-reference` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 29 | `breakfast club` | dish | vague-reference |

#### `pro_reason = too-vague` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 29 | `con pan pollo` | regional | too-vague |

#### `pro_reason = notreal` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 32 | `chicken ribs` | dish | notreal |

#### `pro_reason = generic-fragment` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 25 | `nuggets` | dish | generic-fragment |

#### `pro_reason = vague-pairing` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 24 | `eggplant shrimp` | dish | vague-pairing |

#### `pro_reason = hybrid-name` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 25 | `enchilada tamal` | dish | hybrid-name |

#### `pro_reason = confusion` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 20 | `nigiri salmon sashimi` | dish | confusion |

#### `pro_reason = ambiguous-combination` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 14 | `chicken chipotle crunch steak` | combo | ambiguous-combination |

#### `pro_reason = unknown-burger` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 12 | `barnyard burger` | dish | unknown-burger |

#### `pro_reason = generic-modifier` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 12 | `homemade lasagna` | dish | generic-modifier |

#### `pro_reason = vague-mole` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 12 | `mexicano mole` | dish | vague-mole |

#### `pro_reason = pairing` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 12 | `biryani chicken dum ulavacharu` | regional | pairing |

#### `pro_reason = unbranded` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 11 | `passion pepperoni pizza` | dish | unbranded |

#### `pro_reason = cooking` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 9 | `cacciatore` | dish | cooking |

#### `pro_reason = love` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 9 | `lamb love vindaloo` | dish | love |

#### `pro_reason = seasonal` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 9 | `christmas pizza white` | dish | seasonal |

#### `pro_reason = vague-tofu` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 9 | `assorted tofu vegetables` | dish | vague-tofu |

#### `pro_reason = vague-vegs` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 9 | `chicken chinese vegs` | dish | vague-vegs |

#### `pro_reason = incoherent-mashup` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 9 | `bbq fry pizza steak` | combo | incoherent-mashup |

#### `pro_reason = contradictory-name` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 8 | `cashew chicken nuts vegetarian` | dish | contradictory-name |

#### `pro_reason = slogan` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 8 | `breakfast burrito eat veggies your` | dish | slogan |

#### `pro_reason = fusionunknown` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 8 | `japanese lasagna` | dish | fusionunknown |

#### `pro_reason = wham` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 7 | `beef burrito shredded wham` | combo | wham |

#### `pro_reason = go` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 7 | `go goat pesto pizza` | dish | go |

#### `pro_reason = generic_bowl` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 7 | `bowl fed grass steak` | dish | generic_bowl |

#### `pro_reason = vague_hula` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 6 | `bowl hula teriyaki` | combo | vague_hula |

#### `pro_reason = vague_berry_wrap` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 6 | `berry summer wrap` | combo | vague_berry_wrap |

#### `pro_reason = vague_tuscan_sun` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 6 | `pizza sun tuscan` | combo | vague_tuscan_sun |

#### `pro_reason = packaged` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 6 | `chicken crave pc tenders` | dish | packaged |

#### `pro_reason = unspecified` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 5 | `crystal scallops` | dish | unspecified |

#### `pro_reason = localized` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 5 | `bushwick calzone` | dish | localized |

#### `pro_reason = combined-non-dish` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 5 | `enchiladas seafood taco` | combo | combined-non-dish |

#### `pro_reason = non-standard-combo` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 5 | `filet lobster mignon roll` | combo | non-standard-combo |

#### `pro_reason = vague-adjectives` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 5 | `breakfast burrito deli delicious pastrami` | combo | vague-adjectives |

#### `pro_reason = fragmentary` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 5 | `bar coleslaw que sub` | combo | fragmentary |

#### `pro_reason = plural` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 4 | `sopas` | regional | plural |

#### `pro_reason = veggielicious` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 4 | `veggielicious wrap` | dish | veggielicious |

#### `pro_reason = fusion-ambiguous` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 4 | `burrito jambalaya` | dish | fusion-ambiguous |

#### `pro_reason = non-dish` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 4 | `taco tepache` | regional | non-dish |

#### `pro_reason = not-distinct` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 4 | `chicken sauteed shrimp` | combo | not-distinct |

#### `pro_reason = cooking-method` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 4 | `grilled pan shrimp` | dish | cooking-method |

#### `pro_reason = unrecognizable-combination` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 4 | `dumpling peanuts pork steamed` | dish | unrecognizable-combination |

#### `pro_reason = unrecognizable-term` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 4 | `burrito fish fried wham` | dish | unrecognizable-term |

#### `pro_reason = cheese-only` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `manchego` | dish | cheese-only |

#### `pro_reason = not-widely-recognizable` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `maverick pizza` | dish | not-widely-recognizable |

#### `pro_reason = raw-ingredient` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `butt pork` | dish | raw-ingredient |

#### `pro_reason = serving_style` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `basket scallop` | dish | serving_style |

#### `pro_reason = unknown-style` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `mimosa pizza` | dish | unknown-style |

#### `pro_reason = generic-term` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `chicken patties` | dish | generic-term |

#### `pro_reason = species` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `croaker fish` | dish | species |

#### `pro_reason = menu-specific-name` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `maximus pizza` | dish | menu-specific-name |

#### `pro_reason = addon` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `filet mignon solo` | dish | addon |

#### `pro_reason = vague-hybrid` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `chicken pizza taco` | combo | vague-hybrid |

#### `pro_reason = fusion-invalid` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `biryani pasta shrimp` | combo | fusion-invalid |

#### `pro_reason = grade` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `sirloin steak usda` | dish | grade |

#### `pro_reason = unrecognized-local` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `cheese reynosa taco` | dish | unrecognized-local |

#### `pro_reason = local-proper` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `crunch kemah roll` | dish | local-proper |

#### `pro_reason = possessive-name` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `asada carne escalante` | regional | possessive-name |

#### `pro_reason = vague-dumplings` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `dumplings entree leek scallion` | dish | vague-dumplings |

#### `pro_reason = redundant-meats` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `bacon burrito ham meat` | dish | redundant-meats |

#### `pro_reason = sandwich` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `baked loaded potato sandwich` | dish | sandwich |

#### `pro_reason = size-modifier` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `de mediana pizza queso` | dish | size-modifier |

#### `pro_reason = nada` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `chicken nada parmesan sub` | dish | nada |

#### `pro_reason = combined-dish-confusion` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 3 | `asada carne quesadilla taco` | combo | combined-dish-confusion |

#### `pro_reason = pasta` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `bucatini` | regional | pasta |

#### `pro_reason = vague-local` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `milwaukee pizza` | dish | vague-local |

#### `pro_reason = vague-proper-noun` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `burger crafthouse` | dish | vague-proper-noun |

#### `pro_reason = vague-regional` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `arizona burger` | dish | vague-regional |

#### `pro_reason = container` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `bowl pozole` | dish | container |

#### `pro_reason = concatenation` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `gyro kalamari` | combo | concatenation |

#### `pro_reason = not_iconic` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `burger tennessee` | dish | not_iconic |

#### `pro_reason = unknown-person` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `burrito pablin` | regional | unknown-person |

#### `pro_reason = generic-bowl` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `bowl parrilla` | regional | generic-bowl |

#### `pro_reason = menu-period` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `lunch taquitos` | dish | menu-period |

#### `pro_reason = chilerrito` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `burrito chilerrito` | regional | chilerrito |

#### `pro_reason = not_searchable` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `phish taco` | dish | not_searchable |

#### `pro_reason = size_only` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `chalupas grand` | dish | size_only |

#### `pro_reason = serving_size` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `picadillo quart` | regional | serving_size |

#### `pro_reason = generic_plate` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `huasteca plate` | regional | generic_plate |

#### `pro_reason = number` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `tostadas tres` | regional | number |

#### `pro_reason = yelm` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `roll sushi yelm` | dish | yelm |

#### `pro_reason = stryker` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `roll stryker sushi` | dish | stryker |

#### `pro_reason = mashed-up` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `breakfast burrito torta` | dish | mashed-up |

#### `pro_reason = rotating` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `du jour quiche` | dish | rotating |

#### `pro_reason = vague-bowl` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `bowl mushroom rice` | dish | vague-bowl |

#### `pro_reason = vague-mix` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `curry katsudon mix` | combo | vague-mix |

#### `pro_reason = vague-entree` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `entree pork pulled` | dish | vague-entree |

#### `pro_reason = person-name-roll` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `roll stephanie sushi` | dish | person-name-roll |

#### `pro_reason = bulk` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `botanero chicharron lb` | regional | bulk |

#### `pro_reason = named-roll` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `katrina maki roll` | dish | named-roll |

#### `pro_reason = creative-roll` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `maki rocketman roll` | dish | creative-roll |

#### `pro_reason = warrior` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `chicken udon warrior` | combo | warrior |

#### `pro_reason = meat` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `cabeza de res` | regional | meat |

#### `pro_reason = branded-unknown` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `cluck it waffle` | dish | branded-unknown |

#### `pro_reason = attrib` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `mediterranean pizza size` | dish | attrib |

#### `pro_reason = pb` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `flounder pb sub` | dish | pb |

#### `pro_reason = insufficient-identity` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `bbq sandwich tater` | dish | insufficient-identity |

#### `pro_reason = non-dish-name` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `eggplant free gluten pork` | dish | non-dish-name |

#### `pro_reason = vague-wrap` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `chicken soy vegetable wrap` | dish | vague-wrap |

#### `pro_reason = holiday` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `cinco de mayo platter` | dish | holiday |

#### `pro_reason = weight` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `bbq chicken pounds pulled` | dish | weight |

#### `pro_reason = menu-schedule` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `domingo menudo sabado` | regional | menu-schedule |

#### `pro_reason = rafa` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `grits rafa shrimp` | dish | rafa |

#### `pro_reason = twins` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `beef pepper tongue twins` | dish | twins |

#### `pro_reason = branded-ambiguous` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `bama chicken sandwich spicy` | dish | branded-ambiguous |

#### `pro_reason = mixed-sauces` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `alfredo fettuccine pasta primavera` | dish | mixed-sauces |

#### `pro_reason = medley` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `hk noodles pasta rice` | combo | medley |

#### `pro_reason = not-fried-biryani` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `biryani boneless chicken fried` | dish | not-fried-biryani |

#### `pro_reason = parts` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `chicken fried thighs wings` | dish | parts |

#### `pro_reason = choice-listing` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `baba ghanouj hummus or sandwich` | combo | choice-listing |

#### `pro_reason = incoherent-mix` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `ahi ceviche shrimp sushi tuna` | combo | incoherent-mix |

#### `pro_reason = platter-mix` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `pork pot scallops shrimp stickers` | combo | platter-mix |

#### `pro_reason = conflated` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `fried rice singapore style vermicelli` | dish | conflated |

#### `pro_reason = place-specific` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `brooklyn heights italian sausage subs` | dish | place-specific |

#### `pro_reason = irregular` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `pepper shrimp sour steak sweet` | combo | irregular |

#### `pro_reason = surf-turf` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `chicken grilled lime sauteed shrimp` | combo | surf-turf |

#### `pro_reason = combination-platter` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `chicken combination orange teriyaki` | combo | combination-platter |

#### `pro_reason = multiple_dishes` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `chicken fajita nachos or quesadilla steak` | combo | multiple_dishes |

#### `pro_reason = proper_name` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `alfredo fettuccine leonardo pasta` | pasta | proper_name |

#### `pro_reason = noodle-pasta` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `fried noodle pasta pork roasted stir` | dish | noodle-pasta |

#### `pro_reason = unknown_style` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `baked cheese mac palio pasta style` | dish | unknown_style |

#### `pro_reason = combo_plate` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `beef burrito chicken enchilada one tacos two` | combo | combo_plate |

#### `pro_reason = deli-list` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `beef cold corned ham or roast roasted turkey` | combo | deli-list |

#### `pro_reason = unknown-item` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `pescara sub` | dish | unknown-item |

#### `pro_reason = portmanteau` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 2 | `pizzawich sub` | dish | portmanteau |

#### `pro_reason = kidsmeal` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `bologna kidz` | dish | kidsmeal |

#### `pro_reason = unique-name` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `minoan pizza` | dish | unique-name |

#### `pro_reason = unrecognizable-abbreviation` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `bulgogi pb` | combo | unrecognizable-abbreviation |

#### `pro_reason = numbered` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `calzone ventidue` | dish | numbered |

#### `pro_reason = fabricated` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `burger codwich` | dish | fabricated |

#### `pro_reason = establishment` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `gyro village` | dish | establishment |

#### `pro_reason = atypical` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `grill spanakopita` | dish | atypical |

#### `pro_reason = regional_vague` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `ghent waffles` | regional | regional_vague |

#### `pro_reason = ingredient_prep` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `catfish eggs` | combo | ingredient_prep |

#### `pro_reason = temperature` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `bibimbap cold` | dish | temperature |

#### `pro_reason = fusion-nonstandard` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `quesadilla wings` | dish | fusion-nonstandard |

#### `pro_reason = vague-concept` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `cajun skillet` | dish | vague-concept |

#### `pro_reason = proper-noun-location` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `plano skillets` | dish | proper-noun-location |

#### `pro_reason = size-descriptor` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `gigantic tenders` | dish | size-descriptor |

#### `pro_reason = fantasy` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `dragon tamales` | dish | fantasy |

#### `pro_reason = neologism` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `rollrrito tofu` | gibberish | neologism |

#### `pro_reason = composition` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `birria flatbread` | dish | composition |

#### `pro_reason = preparation` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `split wings` | dish | preparation |

#### `pro_reason = exotic` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `bear pelmeni` | dish | exotic |

#### `pro_reason = not_dish` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `burrito cadillac` | dish | not_dish |

#### `pro_reason = unspecific` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `borrego gordita` | regional | unspecific |

#### `pro_reason = quirky` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `gaijin katsu` | regional | quirky |

#### `pro_reason = not-a-dish` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `quiche soup` | combo | not-a-dish |

#### `pro_reason = part` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chicken neck` | dish | part |

#### `pro_reason = unestablished` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `charros rice` | regional | unestablished |

#### `pro_reason = unrecognizable-modifier` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `burger frjtz` | dish | unrecognizable-modifier |

#### `pro_reason = unrecognizable-word` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `cheeseburger fryders` | dish | unrecognizable-word |

#### `pro_reason = unrecognized-name` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `huachicolero roll` | regional | unrecognized-name |

#### `pro_reason = obscure-roll` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `metropolitan roll` | dish | obscure-roll |

#### `pro_reason = playful-nonstandard` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `burger cheesus` | dish | playful-nonstandard |

#### `pro_reason = unnatural` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `enchiladas mounted` | dish | unnatural |

#### `pro_reason = atlantis` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `atlantis burger` | dish | atlantis |

#### `pro_reason = uncooked` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `raw tamales` | dish | uncooked |

#### `pro_reason = notadish` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `sandwich spring` | dish | notadish |

#### `pro_reason = unknown-word` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `bacon bun steakie` | dish | unknown-word |

#### `pro_reason = slang-pizza` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `pizza za` | dish | slang-pizza |

#### `pro_reason = term` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `ala carta enchilada` | dish | term |

#### `pro_reason = equipment` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `cheesesteak flat top` | dish | equipment |

#### `pro_reason = unclear-concept` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `basket cod wrap` | combo | unclear-concept |

#### `pro_reason = serving-format` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chicken tender tray` | dish | serving-format |

#### `pro_reason = jerky` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `beef firfir jerky` | regional | jerky |

#### `pro_reason = abbrev` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `garlic nw pasta` | dish | abbrev |

#### `pro_reason = chutney` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chutney curry ginger` | dish | chutney |

#### `pro_reason = tipsy` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `birria nachos tipsy` | dish | tipsy |

#### `pro_reason = fictional-reference` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `clubber lang taco` | branded | fictional-reference |

#### `pro_reason = branding` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `aroma hamburguesa sandwich` | dish | branding |

#### `pro_reason = vague-fusion` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `noodles pad saigon` | regional | vague-fusion |

#### `pro_reason = quantity-not-dish` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chorizo pound taco` | dish | quantity-not-dish |

#### `pro_reason = cocktail` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `bulgogi fashioned old` | dish | cocktail |

#### `pro_reason = dietary` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chicken gf parm` | dish | dietary |

#### `pro_reason = pop-culture` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `one piece waffle` | dish | pop-culture |

#### `pro_reason = tinfoil` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `fillet fish tinfoil` | dish | tinfoil |

#### `pro_reason = ingredients-only` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chicken salmon shrimp` | combo | ingredients-only |

#### `pro_reason = place-name` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `burger mount ogden` | dish | place-name |

#### `pro_reason = sides` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `beans rice tamales` | dish | sides |

#### `pro_reason = named-breakfast` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `desayuno pueblo viejo` | regional | named-breakfast |

#### `pro_reason = compound` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `antojito asada tortas` | regional | compound |

#### `pro_reason = portion-size` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `gyro micro portion` | dish | portion-size |

#### `pro_reason = generic-boast` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `award ribs winning` | dish | generic-boast |

#### `pro_reason = orders` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `catfish filet orders` | dish | orders |

#### `pro_reason = vague-sides` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `grilled mushrooms onions` | combo | vague-sides |

#### `pro_reason = day-special` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `bao taco tuesday` | combo | day-special |

#### `pro_reason = obscure-brand` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chicken tarbouch wrap` | regional | obscure-brand |

#### `pro_reason = zurrito` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `greek salad zurrito` | combo | zurrito |

#### `pro_reason = galaxy` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `club galaxy wrap` | dish | galaxy |

#### `pro_reason = flan` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chimichurri flan steak` | combo | flan |

#### `pro_reason = fictional` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `irish leprechaun stew` | dish | fictional |

#### `pro_reason = unrecognizable-fusion` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `burrito roll spring` | combo | unrecognizable-fusion |

#### `pro_reason = unrecognized-modifier` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `birria laotino taco` | regional | unrecognized-modifier |

#### `pro_reason = slang-name` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chingon spicy taco` | dish | slang-name |

#### `pro_reason = generic-bites` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `bites chicken fried` | dish | generic-bites |

#### `pro_reason = simple-preparation` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `arrosto organico pollo` | regional | simple-preparation |

#### `pro_reason = generic-steak` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `angus certified ribeye` | dish | generic-steak |

#### `pro_reason = poetic-not-dish` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `cielo del tacos` | regional | poetic-not-dish |

#### `pro_reason = noticonic` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `big dog pizza` | dish | noticonic |

#### `pro_reason = noise` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `brisket each kolache` | regional | noise |

#### `pro_reason = character` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `foghorn leghorn sandwich` | dish | character |

#### `pro_reason = craftless` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chicken craver grilled` | dish | craftless |

#### `pro_reason = ingredient,` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `clam meat razor` | dish | ingredient, |

#### `pro_reason = mix` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `crepe crepiano mix` | combo | mix |

#### `pro_reason = unknown-combo` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `durango shrimp steak` | dish | unknown-combo |

#### `pro_reason = event` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `lagunera taco taquiza` | regional | event |

#### `pro_reason = vessel` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `curry thai wok` | dish | vessel |

#### `pro_reason = joke` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `burger cheesy politician` | dish | joke |

#### `pro_reason = vague-taco` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `american made taco` | dish | vague-taco |

#### `pro_reason = weird-ingredient` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `blackened burger hemp` | dish | weird-ingredient |

#### `pro_reason = vague-patty` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `light melt patty` | dish | vague-patty |

#### `pro_reason = branded-no-recipe` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `california dreamin gf sandwich` | dish | branded-no-recipe |

#### `pro_reason = strawberry` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chicken moo shu strawberry` | dish | strawberry |

#### `pro_reason = vague-platter` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `almond combination platter shrimp` | combo | vague-platter |

#### `pro_reason = vague_combination` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chicken fried hibachi skillet` | dish | vague_combination |

#### `pro_reason = brand-ingredient` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `boar head pepperoni` | dish | brand-ingredient |

#### `pro_reason = ingredient_only` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `boar head provolone` | dish | ingredient_only |

#### `pro_reason = proper-noun-possessive` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `deluxe geno pizza` | dish | proper-noun-possessive |

#### `pro_reason = proprietary_name` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `harbor master sandwich wrap` | dish | proprietary_name |

#### `pro_reason = unknown-sub` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chicken farm sub` | dish | unknown-sub |

#### `pro_reason = option-split` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `beef chicken curry or` | combo | option-split |

#### `pro_reason = grocery-item` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `dumpling frozen lettuce pork` | dish | grocery-item |

#### `pro_reason = state` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `dumpling fennel frozen pork` | dish | state |

#### `pro_reason = board` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `board focaccia house salumi` | dish | board |

#### `pro_reason = implausible-phrase` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chapali kabob only skewer` | combo | implausible-phrase |

#### `pro_reason = jumbled-tokens` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `burger burrito poke salmon` | combo | jumbled-tokens |

#### `pro_reason = unlikely-fusion` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `bihari calzone chicken kebab` | dish | unlikely-fusion |

#### `pro_reason = proprietary-blend` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `blend butchers cheeseburger sandwich` | dish | proprietary-blend |

#### `pro_reason = choice-not-dish` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `baba ghanouj hummus or` | combo | choice-not-dish |

#### `pro_reason = regional-vague` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chicken dc hot sandwich` | dish | regional-vague |

#### `pro_reason = container-not-dish` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `basket french fry sidewinder` | combo | container-not-dish |

#### `pro_reason = diet-brand` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `atkins roll salmon tuna` | dish | diet-brand |

#### `pro_reason = vague-signature` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `cheese ham sandwich signature` | dish | vague-signature |

#### `pro_reason = kalypso` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `grilled kalypso shrimp` | dish | kalypso |

#### `pro_reason = chef-special` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chef curry panang seafood` | dish | chef-special |

#### `pro_reason = pasta-list` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `fettuccine or spaghetti ziti` | dish | pasta-list |

#### `pro_reason = nickname` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chicken fried sandwich sandy` | dish | nickname |

#### `pro_reason = combo-list` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `flatbread philly pizza wings` | combo | combo-list |

#### `pro_reason = station` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `filling reuben sandwich station` | dish | station |

#### `pro_reason = specialized` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `breakfast sandwich torpedo uss` | dish | specialized |

#### `pro_reason = custom-order` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `california protein style turkey` | dish | custom-order |

#### `pro_reason = recipe` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `mexican original pambazo recipe` | regional | recipe |

#### `pro_reason = kid's-meal` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chalupa child plate` | dish | kid's-meal |

#### `pro_reason = inaccurate` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `king salmon sushi toro` | combo | inaccurate |

#### `pro_reason = hype` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `biggest brisket burger sandwich` | dish | hype |

#### `pro_reason = vague-preparation` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `eggplant grilled oil scallion` | dish | vague-preparation |

#### `pro_reason = stylized-spelling` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chicken hawt royale sandwich` | dish | stylized-spelling |

#### `pro_reason = vague-region` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `burger sandwich shore south` | dish | vague-region |

#### `pro_reason = house-specialty` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `el general roll sushi` | dish | house-specialty |

#### `pro_reason = sausage` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `country polish sausage smoked` | dish | sausage |

#### `pro_reason = no` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chicken delicias enchilada shredded` | combo | no |

#### `pro_reason = instructions` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `blackened grilled or tilapia` | dish | instructions |

#### `pro_reason = kids` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `childs flour plate quesadilla` | dish | kids |

#### `pro_reason = location_specific` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `hot park ridge wings` | dish | location_specific |

#### `pro_reason = team` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `bacon bulls burger chicago` | combo | team |

#### `pro_reason = not_a_dish` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `champion cheese plate sandwich` | dish | not_a_dish |

#### `pro_reason = kitchen` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `arepa kitchen zulia` | regional | kitchen |

#### `pro_reason = redundant-fragments` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `bone plate rib ribs` | dish | redundant-fragments |

#### `pro_reason = possessive-person` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `abuela de la mole` | regional | possessive-person |

#### `pro_reason = instruction-fragment` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `beans burrito no pastor` | dish | instruction-fragment |

#### `pro_reason = housespecial` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chicken dk dosa special` | combo | housespecial |

#### `pro_reason = limited-time` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `blazing chicken taco wrap` | dish | limited-time |

#### `pro_reason = modifiervague` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `avocado choice eggs toast` | dish | modifiervague |

#### `pro_reason = dubious` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `el fajita matatdor parrillada` | regional | dubious |

#### `pro_reason = vague-ingredient` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `boiled head lb shrimp` | dish | vague-ingredient |

#### `pro_reason = non-traditional` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `bulgogi rice seafood spicy` | combo | non-traditional |

#### `pro_reason = improbable` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `bonless charsi chicken karahi` | regional | improbable |

#### `pro_reason = scheduled-item` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `domingo pozole sabado` | regional | scheduled-item |

#### `pro_reason = trio-plate` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `ribs shrimp steak trio` | combo | trio-plate |

#### `pro_reason = limited` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `asian limited ramen spicy` | combo | limited |

#### `pro_reason = disjoint` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `pasta risotto seasonal vegetable` | dish | disjoint |

#### `pro_reason = mealperiod` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `lunch pasta pesto vegetable` | combo | mealperiod |

#### `pro_reason = incomplete-dish` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `bacon pulled` | generic | incomplete-dish |

#### `pro_reason = sauce-not-dish` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `bean black oyster sauce steamed` | dish | sauce-not-dish |

#### `pro_reason = meta` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chicken course main spice tikka` | combo | meta |

#### `pro_reason = imitation` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `crab imitation roe soup tofu` | dish | imitation |

#### `pro_reason = meal-platter` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `asado beans pollo rice tortillas` | combo | meal-platter |

#### `pro_reason = possessive-unclear` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `brie burger cheese chester` | dish | possessive-unclear |

#### `pro_reason = surname` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `country fried sonnenberg steak` | regional | surname |

#### `pro_reason = holiday-platter` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `cinco de mayo platter taco` | regional | holiday-platter |

#### `pro_reason = obscure-name` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `bacon bolt burger classic egg` | dish | obscure-name |

#### `pro_reason = packaging` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `grilled pastrami reuben sub tub` | combo | packaging |

#### `pro_reason = inconsistent` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `curry fried ham rice vegetarian` | dish | inconsistent |

#### `pro_reason = odd-combination` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `camarones cocktail de la marinara` | dish | odd-combination |

#### `pro_reason = vague-pasta` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `green noodles oil onion pasta` | combo | vague-pasta |

#### `pro_reason = combo-listing` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `birria carnitas fajita lengua machito` | combo | combo-listing |

#### `pro_reason = unclear-fragments` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chicken ga lemongrass xa xiano` | regional | unclear-fragments |

#### `pro_reason = messy` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `beef comales fajita los parillada` | regional | messy |

#### `pro_reason = confused-name` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chicken con pollo salsa suiza un` | regional | confused-name |

#### `pro_reason = brand-not-dish` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `boar cheese cream havarti head` | combo | brand-not-dish |

#### `pro_reason = qualifier` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `angus black burger certified cheese saloon` | dish | qualifier |

#### `pro_reason = instant` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `instant noodles oriental style wai` | dish | instant |

#### `pro_reason = meal-deal` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `basket chicken chips fried lunch plate` | combo | meal-deal |

#### `pro_reason = house-name` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `crazy nachos pork ribs roja salsa` | dish | house-name |

#### `pro_reason = incoherent-fragments` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `grilled leg pilaf seafood shrimp turkey` | dish | incoherent-fragments |

#### `pro_reason = house-plate` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `breast chicken grilled house plate seasoned` | combo | house-plate |

#### `pro_reason = count` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `california pieces roll sushi two vegetable` | dish | count |

#### `pro_reason = random` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `fish fried pasta rice salt sausage` | dish | random |

#### `pro_reason = unidentifiable` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `cheese crispy el ench sabroso taco` | combo | unidentifiable |

#### `pro_reason = combination-vague` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `bean chalupa chicken cream enchilada sour` | combo | combination-vague |

#### `pro_reason = choice-parsing` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `fun lo mei mein or shrimp` | dish | choice-parsing |

#### `pro_reason = temo` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `avocado bacon burger ham temo` | burger | temo |

#### `pro_reason = duke` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `bacon beef duke jalapeno steak wrapped` | dish | duke |

#### `pro_reason = listing` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `guacamole mushrooms or quesadilla rice salad spinach` | combo | listing |

#### `pro_reason = jargon` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `breaded chicken hand jb sandwich tender` | dish | jargon |

#### `pro_reason = separate` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `egg grilled pork roll shrimp skewers` | dish | separate |

#### `pro_reason = flavors` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `bbq buffalo chile or plain sweet wings` | combo | flavors |

#### `pro_reason = multi-option` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `general or sauce sesame tofu tso` | dish | multi-option |

#### `pro_reason = menu-phrase` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chimichanga choice enchilada one or tamal` | combo | menu-phrase |

#### `pro_reason = choice-format` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `bean beans beef burritos ground or rice` | combo | choice-format |

#### `pro_reason = menu-choice` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `grilled meat or rolls shrimp spring vermicelli` | combo | menu-choice |

#### `pro_reason = combo-items` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `bowl grilled noodles pork roll shrimp spring` | combo | combo-items |

#### `pro_reason = ingredient-mismatch` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `angel hair noodles pasta rice singapore vegetables` | combo | ingredient-mismatch |

#### `pro_reason = options-list` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `fresh or roll salmon sushi tuna yellowtail` | dish | options-list |

#### `pro_reason = gizzard` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chicken cucumber fried gizzard ground pork skin stir` | combo | gizzard |

#### `pro_reason = elefante` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `breaded de elefante fried milanesa orejas steak` | regional | elefante |

#### `pro_reason = assorted` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `chinese chives dumplings fish mackerel meat pork steamed` | combo | assorted |

#### `pro_reason = pizza` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `crust greek italiano pizza sicilian speciality thick` | dish | pizza |

#### `pro_reason = alternative` (1 pro-vetoes)

| count | canonical | gemini reason | pro reason |
|---|---|---|---|
| 1 | `beef clay flounder hot numbing or pot tofu` | combo | alternative |

---

## BOTH_DROP — both models said DROP (already-validated drops)

Re-showing top of bucket for completeness.

### Top 20 highest-count BOTH_DROP

| count | canonical | gemini reason | pro reason |
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

---

## PRO_RESCUE — Gemini said DROP, Pro said KEEP (already-validated rescues)

Re-showing top of bucket for completeness.

### Top 20 highest-count PRO_RESCUE

| count | canonical | gemini said DROP because | pro said KEEP because |
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
