// Load a single image (thumbnail or resized)
const loadImage = (filename, type = "thumbnails") =>
  new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onerror = (e) => reject(`failed to load ${filename}`);
    img.onload = () => resolve(img);
    const path = `http://localhost:3001/${type}/${filename}`;
    img.src = path;
  });
  
  // load all thumbnails for points
  const thumbnails = async (points) => {
  const validPoints = points.filter((p) => p.filename);
  if (validPoints.length !== points.length) {
    console.warn("Some points are missing filenames and will be skipped:", points.filter(p => !p.filename));
  }
  console.log(`Loading ${validPoints.length} thumbnails...`);
  const images = await Promise.all(validPoints.map((p) => loadImage(p.filename)));
  validPoints.forEach((p, i) => (p.thumb = images[i]));
  return validPoints;
};

  // load a resized image
  const resized = (filename) => loadImage(filename, "resized");
  
  // fetch artist information
  const artists = async (name) => {
    try {
      const response = await fetch("/api/artists");
      if (!response.ok) throw new Error(response.statusText);
      const data = await response.json();
      return data.find((a) => a.name === name);
    } catch {
      return null;
    }
  };
  
  // Load a visualization image (and optionally fetch metadata elsewhere)
const visualizations = (filename) => loadImage(filename, "visualizations");

export { thumbnails, resized, artists, visualizations };

  