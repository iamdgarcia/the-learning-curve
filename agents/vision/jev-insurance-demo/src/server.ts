#!/usr/bin/env bun
import { readFileSync, existsSync } from "fs";
import { join } from "path";

const API_KEY = process.env.NOVITA_API_KEY!;
const PORT = parseInt(process.env.PORT ?? "3456");
const ROOT = join(import.meta.dir, "..");

function serveFile(path: string, ct: string) {
  try { return new Response(readFileSync(path), { headers: { "Content-Type": ct } }); }
  catch { return new Response("Not found", { status: 404 }); }
}

const MIME: Record<string, string> = {
  ".html": "text/html", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
  ".png": "image/png", ".webp": "image/webp", ".json": "application/json",
};

Bun.serve({
  port: PORT,
  async fetch(req) {
    const url = new URL(req.url);

    // POST /api/decide → proxy to Novita
    if (url.pathname === "/api/decide" && req.method === "POST") {
      const upstream = await fetch("https://api.novita.ai/v3/autotrust/v1/decide", {
        method: "POST",
        headers: { Authorization: `Bearer ${API_KEY}`, "Content-Type": "application/json" },
        body: await req.text(),
      });
      return new Response(await upstream.text(), {
        status: upstream.status,
        headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
      });
    }

    // GET /api/results → benchmark results JSON
    if (url.pathname === "/api/results") {
      const p = join(ROOT, "data/results.json");
      if (!existsSync(p)) return new Response(JSON.stringify({ error: "No benchmark run yet" }), {
        status: 404, headers: { "Content-Type": "application/json" },
      });
      return new Response(readFileSync(p), { headers: { "Content-Type": "application/json" } });
    }

    // GET /images/:file → saved benchmark images
    if (url.pathname.startsWith("/images/")) {
      const file = url.pathname.replace("/images/", "");
      return serveFile(join(ROOT, "data/images", file), "image/jpeg");
    }

    // GET / → demo
    return serveFile(join(ROOT, "demo/index.html"), "text/html");
  },
});

console.log(`\n🚗 Insurance demo → http://localhost:${PORT}\n`);
