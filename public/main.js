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

import {
  hitTest,
  showArtistInfo,
  populateConfigDropdown,
  setControlState,
  showStatus,
  showPythonEnv,
  updateArtistPanel,
  updateImagePanel,
  showDetailsPanel
} from "./ui.js";
import { thumbnails, resized, artists } from "./load.js";

  let canvas, ctx;
document.addEventListener("DOMContentLoaded", async () => {
  // Show Python executable path
  try {
    const res = await fetch("/api/python-env");
    if (res.ok) {
      const data = await res.json();
      showPythonEnv(data.python);
    }
  } catch {}

  // UI elements for method/config selection
  const methodSelect = document.getElementById("method");
  const configSelect = document.getElementById("config");
  const loadBtn = document.getElementById("load");
  const runPythonBtn = document.getElementById("run-python");

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
  // Disable method selection
  methodSelect.disabled = true;

  // 2. When method changes, fetch configs
  async function updateConfigs() {
    const method = methodSelect.value;
    setControlState("config", "disabled");
    setControlState("load", "disabled");
    showStatus("Loading configs...", "info");
    const res = await fetch(`/api/configs?method=${method}`);
    const configs = await res.json();
    populateConfigDropdown(configs);
    if (!configs.length) {
      setControlState("load", "disabled");
      showStatus("No configs available", "error");
      return;
    }
    setControlState("config", "enabled");
    setControlState("load", "enabled");
    showStatus("Configs loaded", "info");
  }
  methodSelect.addEventListener("change", updateConfigs);
  await updateConfigs();

  // 3. On Load button, initialize app with selection
  loadBtn.addEventListener("click", async () => {
    const viz_id = configSelect.value;
    if (!viz_id) {
      alert("Select a visualization before loading.");
      return;
    }
    // Fetch the selected config's info from /api/viz-config
    const res = await fetch(`/api/viz-config?viz_id=${viz_id}`);
    if (!res.ok) {
      alert("Failed to fetch visualization config");
      return;
    }
    const vizConfig = await res.json();
    if (!vizConfig.low_res) {
      alert("Selected visualization does not have an image file.");
      return;
    }
    // Load the visualization image using its filename
    import('./load.js').then(({ visualizations }) => {
      visualizations(vizConfig.low_res).then(img => {
        // Optionally, show the image somewhere in the UI or log it
        console.log('Visualization image loaded', img);
        // Example: append to a container
        const vizImgContainer = document.getElementById('viz-image-preview');
        if (vizImgContainer) {
          vizImgContainer.innerHTML = '';
          vizImgContainer.appendChild(img);
        }
        // Draw the visualization image to the canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        canvas.style.display = "block";
      }).catch(err => {
        alert('Failed to load visualization image: ' + err);
      });
    });
    // Show canvas
    setControlState("canvas", "visible");
    // Do not initialize app or draw D3 content
    // Only the loaded image will be drawn to the canvas
    // Optionally hide controls after load
    // setControlState("controls", "hidden");
  });

  // 4. On Run Python button, trigger backend Python script
  runPythonBtn.addEventListener("click", async () => {
    // Decoupled: Always run with hardcoded method/config
    const method = "umap";
    const configName = "detail";
    console.log("[RunPython] Button clicked");
    runPythonBtn.disabled = true;
    try {
      console.log("[RunPython] Sending request to /api/run", { method, config: configName });
      const res = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ method, config: configName })
      });
      console.log("[RunPython] Response received from /api/run");
      const text = await res.text();
      if (!res.ok) {
        let errMsg = `Python error (${res.status}): ${text}`;
        alert(errMsg);
        console.error("/api/run error", errMsg);
      } else {
        alert("Python script output:\n" + text);
        console.log("/api/run output:", text);
      }
      console.log("[RunPython] Python script completed");
    } catch (err) {
      alert("Request failed: " + err);
      console.error("[RunPython] Fetch or script error:", err);
    } finally {
      runPythonBtn.disabled = false;
      console.log("[RunPython] Button re-enabled");
    }
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
  
    // Do not auto-initialize app on page load. Only load when user clicks the Load button with valid selections.
  
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
async function initializeApp(viz_id) {
  // 1. Load viz config and points for selected viz_id
  state.transition(AppState.LOADING_DATA);
  let vizConfig, vizPoints;
  try {
    // Fetch viz config for this viz_id
    const configRes = await fetch(`/api/viz-config?viz_id=${viz_id}`);
    if (!configRes.ok) {
      let message = `Failed to load viz config (status ${configRes.status}): ${configRes.statusText}`;
      try {
        const errJson = await configRes.json();
        if (errJson && errJson.error) message += `\n${errJson.error}`;
      } catch {}
      alert(message);
      throw new Error(message);
    }
    vizConfig = await configRes.json();
    console.log("Loaded viz config", vizConfig);
    if (!vizConfig || !vizConfig.viz_id) throw new Error("No viz config found for this viz_id");

    // Fetch viz points for this viz_id
    const pointsRes = await fetch(`/api/viz-points?viz_id=${viz_id}`);
    if (!pointsRes.ok) {
      let message = `Failed to load viz points (status ${pointsRes.status}): ${pointsRes.statusText}`;
      try {
        const errJson = await pointsRes.json();
        if (errJson && errJson.error) message += `\n${errJson.error}`;
      } catch {}
      alert(message);
      throw new Error(message);
    }
    vizPoints = await pointsRes.json();
    state.points = vizPoints;
    console.log(`Loaded ${state.points.length} viz points`);
  } catch (err) {
    alert(`Could not load visualization data.\n${err.message || err}`);
    throw err;
  }

  // 2. Load images for visualization (using viz name)
  state.transition(AppState.LOADING_IMAGES);
  // If vizConfig.name exists, use it for image loading
  const vizName = vizConfig && vizConfig.name ? vizConfig.name : undefined;
  await thumbnails(state.points, vizName);
  console.log("Loaded all thumbnails for visualization", vizName);

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
      