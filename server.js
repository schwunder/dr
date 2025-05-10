import { points, artists, getConfigs } from "./db.js";
import { serveStatic, spawn } from "bun";

const PY = "./.venv/bin/python"; // or just "python3" if your venv is activated

Bun.serve({
  port: 3000,
  async fetch(req) {
    const url = new URL(req.url);
    const path = url.pathname;

    // ─── 1) Run a Python script ───
    if (path === "/api/run" && req.method === "POST") {
      try {
        const { method, config } = await req.json();
        const proc = spawn([
          PY,
          "run.py",
          "--method", method,
          "--config", config
        ]);
        const { stdout, stderr, exitCode } = await proc.exited;
        if (exitCode !== 0) {
          return new Response(stderr, { status: 500 });
        }
        return new Response(stdout || "OK");
      } catch (e) {
        return new Response("Failed to run script: " + e.message, { status: 500 });
      }
    }

    // ─── 2) Static files ───
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
