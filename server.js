import { points, artists, getConfigs } from "./db.js";

Bun.serve({
  port: 3000,
  fetch: (req) => {
    const path = new URL(req.url).pathname;

    if (!path.startsWith("/api/")) {
      return new Response(
        Bun.file("public" + ((path === "/" && "/index.html") || path)),
        {
          headers: {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
          },
        }
      );
    }

    // API routing
    if (path === "/api/artists") {
      return new Response(JSON.stringify(artists()), {
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    }
    if (path === "/api/configs") {
      const url = new URL(req.url);
      const method = url.searchParams.get("method") || "umap";
      return new Response(JSON.stringify(getConfigs(method)), {
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    }
    if (path === "/api/points") {
      const url = new URL(req.url);
      const method = url.searchParams.get("method") || "umap";
      const config_id = url.searchParams.get("config_id");
      if (!config_id) {
        return new Response(JSON.stringify({ error: "Missing config_id" }), { status: 400 });
      }
      try {
        const pts = points(method, Number(config_id));
        return new Response(JSON.stringify(pts), {
          headers: {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
          },
        });
      } catch (e) {
        return new Response(JSON.stringify({ error: e.message }), { status: 500 });
      }
    }
    return new Response(JSON.stringify({ error: "Not found" }), { status: 404 });
  },
});
