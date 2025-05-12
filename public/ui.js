// Find point under cursor with tolerance
function hitTest(
    points,
    clientX,
    clientY,
    rect,
    transform,
    boundsKey = "bounds"
  ) {
    // Transform from screen coordinates to bitmap coordinates
    const x = (clientX - rect.left - transform.x) / transform.k;
    const y = (clientY - rect.top - transform.y) / transform.k;
  
    // Use a tolerance for hit detection
    const tolerance = 20;
  
    // Find a point whose bounds contain these coordinates
    return points.find((p) => {
      if (!p[boundsKey]) return false;
  
      const bounds = p[boundsKey];
      return (
        x >= bounds.x - tolerance &&
        x <= bounds.x + bounds.width + tolerance &&
        y >= bounds.y - tolerance &&
        y <= bounds.y + bounds.height + tolerance
      );
    });
  }
  
  // Display artist information
  function showArtistInfo(point, loadResized, loadArtist) {
    // Get the container element
    const imageEl = document.getElementById("image");
    imageEl.innerHTML = "<p>Loading...</p>";
  
    // Load image and artist info in parallel
    return Promise.all([
      loadResized(point.filename),
      loadArtist(point.artist),
    ]).then(([img, artist]) => {
      // Display image
      imageEl.innerHTML = "";
      imageEl.appendChild(img);
  
      // Display artist info
      if (artist) {
        [
          "bio",
          "genre",
          "name",
          "nationality",
          "paintings",
          "wikipedia",
          "years",
        ].forEach((key) => {
          const el = document.getElementById(key);
          if (el) el.textContent = artist[key] || "";
        });
      }
    });
  }
  
  // Populate the config dropdown
async function populateConfigDropdown() {
  const configSelect = document.getElementById("config");
  configSelect.innerHTML = '';
  // Fetch all available visualizations
  const res = await fetch('/api/viz-list');
  if (!res.ok) {
    alert('Failed to fetch visualization list');
    return;
  }
  const vizList = await res.json();
  vizList.forEach(viz => {
    const opt = document.createElement('option');
    opt.value = viz.viz_id;
    opt.textContent = viz.name ? viz.name : `viz ${viz.viz_id} (${viz.method}, config ${viz.config_id})`;
    configSelect.appendChild(opt);
  });
}

  // Enable, disable, or hide a control by id
function setControlState(id, state) {
  const el = document.getElementById(id);
  if (!el) return;
  if (state === "enabled") el.disabled = false;
  else if (state === "disabled") el.disabled = true;
  else if (state === "hidden") el.style.display = "none";
  else if (state === "visible") el.style.display = "";
}

// Show a status message in a dedicated div
function showStatus(msg, type = "info") {
  let statusDiv = document.getElementById("status-message");
  if (!statusDiv) {
    statusDiv = document.createElement("div");
    statusDiv.id = "status-message";
    statusDiv.style.position = "absolute";
    statusDiv.style.top = "5px";
    statusDiv.style.right = "10px";
    statusDiv.style.zIndex = 100;
    statusDiv.style.padding = "6px 12px";
    statusDiv.style.borderRadius = "6px";
    statusDiv.style.fontSize = "1em";
    document.body.appendChild(statusDiv);
  }
  statusDiv.textContent = msg;
  statusDiv.style.background = type === "error" ? "#ffdddd" : "#eef";
  statusDiv.style.color = type === "error" ? "#a00" : "#333";
}

// Display Python env info
function showPythonEnv(path) {
  let pyEnvEl = document.getElementById("python-env");
  if (!pyEnvEl) {
    pyEnvEl = document.createElement("div");
    pyEnvEl.id = "python-env";
    pyEnvEl.style.fontSize = "smaller";
    pyEnvEl.style.color = "#555";
    const controls = document.getElementById("controls");
    if (controls) controls.appendChild(pyEnvEl);
    else document.body.appendChild(pyEnvEl);
  }
  pyEnvEl.textContent = `Python executable: ${path}`;
}

// Update artist info panel
function updateArtistPanel(artist) {
  ["bio", "genre", "name", "nationality", "paintings", "wikipedia", "years"].forEach(key => {
    const el = document.getElementById(key);
    if (el) el.textContent = artist && artist[key] ? artist[key] : "";
  });
}

// Update image panel
function updateImagePanel(img) {
  const imageEl = document.getElementById("image");
  if (imageEl) {
    imageEl.innerHTML = "";
    if (img) imageEl.appendChild(img);
  }
  // Optionally show the details panel if in split mode
  if (img) showDetailsPanel(true);
}

// Show/hide the details panel (split view)
function showDetailsPanel(show = true) {
  document.body.classList.toggle("show-resized", show);
}

// Toggle split view
function toggleSplitView() {
  showDetailsPanel(!document.body.classList.contains("show-resized"));
}

export { hitTest, showArtistInfo, populateConfigDropdown, setControlState, showStatus, showPythonEnv, updateArtistPanel, updateImagePanel, showDetailsPanel, toggleSplitView };