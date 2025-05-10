import {
    dimensions,
    createScales,
    setupZoom,
    drawToBitmap,
    renderView,
    getFitScale,
    resetZoom,
    MAX_BITMAP_SIZE,
  } from "./d3.js";
  
  import { hitTest, showArtistInfo } from "./ui.js";
  import { thumbnails, resized, artists } from "./load.js";
  
  let canvas, ctx;
document.addEventListener("DOMContentLoaded", async () => {
  // UI elements for method/config selection
  const methodSelect = document.getElementById("method");
  const configSelect = document.getElementById("config");
  const loadBtn = document.getElementById("load");

  // Hide canvas until data is loaded
  canvas = document.getElementById("canvas");
  ctx = canvas.getContext("2d");
  canvas.style.display = "none";

  // 1. List of methods (hardcoded or fetch from backend if available)
  const methods = ["umap", "tsne", "pca", "isomap", "lle", "mds", "phate", "trimap"];
  methods.forEach(m => {
    const opt = document.createElement("option");
    opt.value = m;
    opt.textContent = m;
    methodSelect.appendChild(opt);
  });

  // 2. When method changes, fetch configs
  async function updateConfigs() {
    const method = methodSelect.value;
    configSelect.innerHTML = "<option>Loading...</option>";
    const res = await fetch(`/api/configs?method=${method}`);
    const configs = await res.json();
    configSelect.innerHTML = "";
    if (!configs.length) {
      const opt = document.createElement("option");
      opt.value = "";
      opt.textContent = "No configs";
      configSelect.appendChild(opt);
      loadBtn.disabled = true;
      return;
    }
    configs.forEach(cfg => {
      const opt = document.createElement("option");
      opt.value = cfg.config_id;
      opt.textContent = `ID ${cfg.config_id} (${cfg.subset_strategy}, size ${cfg.subset_size})`;
      configSelect.appendChild(opt);
    });
    loadBtn.disabled = false;
  }
  methodSelect.addEventListener("change", updateConfigs);
  await updateConfigs();

  // 3. On Load button, initialize app with selection
  loadBtn.addEventListener("click", async () => {
    const method = methodSelect.value;
    const config_id = configSelect.value;
    if (!method || !config_id) return;
    // Show canvas
    canvas.style.display = "block";
    // Start app
    await initializeApp(method, config_id);
    // Optionally hide controls after load
    // document.getElementById("controls").style.display = "none";
  });
});

    const html = document.documentElement;
    const resizedPane = document.getElementById("resized");
  // All logic is now inside the DOMContentLoaded event or functions.

    // Define application states
    const AppState = {
      LOADING_DATA: "loading_data",
      LOADING_IMAGES: "loading_images",
      CREATING_BITMAPS: "creating_bitmaps",
      VIEWING: "viewing",
      DETAIL: "detail",
    };
  
    // Application state
    const state = {
      current: AppState.LOADING_DATA,
      points: [],
      bitmaps: {
        full: null,
        half: null,
      },
      transform: d3.zoomIdentity,
      selectedPoint: null,
  
      transition(to, data = {}) {
        console.log(`State transition: ${this.current} → ${to}`);
        this.current = to;
  
        // Handle state-specific logic
        if (to === AppState.DETAIL) {
          this.selectedPoint = data.point;
          html.classList.add("show-resized");
        } else if (
          to === AppState.VIEWING &&
          html.classList.contains("show-resized")
        ) {
          html.classList.remove("show-resized");
        }
  
        // Re-render if appropriate
        if (to === AppState.VIEWING || to === AppState.DETAIL) {
          updateView();
        }
      },
    };
  
    // Initialize the application
    try {
      await initializeApp();
    } catch (error) {
      console.error("Failed to initialize app:", error);
    }
  
    // Function to update view based on current state
    function updateView() {
      const currentBitmap =
        state.current === AppState.DETAIL
          ? state.bitmaps.half
          : state.bitmaps.full;
  
      const dims = dimensions(canvas);
      renderView(ctx, dims, state.transform, currentBitmap);
    }
  
    // App initialization pipeline
    async function initializeApp(method, config_id) {
  // 1. Load data
  state.transition(AppState.LOADING_DATA);
  const response = await fetch(`/api/points?method=${method}&config_id=${config_id}`);
  if (!response.ok) throw new Error(response.statusText);
  const points = (await response.json()).map((p) => ({
    ...p,
    x: p.x,
    y: p.y,
  }));
  state.points = points;
  console.log(`Loaded ${state.points.length} data points`);

  // 2. Load images
  state.transition(AppState.LOADING_IMAGES);
  await thumbnails(state.points);
  console.log("Loaded all thumbnails");

  // 3. Create bitmaps
  state.transition(AppState.CREATING_BITMAPS);
  await createBitmaps();
  console.log("Created bitmaps");

  // 4. Setup interactions
  setupInteractions();

  // 5. Transition to viewing state
  state.transition(AppState.VIEWING);
  console.log("App initialization complete");
}

  
    // Bitmap factory
    async function createBitmaps() {
      const dims = dimensions(canvas);
  
      // Create full-width bitmap
      console.log("Creating full-width bitmap");
      canvas.width = MAX_BITMAP_SIZE;
      canvas.height = MAX_BITMAP_SIZE;
      const fullScales = createScales(state.points, 40, {
        width: MAX_BITMAP_SIZE,
        height: MAX_BITMAP_SIZE,
      });
      drawToBitmap(
        ctx,
        state.points,
        fullScales,
        { width: MAX_BITMAP_SIZE, height: MAX_BITMAP_SIZE },
        "fullBounds"
      );
      state.bitmaps.full = await createImageBitmap(canvas);
  
      // Create half-width bitmap
      console.log("Creating half-width bitmap");
      canvas.width = MAX_BITMAP_SIZE / 2;
      canvas.height = MAX_BITMAP_SIZE;
      const halfScales = createScales(state.points, 40, {
        width: MAX_BITMAP_SIZE / 2,
        height: MAX_BITMAP_SIZE,
      });
      drawToBitmap(
        ctx,
        state.points,
        halfScales,
        { width: MAX_BITMAP_SIZE / 2, height: MAX_BITMAP_SIZE },
        "halfBounds"
      );
      state.bitmaps.half = await createImageBitmap(canvas);
  
      // Reset canvas to viewport size
      canvas.width = dims.width;
      canvas.height = dims.height;
    }
  
    // Setup interaction handlers
    function setupInteractions() {
      // Command functions
      function resetViewZoom() {
        const dims = dimensions(canvas);
        const scale = getFitScale(dims, MAX_BITMAP_SIZE, MAX_BITMAP_SIZE);
        state.transform = resetZoom(canvas, scale);
        updateView();
      }
  
      // Set up zoom behavior
      const onZoom = (transform) => {
        state.transform = transform;
        updateView();
      };
  
      const zoomBehavior = setupZoom(canvas, onZoom);
  
      // Set initial transform
      const dims = dimensions(canvas);
      const initialScale = getFitScale(dims, MAX_BITMAP_SIZE, MAX_BITMAP_SIZE);
      state.transform = d3.zoomIdentity.scale(initialScale);
      d3.select(canvas).call(zoomBehavior.transform, state.transform);
  
      // Canvas click - hit detection and detail view
      canvas.addEventListener("click", (e) => {
        const rect = canvas.getBoundingClientRect();
        const boundsKey =
          state.current === AppState.DETAIL ? "halfBounds" : "fullBounds";
        const point = hitTest(
          state.points,
          e.clientX,
          e.clientY,
          rect,
          state.transform,
          boundsKey
        );
  
        if (point) {
          // Show detail view
          state.transition(AppState.DETAIL, { point });
          showArtistInfo(point, resized, artists);
        }
      });
  
      // Close detail view on click outside
      resizedPane.addEventListener("click", (e) => {
        if (e.target === resizedPane) {
          state.transition(AppState.VIEWING);
        }
      });
  
      // Escape key to reset zoom and close detail
      document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
          // Close detail view if open
          if (state.current === AppState.DETAIL) {
            state.transition(AppState.VIEWING);
          }
  
          // Reset zoom
          resetViewZoom();
        }
      });
    }
      