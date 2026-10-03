import { createServer } from "node:http";

const port = Number(process.env.PORT || 10000);

const server = createServer((req, res) => {
  if (req.url === "/health" || req.url === "/") {
    res.writeHead(200, {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    });
    res.end(
      JSON.stringify({
        ok: true,
        service: "smart-building-mqtt-worker",
      }),
    );
    return;
  }

  res.writeHead(404, {
    "content-type": "application/json; charset=utf-8",
  });
  res.end(JSON.stringify({ ok: false }));
});

server.listen(port, "0.0.0.0", () => {
  console.log(`[health] listening on :${port}`);
});

await import("./bridge-clean.js");

const shutdown = () => {
  server.close(() => process.exit(0));
};

process.on("SIGTERM", shutdown);
process.on("SIGINT", shutdown);
