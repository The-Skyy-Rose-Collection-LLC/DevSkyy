"""Live dashboard for a render-pipeline run — reads the RunLog JSONL, serves HTML.

Read-only by design: the monitor polls ``renders/oai/_runs/run-*.jsonl`` (written
by :mod:`oai_render.runlog`) and never touches the pipeline, so a monitor crash
can never cost a render. Works live (file still being appended) and post-hoc
(forensics on a finished run).

Usage::

    python scripts/oai-render-monitor.py                 # newest run, port 8946
    python scripts/oai-render-monitor.py --port 9000
    python scripts/oai-render-monitor.py --run renders/oai/_runs/run-X.jsonl
    python scripts/oai-render-monitor.py --once          # print aggregate JSON, exit
"""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .runlog import RUNS_DIR, load_events, newest_run_file

DEFAULT_PORT = 8946

# Terminal SKU states; everything else is in-flight.
_TERMINAL = {"accepted", "qc_failed", "error", "skipped"}


def aggregate(events: list[dict]) -> dict:
    """Fold a run's event stream into dashboard state: run meta + per-SKU progress."""
    run: dict = {"started": None, "finished": False, "spent_usd": 0.0}
    skus: dict[str, dict] = {}

    def sku_state(sku: str) -> dict:
        return skus.setdefault(
            sku,
            {"sku": sku, "status": "pending", "attempts": [], "name": "", "output_path": ""},
        )

    for ev in events:
        kind = ev.get("event", "")
        spent = ev.get("spent_usd")
        if isinstance(spent, (int, float)):
            run["spent_usd"] = max(run["spent_usd"], float(spent))

        if kind == "run_start":
            run.update(
                started=ev.get("ts"),
                n_plans=ev.get("n_plans"),
                est_cost_usd=ev.get("est_cost_usd"),
                cap_usd=ev.get("cap_usd"),
                judge=ev.get("judge", ""),
            )
            for s in ev.get("skus", []):
                sku_state(s)
        elif kind == "run_end":
            run["finished"] = True
            run["summary"] = {
                k: ev.get(k, 0) for k in ("rendered", "skipped", "errored", "qc_failed")
            }
            # run_end may carry the cap when run_start was lost (torn file); the
            # run_start value wins otherwise via the fallback default.
            run["cap_usd"] = ev.get("cap_usd", run.get("cap_usd"))
        elif kind == "attempt":
            st = sku_state(ev["sku"])
            st["status"] = "rendering"
            st["name"] = ev.get("name", st["name"])
            st["attempts"].append({"n": ev.get("attempt"), "verdict": None})
        elif kind == "qc_verdict":
            st = sku_state(ev["sku"])
            verdict = {
                "passed": ev.get("passed"),
                "tags": ev.get("tags", []),
                "reason": ev.get("reason", ""),
                "analysis": ev.get("analysis", ""),
            }
            if st["attempts"]:
                st["attempts"][-1]["verdict"] = verdict
            else:  # verdict without a logged attempt (defensive)
                st["attempts"].append({"n": ev.get("attempt"), "verdict": verdict})
        elif kind == "accepted":
            st = sku_state(ev["sku"])
            st["status"] = "accepted"
            st["output_path"] = ev.get("path", "")
        elif kind == "quarantined":
            sku_state(ev["sku"])["status"] = "retrying"
        elif kind == "qc_exhausted":
            st = sku_state(ev["sku"])
            st["status"] = "qc_failed"
            st["reason"] = ev.get("reason", "")
        elif kind in ("render_error", "budget_stop"):
            st = sku_state(ev["sku"])
            st["status"] = "error"
            st["reason"] = ev.get("reason", "budget cap reached")
        elif kind == "skipped":
            st = sku_state(ev["sku"])
            st["status"] = "skipped"
            st["reason"] = ev.get("reason", "")

    done = sum(1 for s in skus.values() if s["status"] in _TERMINAL)
    run["progress"] = {"done": done, "total": len(skus)}
    return {"run": run, "skus": list(skus.values())}


def snapshot(run_path: Path | None, runs_dir: Path = RUNS_DIR) -> dict:
    """Aggregate the pinned run file, or the newest one in ``runs_dir``."""
    path = run_path or newest_run_file(runs_dir)
    if path is None or not path.exists():
        return {"run": {"error": f"no run-*.jsonl found in {runs_dir}"}, "skus": [], "file": ""}
    data = aggregate(load_events(path))
    data["file"] = path.name
    return data


# ── Dashboard page (static shell; all data arrives via /data polling) ────────
# DOM is built exclusively with createElement/textContent — no innerHTML — so
# judge reasons/analyses (model-generated text) can never inject markup.
_PAGE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SkyyRose Render Pipeline — Live Monitor</title>
<style>
  :root{--accent:#B76E79;--bg:#0A0A0A;--card:#161214;--ok:#3fb950;--bad:#f85149;--warn:#d29922;--muted:#9a8f93}
  body{font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:#eee;margin:0;padding:1.2rem}
  h1{font-size:1.05rem;margin:0 0 .2rem;color:var(--accent);letter-spacing:.06em;text-transform:uppercase}
  #meta{color:var(--muted);font-size:.85em;margin-bottom:1rem}
  #spendwrap{background:#1d1518;border-radius:6px;height:22px;position:relative;margin:.6rem 0 1.2rem;max-width:640px;overflow:hidden}
  #spendbar{background:var(--accent);height:100%;width:0;transition:width .6s}
  #spendlabel{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:.8em;color:#fff}
  #grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:.8rem}
  .card{background:var(--card);border:1px solid #2a2226;border-radius:8px;padding:.7rem .9rem}
  .card h2{font-size:.95em;margin:0 0 .3rem;display:flex;justify-content:space-between;gap:.5rem}
  .chip{font-size:.72em;padding:.1rem .5rem;border-radius:999px;align-self:center;white-space:nowrap}
  .accepted{background:#12351c;color:var(--ok)} .rendering,.retrying{background:#33260b;color:var(--warn)}
  .qc_failed,.error{background:#3a1517;color:var(--bad)} .pending,.skipped{background:#26222a;color:var(--muted)}
  .att{border-top:1px dashed #2e272b;margin-top:.45rem;padding-top:.45rem;font-size:.83em}
  .tags{color:var(--bad)} .reason{color:#ccc}
  details{margin-top:.25rem} summary{cursor:pointer;color:var(--accent);font-size:.85em}
  .analysis{color:var(--muted);white-space:pre-wrap;font-size:.92em;margin:.3rem 0 0}
</style></head><body>
<h1>SkyyRose Render Pipeline</h1>
<div id="meta">connecting…</div>
<div id="spendwrap"><div id="spendbar"></div><div id="spendlabel"></div></div>
<div id="grid"></div>
<script>
"use strict";
function el(tag, cls, text){const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;}
function render(d){
  const run=d.run||{}, meta=document.getElementById("meta");
  const prog=run.progress||{done:0,total:0};
  meta.textContent=(d.file||"no run file")
    +(run.judge?"  ·  judge: "+run.judge:"")
    +"  ·  "+prog.done+"/"+prog.total+" done"
    +(run.finished?"  ·  FINISHED":"  ·  live")
    +(run.error?"  ·  "+run.error:"");
  const spent=run.spent_usd||0, cap=run.cap_usd||50;
  document.getElementById("spendbar").style.width=Math.min(100,100*spent/cap)+"%";
  document.getElementById("spendlabel").textContent="$"+spent.toFixed(2)+" of $"+cap.toFixed(2)+" cap";
  const grid=document.getElementById("grid");
  grid.replaceChildren();
  for(const s of d.skus||[]){
    const card=el("div","card");
    const h=el("h2",null,"");
    h.append(el("span",null,s.sku+(s.name?" — "+s.name:"")), el("span","chip "+s.status,s.status));
    card.append(h);
    if(s.reason)card.append(el("div","reason",s.reason));
    for(const a of s.attempts||[]){
      const att=el("div","att","attempt "+a.n);
      if(a.verdict){
        att.append(el("span",null," → "+(a.verdict.passed?"QC pass":"QC fail")));
        if(!a.verdict.passed&&a.verdict.tags.length)att.append(el("div","tags",a.verdict.tags.join(", ")));
        if(a.verdict.reason)att.append(el("div","reason",a.verdict.reason));
        if(a.verdict.analysis){
          const det=el("details");det.append(el("summary",null,"judge analysis"),el("div","analysis",a.verdict.analysis));
          att.append(det);
        }
      }
      card.append(att);
    }
    grid.append(card);
  }
}
async function poll(){
  try{const r=await fetch("/data",{cache:"no-store"});render(await r.json());}
  catch(e){document.getElementById("meta").textContent="poll failed: "+e;}
}
poll();setInterval(poll,2500);
</script></body></html>
"""


def make_handler(run_path: Path | None, runs_dir: Path):
    """Build the request handler bound to a pinned run file (or newest-run mode)."""

    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802 — BaseHTTPRequestHandler API
            # Exact-match routing (query string tolerated on /data for cache busting);
            # anything else is a 404 — no surprise endpoints on a data-bearing server.
            if self.path == "/data" or self.path.startswith("/data?"):
                body = json.dumps(snapshot(run_path, runs_dir)).encode("utf-8")
                ctype = "application/json"
            elif self.path in ("/", "/index.html"):
                body = _PAGE.encode("utf-8")
                ctype = "text/html; charset=utf-8"
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *args):  # quiet: polling spams stderr otherwise
            pass

    return _Handler


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="oai-render-monitor", description=__doc__)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--run", type=Path, default=None, help="Pin a specific run-*.jsonl file.")
    parser.add_argument("--runs-dir", type=Path, default=RUNS_DIR)
    parser.add_argument(
        "--once", action="store_true", help="Print the aggregate JSON once and exit (no server)."
    )
    args = parser.parse_args(argv)

    if args.once:
        print(json.dumps(snapshot(args.run, args.runs_dir), indent=2))
        return 0

    # Localhost only — this serves spend data + judge reasoning, not for LAN exposure.
    try:
        server = ThreadingHTTPServer(
            ("127.0.0.1", args.port), make_handler(args.run, args.runs_dir)
        )
    except OSError as exc:
        print(f"Cannot bind 127.0.0.1:{args.port}: {exc}. Is a monitor already running?")
        return 1
    target = args.run or f"newest in {args.runs_dir}"
    print(f"Monitoring {target}")
    print(f"Dashboard: http://127.0.0.1:{args.port}/  (Ctrl-C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
