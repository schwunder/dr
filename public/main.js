/* ------------------------------------------------------------------
   Imports
   ------------------------------------------------------------------ */
   import {
    dimensions, createScales, setupZoom, drawToBitmap,
    renderView, getFitScale, resetZoom, MAX_BITMAP_SIZE
  } from "./d3.js";
  
  import {
    hitTest, showArtistInfo, populateConfigDropdown,
    setControlState, showStatus, showPythonEnv
  } from "./ui.js";
  
  import { thumbnails, resized, artists } from "./load.js";
  
  /* ------------------------------------------------------------------
     DOM ready
     ------------------------------------------------------------------ */
  document.addEventListener("DOMContentLoaded", async () => {
  
    /* ---------- top‑bar controls ---------- */
    const methodSel   = document.getElementById("method");
    const configSel   = document.getElementById("config");
    const loadBtn     = document.getElementById("load");
    const runPyBtn    = document.getElementById("run-python");
    const canvas      = document.getElementById("canvas");
    const ctx         = canvas.getContext("2d");
    const html        = document.documentElement;
    const resizedPane = document.getElementById("resized");
    const svgOverlay  = d3.select('#viz-svg');
  
    /* ---------- python env ---------- */
    try {
      const res = await fetch("/api/python-env");
      if (res.ok) showPythonEnv((await res.json()).python);
    } catch {/* ignore */}
  
    /* ========== Application‑state ========== */
    const AppState = {
      LOADING_DATA   : "loading_data",
      LOADING_IMAGES : "loading_images",
      CREATING_BITMAPS:"creating_bitmaps",
      VIEWING        : "viewing",
      DETAIL         : "detail"
    };
  
    const state = {
      current : AppState.LOADING_DATA,
      points  : [],
      bitmaps : { full:null, half:null },
      transform : d3.zoomIdentity,
      selectedPoint : null,
  
      transition(to, data={}) {
        console.log(`State: ${this.current} → ${to}`);
        this.current = to;
        if (to === AppState.DETAIL) {
          this.selectedPoint = data.point;
          html.classList.add("show-resized");
        } else if (to === AppState.VIEWING) {
          html.classList.remove("show-resized");
        }
        if (to === AppState.VIEWING || to === AppState.DETAIL) {
          updateView();
          renderVizPoints();
        }
      }
    };
  
    /* ---------- helper : view painters ---------- */
    function updateView() {
      const bmp = state.current===AppState.DETAIL ? state.bitmaps.half
                                                  : state.bitmaps.full;
      renderView(ctx, dimensions(canvas), state.transform, bmp);
    }
  
    function renderVizPoints() {
      svgOverlay.selectAll('*').remove();
      if (!state.points.length) return;
  
      svgOverlay.attr('width', canvas.width).attr('height', canvas.height);
  
      const {k,x,y} = state.transform;
      svgOverlay.selectAll('circle')
        .data(state.points)
        .enter().append('circle')
        .attr('cx', d => d.x*k + x)
        .attr('cy', d => d.y*k + y)
        .attr('r', 3)
        .attr('fill', 'red')
        .attr('opacity', 0.7);
    }
  
    /* ------------------------------------------------------------------
       1.  Populate Method dropdown (static list or fetched)
       ------------------------------------------------------------------ */
    const methods = ["umap","tsne","pca","isomap","lle","mds","phate","trimap"];
    methods.forEach(m=>{
      const o=document.createElement("option");o.value=o.textContent=m;methodSel.appendChild(o);
    });
    methodSel.disabled = true;               // fixed to 1 backend family
  
    /* ------------------------------------------------------------------
       2.  Load configs for (single) method
       ------------------------------------------------------------------ */
    async function updateConfigs() {
      setControlState("config","disabled"); setControlState("load","disabled");
      showStatus("Loading configs…","info");
      const res   = await fetch(`/api/configs?method=${methodSel.value}`);
      const cfgs  = await res.json();
      populateConfigDropdown(cfgs);
      if (cfgs.length){
        setControlState("config","enabled"); setControlState("load","enabled");
        showStatus("Configs loaded","info");
      } else {
        showStatus("No configs","error");
      }
    }
    await updateConfigs();   // initial
    methodSel.addEventListener("change",updateConfigs);
  
    /* ------------------------------------------------------------------
       3.  LOAD button – kick‑off full visualisation pipeline
       ------------------------------------------------------------------ */
    loadBtn.addEventListener("click", async () => {
      const viz_id = configSel.value;
      if (!viz_id){ alert("Select a config first"); return; }
      try {
        await initializeApp(viz_id);
      } catch(e) {
        console.error(e);
        alert("Failed to load visualisation: "+e.message);
      }
    });
  
    /* ------------------------------------------------------------------
       4.  RUN‑PYTHON button
       ------------------------------------------------------------------ */
    runPyBtn.addEventListener("click", async () => {
      const payload = { method:"umap", config:"detail" };
      try{
        runPyBtn.disabled=true;
        const res = await fetch("/api/run",{
          method:"POST",headers:{"Content-Type":"application/json"},
          body:JSON.stringify(payload)
        });
        const txt = await res.text();
        res.ok ? alert("Python output:\n"+txt)
               : alert(`Python error (${res.status}):\n${txt}`);
      }catch(err){ alert("Request failed: "+err); }
      finally { runPyBtn.disabled=false; }
    });
  
    /* ==================================================================
       5.  Full pipeline for a chosen config_id
       ================================================================== */
       async function initializeApp(config_id){
        /* -- load projection & config -- */
        state.transition(AppState.LOADING_DATA);
      
        const ptRes = await fetch(`/api/projection-points?config_id=${config_id}`);
        if (!ptRes.ok) throw new Error("projection-points fetch failed");
        const pointsData = await ptRes.json();
        state.points = pointsData.map(p => ({...p, x: p.x, y: p.y}));
        state.names  = pointsData.map(p => p.filename);
      
        /* -- thumbnails -- */
        state.transition(AppState.LOADING_IMAGES);
        await thumbnails(state.points, state.names);
      
        /* -- bitmaps -- */
        state.transition(AppState.CREATING_BITMAPS);
        await createBitmaps();
      
        /* -- interactivity -- */
        setupInteractions();
        state.transition(AppState.VIEWING);
        canvas.style.display = "block";
      }
  
    /* ------------------------------------------------------------------
       Bitmap builder
       ------------------------------------------------------------------ */
    async function createBitmaps(){
      const dims=dimensions(canvas);
  
      // full
      canvas.width=canvas.height=MAX_BITMAP_SIZE;
      const scalesFull=createScales(state.points,40,{width:MAX_BITMAP_SIZE,height:MAX_BITMAP_SIZE});
      drawToBitmap(ctx,state.points,scalesFull,{width:MAX_BITMAP_SIZE,height:MAX_BITMAP_SIZE},"fullBounds");
      state.bitmaps.full=await createImageBitmap(canvas);
  
      // half
      canvas.width=MAX_BITMAP_SIZE/2; canvas.height=MAX_BITMAP_SIZE;
      const scalesHalf=createScales(state.points,40,{width:MAX_BITMAP_SIZE/2,height:MAX_BITMAP_SIZE});
      drawToBitmap(ctx,state.points,scalesHalf,{width:MAX_BITMAP_SIZE/2,height:MAX_BITMAP_SIZE},"halfBounds");
      state.bitmaps.half=await createImageBitmap(canvas);
  
      // reset canvas to viewport dims
      canvas.width=dims.width; canvas.height=dims.height;
    }
  
    /* ------------------------------------------------------------------
       Zoom / click interactions
       ------------------------------------------------------------------ */
    function setupInteractions(){
      const onZoom=t=>{ state.transform=t; updateView(); renderVizPoints(); };
      const zoomBehaviour=setupZoom(canvas,onZoom);
  
      const fit=getFitScale(dimensions(canvas),MAX_BITMAP_SIZE,MAX_BITMAP_SIZE);
      state.transform=d3.zoomIdentity.scale(fit);
      d3.select(canvas).call(zoomBehaviour.transform,state.transform);
  
      canvas.addEventListener("click",e=>{
        const rect=canvas.getBoundingClientRect();
        const key=state.current===AppState.DETAIL?"halfBounds":"fullBounds";
        const p=hitTest(state.points,e.clientX,e.clientY,rect,state.transform,key);
        if(p){ state.transition(AppState.DETAIL,{point:p}); showArtistInfo(p,resized,artists); }
      });
  
      resizedPane.addEventListener("click",e=>{
        if(e.target===resizedPane) state.transition(AppState.VIEWING);
      });
  
      document.addEventListener("keydown",e=>{
        if(e.key==="Escape"){
          if(state.current===AppState.DETAIL) state.transition(AppState.VIEWING);
          const scale=fit; state.transform=resetZoom(canvas,scale); updateView(); renderVizPoints();
        }
      });
    }
  });
  