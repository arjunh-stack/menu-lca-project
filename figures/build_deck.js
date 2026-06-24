// Build a research-talk slide deck from the menu-item-impact figures.
const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");
const imageSizeMod = require("image-size");
const sizeOf = imageSizeMod.imageSize || imageSizeMod.default || imageSizeMod;

const FIG_DIR = process.env.FIG_DIR || ".";

// Palette: greens for a food/environment topic, terracotta accent.
const INK = "1F2A24";       // near-black green
const FOREST = "2C5F2D";    // primary
const MOSS = "97BC62";      // secondary
const ACCENT = "B85042";    // terracotta accent
const MUTE = "6B7A70";      // muted caption
const PAPER = "F7F6F1";     // light slide background
const DARK = "1F2A24";      // dark slide background

const HEAD = "Georgia";
const BODY = "Calibri";

// Slide geometry (LAYOUT_WIDE = 13.33 x 7.5)
const SW = 13.33, SH = 7.5;

// Figure list, in narrative order. Each entry -> one content slide.
// section marks a chapter for the running footer.
const figures = [
  { file: "fig_hero_manifold.png", section: "Overview",
    title: "The dish manifold, painted by impact, health & price",
    caption: "39,166 canonical dishes embedded in a shared UMAP layout; each panel re-colors the same map by one metric (RdYlBu: red = worse / pricier, blue = better / cheaper)." },

  { file: "fig1_health_by_cuisine.png", section: "By cuisine",
    title: "Nutrition & health vary widely by cuisine",
    caption: "Nutri-Score and health impact (ΔYLL) per cuisine. Each canonical dish counted once (unweighted). Box = IQR, whiskers = P5–P95, line = median, diamond = mean." },
  { file: "fig1_health_by_cuisine_weighted.png", section: "By cuisine",
    title: "Nutrition & health by cuisine — menu-frequency weighted",
    caption: "Same panels as the previous slide, weighted by how often each dish actually appears on menus." },

  { file: "fig1_impact_by_cuisine.png", section: "By cuisine",
    title: "Environmental impact by cuisine",
    caption: "GHG emissions, freshwater use and land use per cuisine. Each canonical dish counted once (unweighted)." },
  { file: "fig1_impact_by_cuisine_weighted.png", section: "By cuisine",
    title: "Environmental impact by cuisine — menu-frequency weighted",
    caption: "Same panels as the previous slide, weighted by menu frequency." },

  { file: "fig2_real_menu.png", section: "Menus in practice",
    title: "Real menus, scored: which item is actually better?",
    caption: "Actual restaurant menus and prices from the dataset; color strip = combined carbon + Nutri-Score (red = worse). kg CO₂e per kg, health grade A–E." },
  { file: "fig2_menu_pizzeria.png", section: "Menus in practice",
    title: "A greener, healthier menu — without leaving the cuisine",
    caption: "The Pizzeria: each dish swapped for its best canonical neighbor within a flexibility sphere (cosine r ≤ 0.2). −39% menu carbon; 5/5 dishes made greener and at least as healthy." },
  { file: "fig2_menu_subshop.png", section: "Menus in practice",
    title: "Reimagining the sub shop within the same cuisine",
    caption: "The Sub Shop: same within-cuisine substitution approach as the pizzeria example." },

  { file: "fig3_flexibility.png", section: "Flexibility",
    title: "Dietary flexibility vs. best-case improvement",
    caption: "Best-case reduction achievable as a function of willingness to substitute (cosine radius). Best substitute within a sphere; unweighted (one dish = one point). Line = mean, band = IQR." },
  { file: "fig3_flexibility_weighted.png", section: "Flexibility",
    title: "Flexibility vs. improvement — menu-frequency weighted",
    caption: "Same curves, weighted by how often dishes appear on real menus." },

  { file: "fig7_macro_flexibility.png", section: "Flexibility",
    title: "Flexibility while keeping the macros similar",
    caption: "38,683 dishes with a macro profile. Macro-matched curves (orange) require total variation of protein/fat/carb calorie shares ≤ 10 vs. any substitute (grey)." },

  { file: "fig4_alignment.png", section: "Alignment",
    title: "Do smarter diet decisions have planetary alignment?",
    caption: "Whole-dataset alignment of 'badness' across metrics, plus within-sphere co-benefit panels at flexibility r = 0.1. Density = log count of dishes; win–win rates 72–77%." },

  { file: "fig5_cost_serving.png", section: "Cost",
    title: "Does price track environmental & health impact? (per serving)",
    caption: "Footprints per serving (impact scaled by dish serving mass) vs. menu price. Price capped at 98th percentile; unweighted. Spearman ρ shown per panel." },
  { file: "fig5_cost_serving_weighted.png", section: "Cost",
    title: "Price vs. impact, per serving — menu-frequency weighted",
    caption: "Same per-serving relationships, weighted by menu frequency." },
  { file: "fig5_cost_kg.png", section: "Cost",
    title: "Does price track environmental & health impact? (per kg)",
    caption: "Footprints per kg (Poore–Nemecek intensity) vs. menu price. Price capped at 98th percentile; unweighted." },
  { file: "fig5_cost_kg_weighted.png", section: "Cost",
    title: "Price vs. impact, per kg — menu-frequency weighted",
    caption: "Same per-kg relationships, weighted by menu frequency." },

  { file: "fig6_geographic.png", section: "Geography",
    title: "Geographic equity of dish impact & nutrition",
    caption: "1,867 US ZIP codes (≥40 priced menu rows each); dish metrics joined from the manifold, affluence proxied by ZIP mean menu price." },

  { file: "figS_dish_similarity.png", section: "Supplement",
    title: "S1 · Dish-to-dish compositional similarity",
    caption: "110,261 dishes. (a) Embedding cosine ranks compositional likeness but is not a 1:1 of shared recipe. (b) Actual ingredient overlap with nearest neighbor: median 62% of types, 83% of mass." },
  { file: "figS_ef_by_category.png", section: "Supplement",
    title: "S2 · Emission-factor source coverage by impact category",
    caption: "GHG from AGRIBALYSE v3.2 or SU-EATABLE LIFE; water, land, acidification & eutrophication carried only by AGRIBALYSE. 96–99% of ingredients covered." },
  { file: "figS_ef_sources.png", section: "Supplement",
    title: "S3 · Provenance of ingredient emission factors",
    caption: "Each ingredient matched to AGRIBALYSE v3.2 or SU-EATABLE LIFE. AGRIBALYSE leads by count but its share falls under occurrence- and mass-weighting." },
];

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "menu-item-impact";
pres.title = "Menu Item Impact — Figures";

const dim = (f) => {
  const b = fs.readFileSync(path.join(FIG_DIR, f));
  const d = sizeOf(b);
  return { w: d.width, h: d.height };
};

// ---- Title slide ----
const t = pres.addSlide();
t.background = { color: DARK };
t.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.28, h: SH, fill: { color: ACCENT } });
t.addText("THE MENU ITEM IMPACT PROJECT", {
  x: 0.9, y: 2.05, w: 11.5, h: 0.5, fontFace: BODY, fontSize: 16, color: MOSS,
  bold: true, charSpacing: 3, margin: 0,
});
t.addText("Environmental & health impact of restaurant dishes", {
  x: 0.9, y: 2.55, w: 11.6, h: 1.6, fontFace: HEAD, fontSize: 40, color: PAPER,
  bold: true, margin: 0, lineSpacingMultiple: 1.0,
});
t.addText("A figure tour of the 39,166-dish manifold — by cuisine, menu, flexibility, cost and geography", {
  x: 0.9, y: 4.25, w: 11.4, h: 0.8, fontFace: BODY, fontSize: 18, color: "CFD6CE", margin: 0,
});
t.addText(`${figures.length} figures`, {
  x: 0.9, y: 6.5, w: 6, h: 0.4, fontFace: BODY, fontSize: 13, color: MUTE, margin: 0,
});

// ---- Figure slides ----
const TOP = 1.18;          // top of image zone
const BOT_CAP = 0.78;      // reserved for caption
const MAXW = SW - 0.9;     // horizontal padding 0.45 each side
const MAXH = SH - TOP - BOT_CAP - 0.08;

figures.forEach((fig) => {
  const s = pres.addSlide();
  s.background = { color: PAPER };

  // Section tag
  s.addText(fig.section.toUpperCase(), {
    x: 0.6, y: 0.32, w: 6, h: 0.35, fontFace: BODY, fontSize: 12, color: ACCENT,
    bold: true, charSpacing: 2, margin: 0,
  });
  // Title
  s.addText(fig.title, {
    x: 0.6, y: 0.62, w: SW - 1.2, h: 0.7, fontFace: HEAD, fontSize: 24, color: INK,
    bold: true, margin: 0, valign: "top",
  });

  // Image sized to fit, preserving aspect ratio, centered in zone
  const { w: pw, h: ph } = dim(fig.file);
  const ar = pw / ph;
  let iw = MAXW, ih = iw / ar;
  if (ih > MAXH) { ih = MAXH; iw = ih * ar; }
  const ix = (SW - iw) / 2;
  const iy = TOP + (MAXH - ih) / 2;
  s.addImage({ path: path.join(FIG_DIR, fig.file), x: ix, y: iy, w: iw, h: ih });

  // Caption
  s.addText(fig.caption, {
    x: 0.6, y: SH - 0.72, w: SW - 1.2, h: 0.6, fontFace: BODY, fontSize: 11,
    color: MUTE, italic: true, margin: 0, valign: "top",
  });
});

const out = process.env.OUT || "menu_item_impact_figures.pptx";
pres.writeFile({ fileName: out }).then((f) => console.log("Wrote", f));
