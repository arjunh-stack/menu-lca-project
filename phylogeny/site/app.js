/* ============================================================
   Dish Compositional Phylogeny — frontend
   Two linked views over the same 39k dishes:
     · Phylogeny  — collapsible HAC dendrogram (zoom into clades)
     · Manifold   — UMAP scatter (no forced single-parent)
   Click a dish to lazy-load its recipe + LCA detail.
   ============================================================ */
'use strict';

/* ---- RdYlBu palette (the only hues; design rule 03) ---------- */
const RAMP = ['#A50026','#D73027','#F46D43','#FDAE61','#FEE090','#FFFFBF',
              '#E0F3F8','#ABD9E9','#74ADD1','#4575B4','#313695'];
// interpolator with 0 = cold/blue/low, 1 = hot/red/high
const rampInterp = d3.interpolateRgbBasis(RAMP.slice().reverse());
const NEUTRAL = '#c4c6cf';
// categorical swatches for cuisine — spread across the ramp, skipping the
// pale near-zero yellows so adjacent categories stay legible
const CAT = ['#D73027','#4575B4','#F46D43','#74ADD1','#A50026','#313695',
             '#FDAE61','#ABD9E9','#6a6d78','#1b1f2a'];

const OVERLAYS = {
  cuisine:      {kind:'cat',  field:'cuisine',      label:'Restaurant cuisine'},
  protein_type: {kind:'cat',  field:'protein_type', label:'Primary protein'},
  carb_type:    {kind:'cat',  field:'carb_type',    label:'Primary carbohydrate'},
  kcal:         {kind:'cont', field:'kcal',    label:'Calories / serving'},
  protein:      {kind:'cont', field:'protein', label:'Protein g / serving'},
  fat:          {kind:'cont', field:'fat',     label:'Fat g / serving'},
  carb:         {kind:'cont', field:'carb',    label:'Carbs g / serving'},
  nutriscore:   {kind:'cont', field:'nutriscore',
                 label:'NutriScore · 0 best → 100 worst'},
  grade:        {kind:'cat',  field:'grade',   label:'NutriScore grade (A–E)'},
  mealhealth:   {kind:'cont', field:'mealhealth',
                 label:'Health impact · yrs of life lost/day-for-life (red = worse)'},
  ghg:          {kind:'cont', field:'ghg',   label:'GHG kg CO₂e / kg'},
  water:        {kind:'cont', field:'water', label:'Water m³ / kg'},
  land:         {kind:'cont', field:'land',  label:'Land-use Pt / kg'},
  n_ingredients:{kind:'cont', field:'n_ingredients', label:'Ingredient count'},
};

/* ---- state --------------------------------------------------- */
const S = {
  manifest:null, tree:null, umap:null,
  view:'tree', overlay:'cuisine',
  selected:null,                 // cluster_id
  shardCache:new Map(),
  catMap:new Map(),              // category value -> color
  ranks:{},                      // overlay -> sorted value array
  leaves:[],                     // all dish records (from tree leaves)
  ingMetric:'ghg',               // detail-panel ingredient-contribution metric
  currentLca:null,               // lca of the dish shown in the detail panel
};

// per-ingredient impact the detail panel can break down (toggle)
const ING_METRICS = {
  ghg:   {field:'ghg_g',   label:'GHG',   unit:'g CO₂e', dec:0, ramp:0.82},
  water: {field:'water_l', label:'Water', unit:'L',      dec:1, ramp:0.20},
  land:  {field:'land_pt', label:'Land',  unit:'Pt',     dec:2, ramp:0.60},
};

const $ = s => document.querySelector(s);
const fmt = (v,d=2) => v==null||isNaN(v) ? '—' : (+v).toFixed(d);
const fmtInt = v => v==null ? '—' : (+v).toLocaleString();

/* ============================================================
   BOOT
   ============================================================ */
// optional deep-link: ?view=map&overlay=nutriscore picks the initial
// view + colour overlay (also lets the overlay state be shared/bookmarked)
function applyUrlState(){
  const q = new URLSearchParams(location.search);
  const v = q.get('view');
  if(v==='map' || v==='tree') S.view = v;
  const o = q.get('overlay');
  if(o && OVERLAYS[o]) S.overlay = o;
}

async function boot(){
  applyUrlState();
  setStatus('loading data…');
  try {
    S.manifest = await fetchJSON('data/manifest.json');
    S.tree     = await fetchJSON('data/tree.json');
    S.umap     = await fetchJSON('data/umap.json').catch(()=>null);
  } catch(e){
    setStatus('');
    $('#stage').innerHTML =
      '<div style="padding:40px;font-size:14px;color:#6a6d78">'+
      'Could not load <code>data/</code>. Run the tool through a local '+
      'server:<br><br><code>cd site &amp;&amp; python3 -m http.server 8000</code>'+
      '<br>then open <code>http://localhost:8000</code></div>';
    return;
  }

  // flatten leaves once — they carry every overlay field
  collectLeaves(S.tree);
  buildScales();
  showBuildMeta();

  renderTree();
  if (S.umap) renderMap();
  buildLegend();
  wireControls();
  syncControls();
  setStatus(`${fmtInt(S.leaves.length)} dishes`);
}

// reflect S.view / S.overlay (possibly set from the URL) into the DOM
function syncControls(){
  const sel = $('#overlay'); if(sel) sel.value = S.overlay;
  document.querySelectorAll('#view-toggle button')
    .forEach(b=> b.classList.toggle('active', b.dataset.view===S.view));
  $('#stage').classList.toggle('map', S.view==='map');
  if(S.view==='map' && S.umap){ resizeMap(); drawMap(); }
}

function fetchJSON(url){ return fetch(url).then(r=>{
  if(!r.ok) throw new Error(url+' '+r.status); return r.json(); }); }

function setStatus(t){ $('#status').textContent = t; }

function showBuildMeta(){
  const m = S.manifest || {};
  $('#build-meta').innerHTML =
    `${fmtInt(m.n_dishes)} dishes · ${fmtInt(m.n_clade_labels)} clades`+
    `<br>layout: ${m.umap_method||'—'} · built ${(m.built_at||'').slice(0,10)}`;
  $('#foot-right').textContent =
    `min-count v1 · ${m.n_shards} shards · ${m.umap_method} manifold`;
}

function collectLeaves(node){
  if(node.leaf){ S.leaves.push(node); return; }
  (node.children||[]).forEach(collectLeaves);
}

/* ---- colour scales ------------------------------------------ */
function buildScales(){
  // categorical overlays — colour by frequency rank (commonest gets CAT[0])
  for(const fld of ['cuisine','protein_type','carb_type']){
    const freq = d3.rollup(S.leaves, v=>v.length, d=>d[fld]);
    Array.from(freq.entries())
      .filter(([k])=>k!=null && k!=='')
      .sort((a,b)=>b[1]-a[1])
      .forEach(([v],i)=> S.catMap.set(fld+':'+v, CAT[i%CAT.length]));
  }
  // "no primary protein/carb" and unknown cuisine read as neutral grey
  S.catMap.set('protein_type:none', NEUTRAL);
  S.catMap.set('carb_type:none', NEUTRAL);
  S.catMap.set('cuisine:Other', NEUTRAL);
  // NutriScore grade is ORDERED (A best → E worst), so it gets fixed hues
  // along the ramp rather than frequency-rank colours: A blue (good) →
  // C yellow → E red (poor). Stays within the RdYlBu palette (rule 03).
  [['A',0.04],['B',0.28],['C',0.5],['D',0.72],['E',0.96]]
    .forEach(([g,t])=> S.catMap.set('grade:'+g, rampInterp(t)));
  // continuous overlays — sorted value array per field for rank colouring
  for(const k of ['ghg','water','land','kcal','protein','fat','carb',
                  'n_ingredients','nutriscore','mealhealth']){
    S.ranks[k] = S.leaves.map(d=>d[k]).filter(v=>v!=null && !isNaN(v))
                         .sort(d3.ascending);
  }
}

// rank in [0,1] — robust to outliers, median maps to ~0.5 (yellow)
function rankOf(v, key){
  const a = S.ranks[key];
  if(!a || !a.length || v==null || isNaN(v)) return null;
  return d3.bisectLeft(a, v) / a.length;
}

function colorOf(d){
  const o = OVERLAYS[S.overlay];
  if(o.kind==='cat'){
    const v = d[o.field];
    if(v==null || v==='') return NEUTRAL;
    return S.catMap.get(S.overlay+':'+v) || NEUTRAL;
  }
  const r = rankOf(d[o.field], o.field);
  return r==null ? NEUTRAL : rampInterp(r);
}

/* ============================================================
   PHYLOGENY (collapsible dendrogram)
   ============================================================ */
let treeRoot, treeG, treeZoom, treeSvg;
const DX = 15, DY = 215;          // leaf spacing / depth spacing

// initial collapse: keep the unlabeled spine open, collapse at every
// labelled clade so the first view is the coarsest named groups
function initCollapse(d){
  if(!d.children) return;
  if(d.data.label){
    d._children = d.children;
    d._children.forEach(initCollapse);
    d.children = null;
  } else {
    d.children.forEach(initCollapse);
  }
}

function renderTree(){
  treeSvg = d3.select('#tree-svg');
  treeSvg.selectAll('*').remove();
  treeG = treeSvg.append('g');

  treeZoom = d3.zoom().scaleExtent([0.05, 8])
    .on('zoom', e => treeG.attr('transform', e.transform));
  treeSvg.call(treeZoom);

  treeRoot = d3.hierarchy(S.tree);
  treeRoot.x0 = 0; treeRoot.y0 = 0;
  initCollapse(treeRoot);
  updateTree(treeRoot);

  // initial framing
  const w = $('#stage').clientWidth || 900;
  treeSvg.call(treeZoom.transform,
    d3.zoomIdentity.translate(90, (window.innerHeight||700)/2).scale(0.62));
}

function updateTree(source){
  const layout = d3.tree().nodeSize([DX, DY]);
  layout(treeRoot);

  const nodes = treeRoot.descendants();
  const links = treeRoot.links();

  const t = treeSvg.transition().duration(380);

  /* links */
  const link = treeG.selectAll('path.link')
    .data(links, d => d.target.data.id);
  const elbow = d => `M${d.source.y},${d.source.x}`
    + `C${(d.source.y+d.target.y)/2},${d.source.x} `
    + `${(d.source.y+d.target.y)/2},${d.target.x} `
    + `${d.target.y},${d.target.x}`;
  link.enter().append('path').attr('class','link')
      .attr('d', () => { const o={x:source.x0,y:source.y0};
        return elbow({source:o,target:o}); })
    .merge(link).transition(t).attr('d', elbow);
  link.exit().transition(t).remove()
    .attr('d', () => { const o={x:source.x,y:source.y};
      return elbow({source:o,target:o}); });

  /* nodes */
  const node = treeG.selectAll('g.node')
    .data(nodes, d => d.data.id);

  const enter = node.enter().append('g')
    .attr('class', nodeClass)
    .attr('transform', () => `translate(${source.y0},${source.x0})`)
    .on('click', (e,d) => {
      if(d.data.leaf){ selectDish(d.data.cluster_id); }
      else { toggle(d); updateTree(d); }
    });

  enter.append('circle').attr('r', nodeR);
  enter.append('text')
    .attr('dy','0.32em')
    .attr('x', d => d.data.leaf || (!d.children && !d._children) ? 9 : -9)
    .attr('text-anchor', d => d.data.leaf ? 'start' : 'end')
    .text(nodeLabel);

  const all = enter.merge(node);
  all.attr('class', nodeClass);
  all.transition(t).attr('transform', d => `translate(${d.y},${d.x})`);
  // leaves get an inline overlay colour; internal nodes are filled by CSS
  // (.node.clade circle) so they follow the light/dark theme
  all.select('circle').attr('r', nodeR)
     .attr('fill', d => d.data.leaf ? colorOf(d.data) : null);
  all.select('text').text(nodeLabel)
     .attr('x', d => d.data.leaf ? 9 : -9)
     .attr('text-anchor', d => d.data.leaf ? 'start' : 'end');

  node.exit().transition(t).remove()
    .attr('transform', () => `translate(${source.y},${source.x})`);

  nodes.forEach(d => { d.x0=d.x; d.y0=d.y; });
}

function nodeClass(d){
  let c = 'node';
  if(d.data.leaf) c+=' leaf';
  else { c+=' clade'; if(d._children) c+=' collapsed'; }
  if(d.data.leaf && d.data.cluster_id===S.selected) c+=' selected';
  return c;
}
function nodeR(d){
  if(d.data.leaf) return 3.6;
  const n = d.data.n_leaves||1;
  return Math.min(8, 2.5 + Math.log10(n));
}
function nodeLabel(d){
  if(d.data.leaf) return d.data.name;
  if(d.data.label) return d._children
    ? `${d.data.label}  (${fmtInt(d.data.n_leaves)})` : d.data.label;
  return d._children ? `(${fmtInt(d.data.n_leaves)})` : '';
}
function toggle(d){
  if(d.children){ d._children=d.children; d.children=null; }
  else { d.children=d._children; d._children=null; }
}

/* ============================================================
   MANIFOLD (UMAP canvas scatter)
   ============================================================ */
let mapCanvas, mapCtx, mapTransform = d3.zoomIdentity, mapQuad;
const MAP_PAD = 36;

function renderMap(){
  mapCanvas = $('#map-canvas');
  mapCtx = mapCanvas.getContext('2d');
  resizeMap();

  mapQuad = d3.quadtree()
    .x(d=>d.x).y(d=>d.y)
    .addAll(S.umap.points);

  const zoom = d3.zoom().scaleExtent([0.6, 40])
    .on('zoom', e => { mapTransform = e.transform; drawMap(); });
  d3.select(mapCanvas).call(zoom)
    .on('mousemove', onMapHover)
    .on('click', onMapClick)
    .on('mouseleave', ()=> hideTooltip());

  drawMap();
}

function mapBox(){
  // CSS-pixel space — the 2-D context is pre-scaled by devicePixelRatio,
  // so all drawing/hit-testing happens in CSS px, not device px.
  const w = mapCanvas._cssw, h = mapCanvas._cssh;
  const s = Math.min(w,h) - 2*MAP_PAD;
  return {ox:(w-s)/2, oy:(h-s)/2, s};
}
function dataToPx(d){
  const b = mapBox();
  const p = mapTransform.apply([b.ox + d.x/1000*b.s, b.oy + d.y/1000*b.s]);
  return p;
}
function pxToData(mx,my){
  const b = mapBox();
  const [x,y] = mapTransform.invert([mx,my]);
  return {x:(x-b.ox)/b.s*1000, y:(y-b.oy)/b.s*1000};
}

function resizeMap(){
  const r = $('#stage').getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  mapCanvas.width = r.width*dpr; mapCanvas.height = r.height*dpr;
  mapCtx.setTransform(dpr,0,0,dpr,0,0);
  // store css px size
  mapCanvas._cssw = r.width; mapCanvas._cssh = r.height;
}
function drawMap(){
  if(!mapCtx) return;
  const w = mapCanvas._cssw, h = mapCanvas._cssh;
  mapCtx.clearRect(0,0,w,h);
  const rad = Math.max(1.3, 2.0*Math.sqrt(mapTransform.k));
  for(const p of S.umap.points){
    const [px,py] = dataToPx(p);
    if(px<-5||py<-5||px>w+5||py>h+5) continue;
    mapCtx.beginPath();
    mapCtx.arc(px,py,rad,0,6.283);
    mapCtx.fillStyle = colorOf(p);
    mapCtx.globalAlpha = 0.82;
    mapCtx.fill();
    if(p.cluster_id===S.selected){
      mapCtx.globalAlpha=1; mapCtx.lineWidth=2;
      mapCtx.strokeStyle='#A50026'; mapCtx.stroke();
    }
  }
  mapCtx.globalAlpha = 1;
}
function nearestPoint(mx,my){
  const d = pxToData(mx,my);
  // hit tolerance: ~16 CSS px converted into data units at the current zoom
  const r = 16 * 1000 / (mapBox().s * mapTransform.k);
  return mapQuad.find(d.x, d.y, Math.max(r, 6));
}
function onMapHover(e){
  const [mx,my] = d3.pointer(e, mapCanvas);
  const p = nearestPoint(mx,my);
  if(p){
    showTooltip(e.clientX, e.clientY,
      `<div class="tt-name">${esc(p.name)}</div>`+
      `<div class="tt-meta">${esc(p.cuisine||'')} · ${esc(p.protein_type||'')} · `+
      `${fmtInt(p.total_count)} menus</div>`);
    mapCanvas.style.cursor='pointer';
  } else { hideTooltip(); mapCanvas.style.cursor='default'; }
}
function onMapClick(e){
  const [mx,my] = d3.pointer(e, mapCanvas);
  const p = nearestPoint(mx,my);
  if(p) selectDish(p.cluster_id);
}

/* ---- tooltip ------------------------------------------------- */
function showTooltip(x,y,html){
  const t = $('#tooltip');
  t.innerHTML = html;
  t.style.display='block';
  t.style.left = Math.min(x+13, window.innerWidth-250)+'px';
  t.style.top  = (y+13)+'px';
}
function hideTooltip(){ $('#tooltip').style.display='none'; }

/* ============================================================
   DETAIL PANEL  (lazy-loaded recipe + LCA)
   ============================================================ */
async function selectDish(cid){
  S.selected = cid;
  refreshSelection();
  const panel = $('#detail');
  panel.classList.remove('empty');
  $('#detail-body').innerHTML =
    '<div class="section spinner">loading dish…</div>';
  try {
    const dish = await loadDish(cid);
    renderDetail(dish);
  } catch(e){
    $('#detail-body').innerHTML =
      `<div class="section warn">Could not load dish ${cid}.</div>`;
  }
}

async function loadDish(cid){
  const shard = cid % S.manifest.n_shards;
  if(!S.shardCache.has(shard)){
    S.shardCache.set(shard, await fetchJSON(`data/dishes/shard_${shard}.json`));
  }
  const dish = S.shardCache.get(shard)[String(cid)];
  if(!dish) throw new Error('not in shard');
  return dish;
}

function renderDetail(d){
  const lca = d.lca || {};
  const grade = lca.data_quality_grade;
  let h = '';

  /* head */
  h += `<div class="detail-head">
    <h2>${esc(d.canonical_name||d.top_raw_name)}</h2>
    <div class="raw">menu name: ${esc(d.top_raw_name||'—')}</div>
    <div class="detail-tags">
      <span class="tag">${esc(d.cuisine||'—')}</span>
      <span class="tag">${esc(d.protein_type||'?')} · ${esc(d.carb_type||'?')}</span>
      <span class="tag">${fmtInt(d.total_count)} menus</span>
      ${grade?`<span class="tag grade-${grade}">grade ${grade}`+
        (lca.data_quality_score!=null?` · ${fmt(lca.data_quality_score,1)}`:'')
        +`</span>`:''}
    </div></div>`;

  /* recipe */
  if(d.recipe && d.recipe.length){
    h += `<div class="section"><span class="eyebrow">Recipe ·
      ${d.recipe.length} ingredients</span>`;
    const mx = d3.max(d.recipe, r=>r.proportion_pct)||1;
    for(const r of d.recipe){
      h += `<div class="ing">
        <div class="ing-top"><span class="ing-name">${esc(r.ingredient)}</span>
        <span class="ing-g num">${fmt(r.grams,0)} g · ${fmt(r.proportion_pct,1)}%</span></div>
        <div class="ing-bar"><div style="width:${(r.proportion_pct/mx*100).toFixed(1)}%"></div></div>
      </div>`;
    }
    h += `</div>`;
  }

  /* nutrition (Stage 2b macros) */
  const nu = d.nutrition;
  if(nu){
    const pk = (nu.protein_g_per_serving||0)*4;   // Atwater: 4 kcal/g
    const fk = (nu.fat_g_per_serving||0)*9;        //          9 kcal/g
    const ck = (nu.carb_g_per_serving||0)*4;       //          4 kcal/g
    const tot = pk+fk+ck || 1;
    const pc = v => v/tot*100;
    h += `<div class="section">
      <span class="eyebrow">Nutrition · per serving · ${
        nu.n_servings||'?'} servings</span>
      <div class="stats n2">
        ${statBox('Energy', nu.energy_kcal_per_serving, 'kcal', 0)}
        ${statBox('Protein', nu.protein_g_per_serving, 'g', 1)}
        ${statBox('Fat', nu.fat_g_per_serving, 'g', 1)}
        ${statBox('Carb', nu.carb_g_per_serving, 'g', 1)}
      </div>
      <div class="macrobar">
        <div style="width:${pc(pk).toFixed(1)}%;background:#4575B4"></div>
        <div style="width:${pc(fk).toFixed(1)}%;background:#D73027"></div>
        <div style="width:${pc(ck).toFixed(1)}%;background:#FDAE61"></div>
      </div>
      <div class="macrobar-key">
        <span><i style="background:#4575B4"></i>protein ${pc(pk).toFixed(0)}%</span>
        <span><i style="background:#D73027"></i>fat ${pc(fk).toFixed(0)}%</span>
        <span><i style="background:#FDAE61"></i>carb ${pc(ck).toFixed(0)}%</span>
      </div>
      <div class="note" style="margin-top:6px">whole recipe · ${
        fmt(nu.energy_kcal_per_recipe,0)} kcal${
        (nu.match_rate!=null && nu.match_rate<0.999)
          ? ` · ${(nu.match_rate*100).toFixed(0)}% ingredient match` : ''}</div>
    </div>`;
  }

  /* nutrition quality (NutriScore, Clark et al. 2022) */
  const nq = d.nutriscore;
  if(nq){
    const p = nq.per_100g || {};
    const gc = S.catMap.get('grade:'+nq.grade) || NEUTRAL;
    h += `<div class="section">
      <span class="eyebrow">NutriScore · per 100 g${
        nq.food_type && nq.food_type!=='general'
          ? ` · ${esc(nq.food_type)} variant` : ''}</span>
      <div class="nutriscore-head">
        <span class="ns-grade" style="background:${gc}">${esc(nq.grade)}</span>
        <div class="ns-nums">
          <div><b>${fmt(nq.score_0to100,0)}</b><span class="u"> / 100 · 0 best</span></div>
          <div class="note">raw ${nq.points>0?'+':''}${fmtInt(nq.points)} ·
            penalties ${fmtInt(nq.negative_points)} − benefits ${
            fmtInt(nq.positive_points)}</div>
        </div>
      </div>
      <div class="stats n2" style="margin-top:8px">
        ${statBox('Sat fat', p.sat_fat_g, 'g', 1)}
        ${statBox('Sugars', p.sugars_g, 'g', 1)}
        ${statBox('Fibre', p.fiber_g, 'g', 1)}
        ${statBox('Salt', p.salt_g, 'g', 1)}
      </div>
      <div class="note" style="margin-top:6px">fruit/veg/nut/legume/oil: ${
        fmt(nq.fvn_pct,0)}% of mass</div>
    </div>`;
  }

  /* health impact (mealhealth — GBD ΔYLL, Koen van Greevenbroek) */
  const mq = d.mealhealth;
  if(mq && mq.delta_yll_lifetime!=null){
    const dy = mq.delta_yll_lifetime;          // >0 yrs gained, <0 yrs lost
    const lost = dy < 0;
    const col = rampInterp(lost ? 0.96 : 0.04);   // red lost / blue gained
    const gg = mq.group_grams || {};
    const groups = Object.entries(gg).sort((a,b)=>b[1]-a[1])
      .map(([k,v])=>`${esc(k.replace(/_/g,' '))} ${fmt(v,0)} g`).join(' · ');
    const paf = mq.paf || {};
    h += `<div class="section">
      <span class="eyebrow">Health impact · this dish daily for life vs US diet</span>
      <div class="nutriscore-head">
        <span class="ns-grade" style="background:${col}">${lost?'▼':'▲'}</span>
        <div class="ns-nums">
          <div><b>${dy>0?'+':''}${fmt(dy,3)}</b><span class="u"> yr ${
            lost?'lost':'gained'} · median adult, lifetime</span></div>
          <div class="note">GBD ΔYLL (mealhealth)${
            mq.meal_kcal!=null?` · ${fmt(mq.meal_kcal,0)} kcal/serving`:''}</div>
        </div>
      </div>
      <div class="note" style="margin-top:8px">GBD risk groups: ${
        groups || 'none — impact via calories only'}</div>
      <div class="stats n2" style="margin-top:8px">
        ${statBox('CHD', paf.CHD!=null?paf.CHD*100:null,'%',1)}
        ${statBox('Stroke', paf.Stroke!=null?paf.Stroke*100:null,'%',1)}
        ${statBox('T2 diabetes', paf.T2DM!=null?paf.T2DM*100:null,'%',1)}
        ${statBox('Colorectal', paf.CRC!=null?paf.CRC*100:null,'%',1)}
      </div>
      <div class="note" style="margin-top:4px">diet-attributable risk change by cause (PAF)</div>
    </div>`;
  }

  /* impact */
  h += `<div class="section"><span class="eyebrow">Life-cycle impact · per kg</span>
    <div class="stats">
      ${statBox('GHG', lca.ghg_kgco2e_per_kg, 'kg CO₂e')}
      ${statBox('Water', lca.water_m3_per_kg, 'm³')}
      ${statBox('Land', lca.land_pt_per_kg, 'pt')}
    </div>`;

  /* monte-carlo uncertainty */
  const mc = lca.ghg_mc;
  if(mc && mc.p5!=null && mc.p95!=null){
    const lo=mc.p5, hi=mc.p95, med=mc.median!=null?mc.median:mc.mean;
    const span = hi-lo || 1;
    const pos = v => Math.max(0,Math.min(100,(v-lo)/span*100));
    h += `<div class="mc"><span class="eyebrow">GHG Monte-Carlo · per recipe</span>
      <div class="mc-track">
        <div class="mc-range" style="left:0%;right:0%"></div>
        <div class="mc-tick" style="left:${pos(med)}%"></div>
      </div>
      <div class="mc-scale"><span>p5 ${fmt(lo)}</span>
        <span>median ${fmt(med)}</span><span>p95 ${fmt(hi)}</span></div>`;
    if(mc.top_variance_drivers && mc.top_variance_drivers.length){
      h += `<div style="margin-top:8px">`;
      for(const dr of mc.top_variance_drivers.slice(0,4)){
        if(!dr.variance_pct) continue;
        h += `<div class="driver"><span class="dn">${esc(dr.ingredient)}</span>
          <span class="dp num">${fmt(dr.variance_pct,1)}% of variance</span></div>`;
      }
      h += `</div>`;
    }
    h += `</div>`;
  }
  h += `</div>`;

  /* per-ingredient impact contribution — toggles GHG / Water / Land */
  if(lca.ingredients && lca.ingredients.length){
    h += `<div class="section"><div class="section-head">
      <span class="eyebrow">Ingredient contribution</span>
      <div class="segmented mini" id="ing-toggle">${
        Object.entries(ING_METRICS).map(([k,m])=>
          `<button data-m="${k}"${k===S.ingMetric?' class="active"':''}>`+
          `${m.label}</button>`).join('')}
      </div></div>
      <div id="ing-contrib-list"></div></div>`;
  }

  /* data gaps */
  const gaps = lca.data_gaps||[], unm = lca.unmatched||[];
  if(gaps.length || unm.length){
    h += `<div class="section"><span class="eyebrow">Data notes</span>`;
    if(unm.length) h += `<div class="note warn">Unmatched: ${
      unm.map(esc).join(', ')}</div>`;
    if(gaps.length) h += `<div class="note">${gaps.map(esc).join('; ')}</div>`;
    h += `</div>`;
  }

  $('#detail-body').innerHTML = h;

  /* fill + wire the ingredient-contribution breakdown */
  S.currentLca = lca;
  if(lca.ingredients && lca.ingredients.length){
    renderIngContrib();
    $('#ing-toggle').addEventListener('click', e=>{
      const b = e.target.closest('button'); if(!b) return;
      S.ingMetric = b.dataset.m;
      $('#ing-toggle').querySelectorAll('button')
        .forEach(x=>x.classList.toggle('active', x===b));
      renderIngContrib();
    });
  }
}

function renderIngContrib(){
  const lca = S.currentLca;
  if(!lca || !lca.ingredients) return;
  const m = ING_METRICS[S.ingMetric];
  const ing = lca.ingredients.slice()
    .sort((a,b)=>(b[m.field]||0)-(a[m.field]||0));
  const mx = d3.max(ing, r=>r[m.field]) || 1;
  let h = '';
  for(const r of ing){
    const v = r[m.field];
    h += `<div class="ing">
      <div class="ing-top">
        <span class="ing-name">${esc(r.ingredient)}${
          r.unmatched?' <span class="warn">(unmatched)</span>':''}</span>
        <span class="ing-g num">${fmt(v,m.dec)} ${m.unit}</span></div>
      <div class="ing-bar"><div style="width:${
        ((v||0)/mx*100).toFixed(1)}%;background:${
        r.unmatched?'#c4c6cf':rampInterp(m.ramp)}"></div></div>
      <div class="note" style="margin-top:1px">${esc(r.matched_lci||'—')}</div>
    </div>`;
  }
  $('#ing-contrib-list').innerHTML = h;
}

function statBox(name, val, unit, dec=2){
  return `<div class="stat"><span class="eyebrow">${name}</span>
    <div class="v num">${fmt(val,dec)}</div><div class="u">${unit}</div></div>`;
}

/* ============================================================
   LEGEND / CONTROLS
   ============================================================ */
function buildLegend(){
  const o = OVERLAYS[S.overlay];
  let h = `<span class="eyebrow">${o.label}</span>`;
  if(o.kind==='cat'){
    // every category, commonest first, with its dish count
    const freq = d3.rollup(S.leaves, v=>v.length, d=>d[o.field]);
    const entries = Array.from(freq.entries())
      .filter(([v])=>v!=null && v!=='')
      // grade is ordered A→E; every other categorical sorts by frequency
      .sort(o.field==='grade'
        ? (a,b)=> d3.ascending(a[0], b[0])
        : (a,b)=> b[1]-a[1]);
    for(const [v,n] of entries)
      h += `<div class="legend-row"><span class="legend-sw" style="background:${
        S.catMap.get(o.field+':'+v)||NEUTRAL}"></span>${esc(v)}`+
        `<span class="ct num">${fmtInt(n)}</span></div>`;
  } else {
    const a = S.ranks[o.field];
    const dec = ['ghg','water','land','mealhealth'].includes(o.field) ? 2 : 0;
    h += `<div class="legend-cont"></div>
      <div class="legend-ends"><span>low · ${fmt(a[0],dec)}</span>
      <span>high · ${fmt(a[a.length-1],dec)}</span></div>
      <div class="legend-row note">colour = rank (median ≈ yellow)</div>`;
  }
  $('#legend').innerHTML = h;
}

function recolor(){
  if(treeG) treeG.selectAll('g.node.leaf circle')
    .attr('fill', d => colorOf(d.data));
  if(S.umap && mapCtx) drawMap();
  buildLegend();
}

function refreshSelection(){
  if(treeG) treeG.selectAll('g.node').attr('class', nodeClass);
  if(S.umap && mapCtx) drawMap();
}

function initTheme(){
  const btn = $('#theme-btn');
  const apply = t => {
    document.documentElement.dataset.theme = t;
    btn.textContent = t==='dark' ? '☀ Light' : '☾ Dark';
  };
  apply(document.documentElement.dataset.theme || 'light');
  btn.addEventListener('click', ()=>{
    const next = document.documentElement.dataset.theme==='dark'
      ? 'light' : 'dark';
    try { localStorage.setItem('phylo-theme', next); } catch(e){}
    apply(next);   // CSS variables cascade — no re-render needed
  });
}

function wireControls(){
  initTheme();
  // view toggle
  $('#view-toggle').addEventListener('click', e=>{
    const b = e.target.closest('button'); if(!b) return;
    S.view = b.dataset.view;
    document.querySelectorAll('#view-toggle button')
      .forEach(x=>x.classList.toggle('active', x===b));
    $('#stage').classList.toggle('map', S.view==='map');
    if(S.view==='map' && S.umap){ resizeMap(); drawMap(); }
  });

  // overlay
  $('#overlay').addEventListener('change', e=>{
    S.overlay = e.target.value; recolor();
  });

  // search
  let searchTimer;
  $('#search').addEventListener('input', e=>{
    clearTimeout(searchTimer);
    searchTimer = setTimeout(()=>doSearch(e.target.value.trim()), 200);
  });

  window.addEventListener('resize', ()=>{
    if(S.view==='map' && S.umap){ resizeMap(); drawMap(); }
  });
}

/* ---- search: jump to the best-matching dish ------------------ */
function doSearch(q){
  if(!q || q.length<2){ setStatus(`${fmtInt(S.leaves.length)} dishes`); return; }
  const ql = q.toLowerCase();
  const hits = S.leaves.filter(d=>(d.name||'').toLowerCase().includes(ql));
  setStatus(`${hits.length} match${hits.length===1?'':'es'}`);
  if(!hits.length) return;
  hits.sort((a,b)=>(b.total_count||0)-(a.total_count||0));
  const best = hits[0];
  selectDish(best.cluster_id);
  if(S.view==='tree') revealLeaf(best.cluster_id);
}

// expand the dendrogram down to a given dish and centre it
function revealLeaf(cid){
  const path = [];
  (function find(d){
    if(d.data.leaf) return d.data.cluster_id===cid;
    const kids = d.children || d._children || [];
    for(const k of kids){ if(find(k)){ path.push(d); return true; } }
    return false;
  })(treeRoot);
  path.reverse().forEach(d=>{ if(d._children){ d.children=d._children;
    d._children=null; } });
  updateTree(treeRoot);
  // centre after the layout transition
  setTimeout(()=>{
    const leaf = treeRoot.descendants()
      .find(d=>d.data.leaf && d.data.cluster_id===cid);
    if(!leaf) return;
    const w=$('#stage').clientWidth, h=$('#stage').clientHeight;
    treeSvg.transition().duration(500).call(treeZoom.transform,
      d3.zoomIdentity.translate(w/2,h/2).scale(1).translate(-leaf.y,-leaf.x));
  }, 420);
}

/* ---- misc --------------------------------------------------- */
function esc(s){ return String(s==null?'':s)
  .replace(/[&<>"]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }

boot();
