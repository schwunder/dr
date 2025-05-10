// Load a single image (thumbnail or resized)
const loadImage = (filename, isResized = false) =>
    new Promise((resolve, reject) => {
      const img = new Image();
      img.crossOrigin = "anonymous"; // prevent tainted canvas security errors
  
      img.onerror = (e) => reject(`failed to load ${filename}`);
      img.onload = () => resolve(img);
  
      const path = `http://localhost:3001/${
        isResized ? "resized" : "thumbnails"
      }/${filename}`;
      img.src = path;
    });
  
  // load all thumbnails for points
  const thumbnails = async (points) => {
    console.log(`Loading ${points.length} thumbnails...`);
    const images = await Promise.all(points.map((p) => loadImage(p.filename)));
    points.forEach((p, i) => (p.thumb = images[i]));
    return points;
  };
  
  // load a resized image
  const resized = (filename) => loadImage(filename, true);
  
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
  
  export { thumbnails, resized, artists };
  