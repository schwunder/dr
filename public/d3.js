// Core rendering and transformation functions
const IMAGE_SIZE = 75;
const MAX_BITMAP_SIZE = 16384;

// Get canvas dimensions and update canvas size
function dimensions(canvas) {
  const dims = { width: window.innerWidth, height: window.innerHeight };
  canvas.width = dims.width;
  canvas.height = dims.height;
  return dims;
}

// Create scales for the data points
function createScales(points, margin, dims) {
  const xExtent = d3.extent(points, (p) => p.x);
  const yExtent = d3.extent(points, (p) => p.y);

  // Keep aspect ratio intact
  const dataWidth = xExtent[1] - xExtent[0];
  const dataHeight = yExtent[1] - yExtent[0];
  const dataAspect = dataWidth / dataHeight;

  const size = Math.min(dims.width, dims.height) - 2 * margin;

  const x = d3
    .scaleLinear()
    .domain(xExtent)
    .range([margin, margin + size * dataAspect]);

  const y = d3
    .scaleLinear()
    .domain(yExtent)
    .range([margin + size, margin]); // Flip Y axis

  return { x, y };
}

// Set up zoom behavior
function setupZoom(canvas, onZoom) {
  const zoomBehavior = d3
    .zoom()
    .scaleExtent([0.01, 20])
    .on("zoom", (e) => onZoom(e.transform));

  d3.select(canvas).call(zoomBehavior);
  return zoomBehavior;
}

// Draw all points to a bitmap with specified bounds key
function drawToBitmap(ctx, points, scales, dims, boundsKey = "bounds") {
  ctx.clearRect(0, 0, dims.width, dims.height);

  points.forEach((p) => {
    const cx = scales.x(p.x);
    const cy = scales.y(p.y);

    // Store bounds with the specified key
    p[boundsKey] = {
      x: cx - IMAGE_SIZE / 2,
      y: cy - IMAGE_SIZE / 2,
      width: IMAGE_SIZE,
      height: IMAGE_SIZE,
    };

    ctx.drawImage(
      p.thumb,
      cx - IMAGE_SIZE / 2,
      cy - IMAGE_SIZE / 2,
      IMAGE_SIZE,
      IMAGE_SIZE
    );
  });
}

// Render the current view with transform
function renderView(ctx, dims, transform, bitmap) {
  if (!bitmap) {
    console.error("Attempted to render with null bitmap");
    return;
  }

  ctx.clearRect(0, 0, dims.width, dims.height);
  ctx.save();
  ctx.setTransform(transform.k, 0, 0, transform.k, transform.x, transform.y);
  ctx.drawImage(bitmap, 0, 0);
  ctx.restore();
}

// Create initial scale to fit view
function getFitScale(dims, bitmapWidth, bitmapHeight) {
  return Math.min(dims.width / bitmapWidth, dims.height / bitmapHeight);
}

// Reset zoom to fit view
function resetZoom(canvas, scale) {
  const resetTransform = d3.zoomIdentity.scale(scale);
  d3.select(canvas).call(d3.zoom().transform, resetTransform);
  return resetTransform;
}

export {
  dimensions,
  createScales,
  setupZoom,
  drawToBitmap,
  renderView,
  getFitScale,
  resetZoom,
  IMAGE_SIZE,
  MAX_BITMAP_SIZE,
};
