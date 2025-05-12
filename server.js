import { getConfigs, getConfig, getProjectionPoints, getVizConfig, getVizPoints, getAllVizConfigs, artists, PARAM_COLS } from "./db.js";
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
        let stdout = "";
        let stderr = "";
        const decoder = new TextDecoder();
        if (proc.stdout) {
          for await (const chunk of proc.stdout) {
            stdout += decoder.decode(chunk);
          }
        }
        if (proc.stderr) {
          for await (const chunk of proc.stderr) {
            stderr += decoder.decode(chunk);
          }
        }
        const { exitCode } = await proc.exited;
        console.log("PYTHON RUN:", { stdout, stderr, exitCode });
        const headers = {
          "Content-Type": "application/json",
          "X-Content-Type-Options": "nosniff",
          "X-Frame-Options": "SAMEORIGIN"
        };
        if (exitCode !== undefined && exitCode !== 0) {
          return new Response(JSON.stringify({
            success: false,
            error: stderr || stdout || "Unknown error",
            stdout,
            stderr,
            exitCode
          }), {
            status: 500,
            headers
          });
        }
        return new Response(JSON.stringify({
          success: true,
          output: stdout,
          stderr: stderr || null,
          exitCode: exitCode === undefined ? 0 : exitCode
        }), {
          status: 200,
          headers
        });
      } catch (e) {
        return new Response(JSON.stringify({ error: "Failed to run script: " + e.message }), {
          status: 500,
          headers: { "Content-Type": "application/json" }
        });
      }
    }

    // ─── Python executable info endpoint ───
    if (path === "/api/python-env") {
      return new Response(JSON.stringify({ python: PY }), {
        headers: { "Content-Type": "application/json" }
      });
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
    // Endpoint to get Python executable path
    if (path === "/api/python-env") {
      return new Response(JSON.stringify({ python: PY }), {
        headers: { "Content-Type": "application/json" }
      });
    }

    if (path === "/api/artists") {
      return new Response(JSON.stringify(artists()), {
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    }
    // (Removed broken /api/visualization endpoint; now handled by static file server)

    // Get all configs for a method
    if (path === "/api/configs") {
      const method = url.searchParams.get("method") || "umap";
      return new Response(JSON.stringify(getConfigs(method)), {
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    }
    // Get a single config by method and config_id
    if (path === "/api/config") {
      const method = url.searchParams.get("method") || "umap";
      const config_id = url.searchParams.get("config_id");
      if (!config_id) {
        return new Response(JSON.stringify({ error: "Missing config_id" }), { status: 400 });
      }
      try {
        const cfg = getConfig(method, Number(config_id));
        return new Response(JSON.stringify(cfg), {
          headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
        });
      } catch (e) {
        return new Response(JSON.stringify({ error: e.message }), { status: 500 });
      }
    }
    // Get projection points for a method/config_id
    if (path === "/api/projection-points") {
      const method = url.searchParams.get("method") || "umap";
      const config_id = url.searchParams.get("config_id");
      if (!config_id) {
        return new Response(JSON.stringify({ error: "Missing config_id" }), { status: 400 });
      }
      try {
        const pts = getProjectionPoints(method, Number(config_id));
        return new Response(JSON.stringify(pts), {
          headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
        });
      } catch (e) {
        return new Response(JSON.stringify({ error: e.message }), { status: 500 });
      }
    }
    // Get all viz configs (for dropdown)
    if (path === "/api/viz-list") {
      try {
        const rows = getAllVizConfigs();
        return new Response(JSON.stringify(rows), {
          headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
        });
      } catch (e) {
        return new Response(JSON.stringify({ error: e.message }), { status: 500 });
      }
    }

    // Get viz_config by viz_id
    if (path === "/api/viz-config") {
      const viz_id = url.searchParams.get("viz_id");
      if (!viz_id) {
        return new Response(JSON.stringify({ error: "Missing viz_id" }), { status: 400 });
      }
      try {
        const row = getVizConfig(Number(viz_id));
        return new Response(JSON.stringify(row), {
          headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
        });
      } catch (e) {
        return new Response(JSON.stringify({ error: e.message }), { status: 500 });
      }
    }
    // Get viz_points by viz_id
    if (path === "/api/viz-points") {
      const viz_id = url.searchParams.get("viz_id");
      if (!viz_id) {
        return new Response(JSON.stringify({ error: "Missing viz_id" }), { status: 400 });
      }
      try {
        const rows = getVizPoints(Number(viz_id));
        return new Response(JSON.stringify(rows), {
          headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
        });
      } catch (e) {
        return new Response(JSON.stringify({ error: e.message }), { status: 500 });
      }
    }
    // Get PARAM_COLS mapping
    if (path === "/api/param-cols") {
      return new Response(JSON.stringify(PARAM_COLS), {
        headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
      });
    }
    return new Response(JSON.stringify({ error: "Not found" }), { status: 404 });
  }
});
