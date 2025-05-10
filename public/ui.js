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
  
  export { hitTest, showArtistInfo };
  