// @ts-nocheck
import { useState, useEffect, useRef, useCallback } from "react";

// ═══════════════════════════════════════════════════════════════
// DevSkyy LLM Roundtable — Competition Arena
// Multi-model battle system for task allocation
// The best response wins. Every time.
// ═══════════════════════════════════════════════════════════════

const R = "#B76E79", SV = "#C0C0C0", CR = "#DC143C", GD = "#D4AF37",
      GR = "#00FF88", BL = "#00AAFF", BG = "#08080A", CD = "#0E0E12",
      BD = "rgba(183,110,121,0.08)", TX = "#F5E6D3", DM = "rgba(245,230,211,0.35)";

// ── MODEL ROSTER ──
const MODELS = [
  { id: "claude-opus", name: "Claude Opus 4.6", provider: "Anthropic", color: "#D4A574", icon: "◆", tier: "frontier", costPer1k: 0.015, avgLatency: 2800, contextWindow: "200K" },
  { id: "claude-sonnet", name: "Claude Sonnet 4.6", provider: "Anthropic", color: "#C49B6A", icon: "◆", tier: "performance", costPer1k: 0.003, avgLatency: 1200, contextWindow: "200K" },
  { id: "gpt-4o", name: "GPT-4o", provider: "OpenAI", color: "#74AA9C", icon: "●", tier: "frontier", costPer1k: 0.005, avgLatency: 1800, contextWindow: "128K" },
  { id: "gpt-4o-mini", name: "GPT-4o Mini", provider: "OpenAI", color: "#5E9E8F", icon: "●", tier: "speed", costPer1k: 0.00015, avgLatency: 600, contextWindow: "128K" },
  { id: "gemini-2", name: "Gemini 2.5 Pro", provider: "Google", color: "#4285F4", icon: "◈", tier: "frontier", costPer1k: 0.00125, avgLatency: 2200, contextWindow: "1M" },
  { id: "gemini-flash", name: "Gemini 2.0 Flash", provider: "Google", color: "#34A853", icon: "◈", tier: "speed", costPer1k: 0.0001, avgLatency: 400, contextWindow: "1M" },
  { id: "deepseek-r1", name: "DeepSeek R1", provider: "DeepSeek", color: "#6366F1", icon: "◇", tier: "reasoning", costPer1k: 0.0014, avgLatency: 4200, contextWindow: "64K" },
  { id: "llama-405b", name: "Llama 3.3 70B", provider: "Meta (HF)", color: "#0668E1", icon: "▣", tier: "open-source", costPer1k: 0.0009, avgLatency: 1600, contextWindow: "128K" },
];

// ── ELO LEADERBOARD ──
const LEADERBOARD = [
  { modelId: "claude-opus", elo: 1847, wins: 342, losses: 41, draws: 17, winRate: 85.5, streak: 8, totalBattles: 400, tokensGenerated: "48.2M", avgScore: 94.2, strongSuit: "Complex reasoning, CRO copy, brand voice" },
  { modelId: "claude-sonnet", elo: 1792, wins: 298, losses: 67, draws: 35, winRate: 74.5, streak: 4, totalBattles: 400, tokensGenerated: "62.8M", avgScore: 91.7, strongSuit: "Balanced speed + quality, SEO, product descriptions" },
  { modelId: "gemini-2", elo: 1756, wins: 264, losses: 96, draws: 40, winRate: 66.0, streak: 2, totalBattles: 400, tokensGenerated: "55.1M", avgScore: 88.4, strongSuit: "Long context analysis, multimodal, research" },
  { modelId: "gpt-4o", elo: 1738, wins: 251, losses: 112, draws: 37, winRate: 62.8, streak: 1, totalBattles: 400, tokensGenerated: "41.6M", avgScore: 87.1, strongSuit: "Social media copy, vision tasks, quick drafts" },
  { modelId: "deepseek-r1", elo: 1704, wins: 228, losses: 134, draws: 38, winRate: 57.0, streak: 0, totalBattles: 400, tokensGenerated: "38.4M", avgScore: 85.6, strongSuit: "Chain-of-thought, math, pricing optimization" },
  { modelId: "llama-405b", elo: 1681, wins: 210, losses: 152, draws: 38, winRate: 52.5, streak: 3, totalBattles: 400, tokensGenerated: "44.9M", avgScore: 82.3, strongSuit: "Bulk generation, cost-effective, embeddings" },
  { modelId: "gpt-4o-mini", elo: 1653, wins: 194, losses: 171, draws: 35, winRate: 48.5, streak: 0, totalBattles: 400, tokensGenerated: "71.2M", avgScore: 78.9, strongSuit: "Classification, tagging, simple Q&A, speed" },
  { modelId: "gemini-flash", elo: 1628, wins: 178, losses: 187, draws: 35, winRate: 44.5, streak: 0, totalBattles: 400, tokensGenerated: "82.6M", avgScore: 76.2, strongSuit: "Fastest inference, bulk ops, image processing" },
];

// ── ACTIVE BATTLES ──
const BATTLES = [
  {
    id: "B-1847",
    task: "Write a product description for BLACK ROSE Heavyweight Hoodie — 280gsm cotton, double-stitched, limited to 200 units",
    category: "Content",
    collection: "black-rose",
    status: "judging",
    startedAt: "12s ago",
    competitors: [
      { modelId: "claude-opus", status: "complete", latency: 2.4, tokens: 187, score: 96, output: "Built for those who move through darkness like it's home. 280gsm cotton that doesn't apologize for its weight. Double-stitched seams because shortcuts aren't in our vocabulary..." },
      { modelId: "claude-sonnet", status: "complete", latency: 1.1, tokens: 164, score: 91, output: "The BLACK ROSE Heavyweight Hoodie is the definition of dark luxury. Crafted from premium 280gsm cotton with reinforced double-stitched seams..." },
      { modelId: "gpt-4o", status: "complete", latency: 1.6, tokens: 192, score: 87, output: "Introducing the BLACK ROSE Heavyweight Hoodie — where streetwear meets sophisticated darkness. Made from 280gsm premium cotton..." },
      { modelId: "gemini-2", status: "complete", latency: 2.1, tokens: 178, score: 84, output: "The BLACK ROSE Heavyweight Hoodie represents the pinnacle of SkyyRose's dark luxury aesthetic. At 280 grams per square meter..." },
    ],
    winner: "claude-opus",
    criteria: ["Brand Voice", "Emotional Impact", "Conversion Potential", "Accuracy"]
  },
  {
    id: "B-1848",
    task: "Generate 5 Instagram carousel slide captions for LOVE HURTS spring lookbook — emotional, Gen Z tone, include CTAs",
    category: "Social Media",
    collection: "love-hurts",
    status: "competing",
    startedAt: "3s ago",
    competitors: [
      { modelId: "claude-sonnet", status: "complete", latency: 1.3, tokens: 245, score: null, output: null },
      { modelId: "gpt-4o", status: "generating", latency: null, tokens: 89, score: null, output: null },
      { modelId: "gemini-2", status: "generating", latency: null, tokens: 142, score: null, output: null },
      { modelId: "gpt-4o-mini", status: "generating", latency: null, tokens: 201, score: null, output: null },
    ],
    winner: null,
    criteria: ["Platform Fit", "Engagement Potential", "Brand Alignment", "CTA Strength"]
  },
  {
    id: "B-1849",
    task: "Analyze conversion funnel for LP SIGNATURE — identify top 3 drop-off points and suggest A/B test hypotheses",
    category: "Analytics",
    collection: "signature",
    status: "competing",
    startedAt: "8s ago",
    competitors: [
      { modelId: "claude-opus", status: "generating", latency: null, tokens: 312, score: null, output: null },
      { modelId: "deepseek-r1", status: "generating", latency: null, tokens: 478, score: null, output: null },
      { modelId: "gemini-2", status: "complete", latency: 2.8, tokens: 567, score: null, output: null },
      { modelId: "claude-sonnet", status: "generating", latency: null, tokens: 234, score: null, output: null },
    ],
    winner: null,
    criteria: ["Analytical Depth", "Actionability", "Data Accuracy", "A/B Test Quality"]
  },
];

// ── BATTLE HISTORY ──
const HISTORY = [
  { id: "B-1846", task: "SEO meta descriptions for 8 collection pages", winner: "claude-sonnet", category: "SEO", time: "4m ago", winnerScore: 93, runnerUp: "gpt-4o", runnerScore: 88 },
  { id: "B-1845", task: "Dynamic pricing model for BLACK ROSE limited restock", winner: "claude-opus", category: "Pricing", time: "12m ago", winnerScore: 97, runnerUp: "deepseek-r1", runnerScore: 94 },
  { id: "B-1844", task: "Email subject lines — abandoned cart flow (5 variants)", winner: "gpt-4o", category: "Email", time: "18m ago", winnerScore: 89, runnerUp: "claude-sonnet", runnerScore: 87 },
  { id: "B-1843", task: "Customer support response — sizing question", winner: "gpt-4o-mini", category: "Support", time: "25m ago", winnerScore: 85, runnerUp: "gemini-flash", runnerScore: 82 },
  { id: "B-1842", task: "Blog post outline: 'From Oakland to the World'", winner: "claude-opus", category: "Content", time: "32m ago", winnerScore: 96, runnerUp: "claude-sonnet", runnerScore: 92 },
  { id: "B-1841", task: "Classify 200 customer reviews by sentiment + topic", winner: "gemini-flash", category: "Classification", time: "41m ago", winnerScore: 91, runnerUp: "gpt-4o-mini", runnerScore: 89 },
  { id: "B-1840", task: "Generate alt-text for 12 product images", winner: "gpt-4o", category: "Vision", time: "55m ago", winnerScore: 90, runnerUp: "gemini-2", runnerScore: 88 },
  { id: "B-1839", task: "Rewrite landing page hero — LOVE HURTS emotional hook", winner: "claude-opus", category: "Conversion", time: "1h ago", winnerScore: 98, runnerUp: "claude-sonnet", runnerScore: 91 },
];

// ── CATEGORY WIN RATES ──
const CATEGORY_DOMINANCE = [
  { category: "Brand Copy", leader: "claude-opus", winRate: 92, battles: 68 },
  { category: "Product Descriptions", leader: "claude-opus", winRate: 88, battles: 124 },
  { category: "SEO / Meta", leader: "claude-sonnet", winRate: 78, battles: 86 },
  { category: "Social Media", leader: "gpt-4o", winRate: 71, battles: 94 },
  { category: "Email Campaigns", leader: "claude-sonnet", winRate: 74, battles: 52 },
  { category: "Analytics / Reports", leader: "claude-opus", winRate: 86, battles: 78 },
  { category: "Classification", leader: "gemini-flash", winRate: 82, battles: 112 },
  { category: "Vision Tasks", leader: "gpt-4o", winRate: 68, battles: 44 },
  { category: "Pricing / Math", leader: "deepseek-r1", winRate: 73, battles: 36 },
  { category: "Bulk Processing", leader: "gemini-flash", winRate: 88, battles: 156 },
  { category: "Customer Support", leader: "gpt-4o-mini", winRate: 76, battles: 64 },
  { category: "Code Generation", leader: "claude-sonnet", winRate: 81, battles: 42 },
];

// ── HELPERS ──
const getModel = id => MODELS.find(m => m.id === id) || MODELS[0];
const cc = c => c === "black-rose" ? SV : c === "love-hurts" ? CR : c === "signature" ? GD : R;
const sc = s => s === "complete" || s === "judging" ? GR : s === "generating" || s === "competing" ? BL : s === "queued" ? GD : DM;

const Pulse = ({ color, size = 5 }) => (
  <span style={{ display: "inline-block", width: size, height: size, borderRadius: "50%", background: color, boxShadow: `0 0 ${size + 2}px ${color}`, animation: "pulse 2s ease-in-out infinite", flexShrink: 0 }} />
);

const Bar = ({ pct, color, h = 3 }) => (
  <div style={{ height: h, background: BD, borderRadius: 1, overflow: "hidden", flex: 1 }}>
    <div style={{ height: "100%", width: `${pct}%`, background: color, borderRadius: 1, transition: "width 1s ease" }} />
  </div>
);

const Tag = ({ children, color }) => (
  <span style={{ padding: "2px 8px", border: `1px solid ${color}33`, background: `${color}0A`, color, fontFamily: "'JetBrains Mono', monospace", fontSize: 8, letterSpacing: 1, borderRadius: 1 }}>{children}</span>
);

const TABS = [
  { label: "LIVE ARENA", icon: "⚔" },
  { label: "LEADERBOARD", icon: "◆" },
  { label: "BATTLE HISTORY", icon: "◷" },
  { label: "CATEGORY MAP", icon: "⊞" },
  { label: "MODEL PROFILES", icon: "◉" },
];

export default function LLMRoundtable() {
  const [tab, setTab] = useState(0);
  const [time, setTime] = useState(new Date());
  const [expandedBattle, setExpandedBattle] = useState("B-1847");
  const [selectedModel, setSelectedModel] = useState(null);
  const [simTokens, setSimTokens] = useState({});
  const [simProgress, setSimProgress] = useState({});

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  // Simulate token generation for active battles
  useEffect(() => {
    const t = setInterval(() => {
      setSimTokens(prev => {
        const next = { ...prev };
        BATTLES.forEach(b => {
          if (b.status === "competing") {
            b.competitors.forEach(c => {
              if (c.status === "generating") {
                const key = `${b.id}-${c.modelId}`;
                next[key] = (prev[key] || c.tokens) + Math.floor(Math.random() * 12);
              }
            });
          }
        });
        return next;
      });
    }, 300);
    return () => clearInterval(t);
  }, []);

  // Canvas for live battle visualization
  const canvasRef = useRef(null);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || tab !== 0) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width = canvas.offsetWidth * 2;
    const H = canvas.height = 200;
    canvas.style.height = '100px';
    let frame = 0, rafId;

    const draw = () => {
      frame++;
      ctx.fillStyle = BG;
      ctx.fillRect(0, 0, W, H);

      // Draw competition lanes
      const laneH = H / 4;
      const competitors = BATTLES.find(b => b.id === expandedBattle)?.competitors || [];
      competitors.forEach((c, i) => {
        const model = getModel(c.modelId);
        const y = i * laneH;
        const progress = c.status === "complete" ? 1 : Math.min(1, (c.tokens + (simTokens[`${expandedBattle}-${c.modelId}`] || 0)) / 500);

        // Lane background
        ctx.fillStyle = `${model.color}08`;
        ctx.fillRect(0, y + 2, W, laneH - 4);

        // Progress bar
        const barW = progress * W * 0.85;
        const grad = ctx.createLinearGradient(0, 0, barW, 0);
        grad.addColorStop(0, `${model.color}15`);
        grad.addColorStop(1, `${model.color}40`);
        ctx.fillStyle = grad;
        ctx.fillRect(40, y + 8, barW, laneH - 16);

        // Leading edge glow
        if (c.status === "generating") {
          const glowX = 40 + barW;
          const glow = ctx.createRadialGradient(glowX, y + laneH / 2, 0, glowX, y + laneH / 2, 20);
          glow.addColorStop(0, `${model.color}60`);
          glow.addColorStop(1, `${model.color}00`);
          ctx.fillStyle = glow;
          ctx.fillRect(glowX - 20, y, 40, laneH);
        }

        // Model icon
        ctx.font = "18px sans-serif";
        ctx.fillStyle = model.color;
        ctx.fillText(model.icon, 10, y + laneH / 2 + 6);

        // Score badge (if complete)
        if (c.score !== null) {
          const sx = 40 + barW + 8;
          ctx.font = "bold 16px 'JetBrains Mono', monospace";
          ctx.fillStyle = c.score >= 90 ? GR : c.score >= 80 ? GD : TX;
          ctx.fillText(c.score.toString(), sx, y + laneH / 2 + 6);
        }

        // Token counter
        const tokens = simTokens[`${expandedBattle}-${c.modelId}`] || c.tokens;
        ctx.font = "10px 'JetBrains Mono', monospace";
        ctx.fillStyle = DM;
        ctx.textAlign = "right";
        ctx.fillText(`${tokens} tok`, W - 10, y + laneH / 2 + 4);
        ctx.textAlign = "left";

        // Pulse particles for generating state
        if (c.status === "generating") {
          for (let p = 0; p < 3; p++) {
            const px = 40 + barW - Math.random() * 30;
            const py = y + laneH / 2 + (Math.random() - 0.5) * (laneH - 20);
            ctx.beginPath();
            ctx.arc(px, py, 1 + Math.random() * 1.5, 0, Math.PI * 2);
            ctx.fillStyle = `${model.color}${Math.floor(Math.random() * 80 + 40).toString(16)}`;
            ctx.fill();
          }
        }
      });

      rafId = requestAnimationFrame(draw);
    };
    draw();
    return () => cancelAnimationFrame(rafId);
  }, [tab, expandedBattle, simTokens]);

  const totalBattles = LEADERBOARD.reduce((s, l) => s + l.totalBattles, 0) / 2;
  const totalTokens = LEADERBOARD.reduce((s, l) => s + parseFloat(l.tokensGenerated), 0);

  return (
    <div style={{ minHeight: "100vh", background: BG, color: TX, fontFamily: "'Inter', -apple-system, sans-serif", fontSize: 13 }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&family=Cinzel:wght@400;600;700;900&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::-webkit-scrollbar { width: 3px; height: 3px; }
        ::-webkit-scrollbar-track { background: ${BG}; }
        ::-webkit-scrollbar-thumb { background: rgba(183,110,121,0.15); }
        @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
        @keyframes slideUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes crownGlow { 0%,100% { text-shadow: 0 0 8px ${GD}40; } 50% { text-shadow: 0 0 20px ${GD}80; } }
        @keyframes battlePulse { 0%,100% { border-color: rgba(0,170,255,0.1); } 50% { border-color: rgba(0,170,255,0.25); } }
        @keyframes tokenStream { from { opacity: 0; transform: translateX(-8px); } to { opacity: 1; transform: translateX(0); } }
        .card { background: ${CD}; border: 1px solid ${BD}; border-radius: 2px; transition: all 0.3s; }
        .card:hover { border-color: rgba(183,110,121,0.14); }
        .lbl { font-family: 'JetBrains Mono', monospace; font-size: 8px; letter-spacing: 3px; text-transform: uppercase; color: ${DM}; }
        .val { font-family: 'Cinzel', serif; font-size: 24px; font-weight: 600; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .tab-btn { padding: 10px 16px; background: none; border: 1px solid transparent; color: ${DM}; cursor: pointer; font-family: 'JetBrains Mono', monospace; font-size: 9px; letter-spacing: 1.5px; text-transform: uppercase; transition: all 0.2s; display: flex; align-items: center; gap: 8px; white-space: nowrap; }
        .tab-btn:hover { color: ${TX}; }
        .tab-btn.active { color: ${R}; border-color: ${R}; background: rgba(183,110,121,0.04); }
        .action-btn { padding: 7px 16px; background: rgba(183,110,121,0.06); border: 1px solid rgba(183,110,121,0.15); color: ${R}; cursor: pointer; font-family: 'JetBrains Mono', monospace; font-size: 9px; letter-spacing: 1px; transition: all 0.2s; border-radius: 1px; }
        .action-btn:hover { background: rgba(183,110,121,0.12); border-color: ${R}; }
        .action-btn.primary { background: ${R}; color: ${BG}; border-color: ${R}; }
        .action-btn.primary:hover { background: #c9838c; }
        .row-hover { transition: background 0.15s; cursor: pointer; }
        .row-hover:hover { background: rgba(183,110,121,0.02); }
        .battle-live { animation: battlePulse 2s ease-in-out infinite; }
        .crown { animation: crownGlow 3s ease-in-out infinite; }
        .elo-bar { height: 6px; border-radius: 1px; transition: width 1s ease; }
      `}</style>

      {/* ═══ TOP BAR ═══ */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "14px 28px", borderBottom: `1px solid ${BD}`, background: "rgba(14,14,18,0.85)", backdropFilter: "blur(20px)", position: "sticky", top: 0, zIndex: 100 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <span style={{ fontFamily: "'Cinzel', serif", fontSize: 13, letterSpacing: 6, textTransform: "uppercase", color: R }}>DevSkyy</span>
          <div style={{ width: 1, height: 18, background: BD }} />
          <span className="mono" style={{ fontSize: 9, letterSpacing: 2, color: DM }}>LLM ROUNDTABLE</span>
          <div style={{ width: 1, height: 18, background: BD }} />
          <span className="mono" style={{ fontSize: 9, letterSpacing: 1, color: `${TX}44` }}>COMPETE · EVALUATE · ALLOCATE</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <Pulse color={BL} />
            <span className="mono" style={{ fontSize: 9, color: BL }}>{BATTLES.filter(b => b.status === "competing").length} LIVE BATTLES</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span className="mono" style={{ fontSize: 9, color: DM }}>{MODELS.length} MODELS</span>
          </div>
          <span className="mono" style={{ fontSize: 10, color: DM }}>{time.toLocaleTimeString("en-US", { hour12: false })}</span>
          <div style={{ width: 26, height: 26, borderRadius: "50%", background: `linear-gradient(135deg, ${R}, ${GD})`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 10, fontWeight: 700, color: BG }}>CF</div>
        </div>
      </div>

      {/* ═══ TAB NAV ═══ */}
      <div style={{ display: "flex", gap: 2, padding: "12px 28px", borderBottom: `1px solid ${BD}` }}>
        {TABS.map((t, i) => (
          <button key={i} className={`tab-btn ${tab === i ? "active" : ""}`} onClick={() => setTab(i)}>
            <span style={{ fontSize: 12 }}>{t.icon}</span>{t.label}
          </button>
        ))}
      </div>

      <div style={{ padding: "20px 28px", maxWidth: 1440, margin: "0 auto" }}>

        {/* ════════════ LIVE ARENA ════════════ */}
        {tab === 0 && (
          <div style={{ animation: "slideUp 0.4s ease" }}>
            {/* KPI Strip */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 12, marginBottom: 20 }}>
              {[
                { l: "Total Battles", v: "1,847", c: R },
                { l: "Active Now", v: BATTLES.filter(b => b.status === "competing").length, c: BL },
                { l: "Models Competing", v: MODELS.length, c: SV },
                { l: "Avg Battle Time", v: "4.2s", c: GD },
                { l: "Top Elo", v: "1,847", c: GR, sub: "Claude Opus 4.6" },
              ].map((m, i) => (
                <div key={i} className="card" style={{ padding: 14, animation: `slideUp 0.3s ease ${i * 0.04}s both` }}>
                  <div className="lbl" style={{ marginBottom: 3 }}>{m.l}</div>
                  <div className="val" style={{ fontSize: 22, color: m.c }}>{m.v}</div>
                  {m.sub && <div className="mono" style={{ fontSize: 8, color: DM, marginTop: 2 }}>{m.sub}</div>}
                </div>
              ))}
            </div>

            {/* Live Battles */}
            {BATTLES.map((b, bi) => {
              const isExpanded = expandedBattle === b.id;
              const winner = b.winner ? getModel(b.winner) : null;
              return (
                <div key={b.id} className={`card ${b.status === "competing" ? "battle-live" : ""}`} style={{ marginBottom: 12, overflow: "hidden", animation: `slideUp 0.4s ease ${bi * 0.08}s both` }}>
                  {/* Battle Header */}
                  <div className="row-hover" style={{ padding: "14px 20px", display: "flex", justifyContent: "space-between", alignItems: "center" }} onClick={() => setExpandedBattle(isExpanded ? null : b.id)}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                        <span className="mono" style={{ fontSize: 9, color: DM }}>{b.id}</span>
                        <Tag color={cc(b.collection)}>{b.collection === "all" ? "ALL" : b.collection.replace("-", " ").toUpperCase()}</Tag>
                        <Tag color={sc(b.status)}>{b.status.toUpperCase()}</Tag>
                        <span className="mono" style={{ fontSize: 9, color: DM }}>{b.startedAt}</span>
                      </div>
                      <div style={{ fontSize: 13, fontWeight: 500, lineHeight: 1.4 }}>{b.task}</div>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 12, marginLeft: 20 }}>
                      {/* Competitor avatars */}
                      <div style={{ display: "flex", gap: -4 }}>
                        {b.competitors.map((c, ci) => {
                          const m = getModel(c.modelId);
                          return <div key={ci} style={{ width: 24, height: 24, borderRadius: "50%", background: `${m.color}20`, border: `1.5px solid ${c.status === "complete" ? m.color : `${m.color}40`}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 10, marginLeft: ci > 0 ? -6 : 0, zIndex: 4 - ci, position: "relative" }}>
                            <span style={{ color: m.color, fontSize: 9 }}>{m.icon}</span>
                            {b.winner === c.modelId && <span style={{ position: "absolute", top: -8, fontSize: 10 }} className="crown">♛</span>}
                          </div>;
                        })}
                      </div>
                      {winner && <span className="mono" style={{ fontSize: 10, color: winner.color, fontWeight: 600 }}>🏆 {winner.name}</span>}
                      <span className="mono" style={{ fontSize: 10, color: DM }}>{isExpanded ? "▲" : "▼"}</span>
                    </div>
                  </div>

                  {/* Expanded: Race Visualization + Details */}
                  {isExpanded && (
                    <div style={{ borderTop: `1px solid ${BD}` }}>
                      {/* Race Canvas */}
                      <canvas ref={canvasRef} style={{ width: "100%", height: 100, display: "block", borderBottom: `1px solid ${BD}` }} />

                      {/* Competitor Details */}
                      <div style={{ padding: "12px 20px" }}>
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
                          {b.competitors.map((c, ci) => {
                            const m = getModel(c.modelId);
                            const isWinner = b.winner === c.modelId;
                            const tokens = simTokens[`${b.id}-${c.modelId}`] || c.tokens;
                            return (
                              <div key={ci} style={{ padding: 14, background: isWinner ? `${m.color}08` : `${BG}`, border: `1px solid ${isWinner ? m.color + "30" : BD}`, borderRadius: 2, animation: `slideUp 0.3s ease ${ci * 0.05}s both` }}>
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                                    <span style={{ color: m.color, fontSize: 14 }}>{m.icon}</span>
                                    <span style={{ fontWeight: 600, fontSize: 11, color: m.color }}>{m.name}</span>
                                  </div>
                                  {isWinner && <span className="crown" style={{ fontSize: 14 }}>♛</span>}
                                </div>
                                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6, marginBottom: 8 }}>
                                  <div>
                                    <div className="lbl" style={{ fontSize: 7 }}>STATUS</div>
                                    <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                                      <Pulse color={sc(c.status)} size={4} />
                                      <span className="mono" style={{ fontSize: 9, color: sc(c.status) }}>{c.status.toUpperCase()}</span>
                                    </div>
                                  </div>
                                  <div>
                                    <div className="lbl" style={{ fontSize: 7 }}>TOKENS</div>
                                    <span className="mono" style={{ fontSize: 11 }}>{tokens}</span>
                                  </div>
                                  <div>
                                    <div className="lbl" style={{ fontSize: 7 }}>LATENCY</div>
                                    <span className="mono" style={{ fontSize: 11 }}>{c.latency ? `${c.latency}s` : "..."}</span>
                                  </div>
                                  <div>
                                    <div className="lbl" style={{ fontSize: 7 }}>SCORE</div>
                                    <span className="mono" style={{ fontSize: 13, fontWeight: 700, color: c.score >= 90 ? GR : c.score >= 80 ? GD : c.score ? TX : DM }}>{c.score ?? "—"}</span>
                                  </div>
                                </div>
                                {c.output && (
                                  <div style={{ padding: 8, background: `${BG}`, border: `1px solid ${BD}`, fontSize: 10, color: `${TX}88`, lineHeight: 1.6, maxHeight: 80, overflow: "hidden" }}>
                                    {c.output.substring(0, 160)}...
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                        {/* Scoring Criteria */}
                        <div style={{ display: "flex", gap: 8, marginTop: 12, alignItems: "center" }}>
                          <span className="lbl" style={{ margin: 0, flexShrink: 0 }}>JUDGING ON:</span>
                          {b.criteria.map(c => <Tag key={c} color={R}>{c}</Tag>)}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}

            {/* New Battle Button */}
            <div style={{ display: "flex", justifyContent: "center", padding: 20 }}>
              <button className="action-btn primary" style={{ padding: "12px 32px", fontSize: 10, letterSpacing: 2 }}>⚔ LAUNCH NEW BATTLE</button>
            </div>
          </div>
        )}

        {/* ════════════ LEADERBOARD ════════════ */}
        {tab === 1 && (
          <div style={{ animation: "slideUp 0.4s ease" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
              <div>
                <span className="lbl">Elo Leaderboard — All-Time Rankings</span>
                <div style={{ fontSize: 12, color: `${TX}60`, marginTop: 4 }}>{(totalBattles).toLocaleString()} battles completed · {totalTokens.toFixed(0)}M tokens generated</div>
              </div>
              <button className="action-btn">RESET SEASON</button>
            </div>

            {LEADERBOARD.map((entry, i) => {
              const m = getModel(entry.modelId);
              const eloMax = 2000;
              const eloMin = 1500;
              const eloPct = ((entry.elo - eloMin) / (eloMax - eloMin)) * 100;
              const isTop3 = i < 3;
              const medals = ["♛", "♔", "♕"];
              return (
                <div key={entry.modelId} className="card row-hover" style={{ marginBottom: 8, padding: 0, overflow: "hidden", animation: `slideUp 0.3s ease ${i * 0.04}s both` }} onClick={() => setSelectedModel(selectedModel === entry.modelId ? null : entry.modelId)}>
                  <div style={{ display: "flex", alignItems: "stretch" }}>
                    {/* Rank */}
                    <div style={{ width: 56, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", borderRight: `1px solid ${BD}`, background: isTop3 ? `${m.color}06` : "transparent" }}>
                      {isTop3 ? (
                        <span className={i === 0 ? "crown" : ""} style={{ fontSize: 20, color: i === 0 ? GD : i === 1 ? SV : "#CD7F32" }}>{medals[i]}</span>
                      ) : (
                        <span style={{ fontFamily: "'Cinzel', serif", fontSize: 18, color: DM }}>#{i + 1}</span>
                      )}
                    </div>

                    {/* Main Content */}
                    <div style={{ flex: 1, padding: "14px 20px" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                          <span style={{ fontSize: 16, color: m.color }}>{m.icon}</span>
                          <div>
                            <span style={{ fontWeight: 600, fontSize: 14, color: m.color }}>{m.name}</span>
                            <span className="mono" style={{ fontSize: 9, color: DM, marginLeft: 8 }}>{m.provider}</span>
                          </div>
                          <Tag color={m.color}>{m.tier.toUpperCase()}</Tag>
                        </div>
                        <div style={{ textAlign: "right" }}>
                          <div style={{ fontFamily: "'Cinzel', serif", fontSize: 28, fontWeight: 700, color: m.color, lineHeight: 1 }}>{entry.elo}</div>
                          <span className="mono" style={{ fontSize: 8, color: DM }}>ELO</span>
                        </div>
                      </div>

                      {/* Elo Bar */}
                      <div style={{ marginBottom: 10 }}>
                        <div style={{ height: 6, background: BD, borderRadius: 1, overflow: "hidden" }}>
                          <div className="elo-bar" style={{ width: `${eloPct}%`, background: `linear-gradient(90deg, ${m.color}40, ${m.color})` }} />
                        </div>
                      </div>

                      {/* Stats Row */}
                      <div style={{ display: "flex", gap: 24 }}>
                        {[
                          { l: "W-L-D", v: `${entry.wins}-${entry.losses}-${entry.draws}` },
                          { l: "WIN RATE", v: `${entry.winRate}%`, c: entry.winRate > 70 ? GR : entry.winRate > 50 ? GD : DM },
                          { l: "STREAK", v: entry.streak > 0 ? `🔥 ${entry.streak}` : "—", c: entry.streak > 5 ? GR : TX },
                          { l: "AVG SCORE", v: entry.avgScore, c: entry.avgScore > 90 ? GR : entry.avgScore > 80 ? GD : TX },
                          { l: "TOKENS GEN", v: entry.tokensGenerated },
                          { l: "STRONG SUIT", v: entry.strongSuit },
                        ].map((s, j) => (
                          <div key={j} style={{ flex: j === 5 ? 2 : undefined }}>
                            <div className="lbl" style={{ fontSize: 7, marginBottom: 2 }}>{s.l}</div>
                            <span className="mono" style={{ fontSize: j === 5 ? 9 : 11, color: s.c || TX }}>{s.v}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* ════════════ BATTLE HISTORY ════════════ */}
        {tab === 2 && (
          <div style={{ animation: "slideUp 0.4s ease" }}>
            <div className="lbl" style={{ marginBottom: 16 }}>Recent Battles</div>
            <div className="card" style={{ overflow: "hidden" }}>
              {/* Header */}
              <div style={{ display: "grid", gridTemplateColumns: "70px 1fr 100px 120px 60px 120px 60px 60px", gap: 12, padding: "10px 20px", borderBottom: `1px solid ${BD}` }}>
                {["BATTLE", "TASK", "CATEGORY", "WINNER", "SCORE", "RUNNER-UP", "SCORE", "TIME"].map(h => (
                  <span key={h} className="lbl" style={{ fontSize: 7 }}>{h}</span>
                ))}
              </div>
              {HISTORY.map((h, i) => {
                const w = getModel(h.winner);
                const ru = getModel(h.runnerUp);
                return (
                  <div key={h.id} className="row-hover" style={{ display: "grid", gridTemplateColumns: "70px 1fr 100px 120px 60px 120px 60px 60px", gap: 12, padding: "12px 20px", borderBottom: `1px solid ${BD}`, alignItems: "center", animation: `slideUp 0.3s ease ${i * 0.03}s both` }}>
                    <span className="mono" style={{ fontSize: 9, color: DM }}>{h.id}</span>
                    <span style={{ fontSize: 12 }}>{h.task}</span>
                    <Tag color={R}>{h.category}</Tag>
                    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                      <span style={{ color: w.color, fontSize: 11 }}>{w.icon}</span>
                      <span className="mono" style={{ fontSize: 10, color: w.color }}>{w.name.split(" ").slice(-2).join(" ")}</span>
                    </div>
                    <span className="mono" style={{ fontSize: 12, fontWeight: 600, color: GR }}>{h.winnerScore}</span>
                    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                      <span style={{ color: ru.color, fontSize: 11 }}>{ru.icon}</span>
                      <span className="mono" style={{ fontSize: 10, color: DM }}>{ru.name.split(" ").slice(-2).join(" ")}</span>
                    </div>
                    <span className="mono" style={{ fontSize: 11, color: DM }}>{h.runnerScore}</span>
                    <span className="mono" style={{ fontSize: 9, color: DM }}>{h.time}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ════════════ CATEGORY MAP ════════════ */}
        {tab === 3 && (
          <div style={{ animation: "slideUp 0.4s ease" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
              <div>
                <span className="lbl">Category Dominance Map</span>
                <div style={{ fontSize: 12, color: `${TX}60`, marginTop: 4 }}>Which model wins which task type — auto-routing intelligence</div>
              </div>
              <button className="action-btn primary">APPLY TO AGENT ROUTER</button>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
              {CATEGORY_DOMINANCE.map((cat, i) => {
                const m = getModel(cat.leader);
                return (
                  <div key={i} className="card row-hover" style={{ padding: 18, animation: `slideUp 0.3s ease ${i * 0.04}s both` }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
                      <div style={{ fontWeight: 600, fontSize: 13 }}>{cat.category}</div>
                      <span className="mono" style={{ fontSize: 9, color: DM }}>{cat.battles} battles</span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
                      <span style={{ color: m.color, fontSize: 14 }}>{m.icon}</span>
                      <span style={{ fontWeight: 600, fontSize: 12, color: m.color }}>{m.name}</span>
                      <span className="mono" style={{ fontSize: 10, color: GR, marginLeft: "auto" }}>{cat.winRate}%</span>
                    </div>
                    <Bar pct={cat.winRate} color={m.color} h={4} />
                    <div className="mono" style={{ fontSize: 8, color: DM, marginTop: 6 }}>
                      Auto-routed → {m.name} for all "{cat.category}" tasks
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Routing Summary */}
            <div className="card" style={{ padding: 20, marginTop: 16 }}>
              <div className="lbl" style={{ marginBottom: 12 }}>Orchestrator Routing Rules (Auto-Generated from Battle Results)</div>
              <div className="mono" style={{ fontSize: 10, lineHeight: 2.2, color: `${TX}77` }}>
                {CATEGORY_DOMINANCE.map((cat, i) => {
                  const m = getModel(cat.leader);
                  return <div key={i}><span style={{ color: DM }}>IF</span> task.category === <span style={{ color: GD }}>"{cat.category}"</span> <span style={{ color: DM }}>→</span> route_to(<span style={{ color: m.color }}>{m.id}</span>) <span style={{ color: DM }}>// {cat.winRate}% win rate over {cat.battles} battles</span></div>;
                })}
              </div>
            </div>
          </div>
        )}

        {/* ════════════ MODEL PROFILES ════════════ */}
        {tab === 4 && (
          <div style={{ animation: "slideUp 0.4s ease" }}>
            <div className="lbl" style={{ marginBottom: 16 }}>Model Roster — {MODELS.length} Competitors</div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
              {MODELS.map((m, i) => {
                const lb = LEADERBOARD.find(l => l.modelId === m.id);
                return (
                  <div key={m.id} className="card" style={{ padding: 0, overflow: "hidden", animation: `slideUp 0.3s ease ${i * 0.05}s both` }}>
                    {/* Header with gradient */}
                    <div style={{ padding: "16px 20px", background: `linear-gradient(135deg, ${m.color}10, transparent)`, borderBottom: `1px solid ${BD}` }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                          <span style={{ fontSize: 22, color: m.color }}>{m.icon}</span>
                          <div>
                            <div style={{ fontWeight: 700, fontSize: 16, color: m.color }}>{m.name}</div>
                            <span className="mono" style={{ fontSize: 9, color: DM }}>{m.provider}</span>
                          </div>
                        </div>
                        <div style={{ textAlign: "right" }}>
                          <Tag color={m.color}>{m.tier.toUpperCase()}</Tag>
                          {lb && <div style={{ fontFamily: "'Cinzel', serif", fontSize: 24, color: m.color, marginTop: 4 }}>{lb.elo}</div>}
                        </div>
                      </div>
                    </div>

                    {/* Stats Grid */}
                    <div style={{ padding: "14px 20px" }}>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginBottom: 12 }}>
                        {[
                          { l: "CONTEXT", v: m.contextWindow },
                          { l: "COST/1K TOK", v: `$${m.costPer1k}` },
                          { l: "AVG LATENCY", v: `${(m.avgLatency / 1000).toFixed(1)}s` },
                          { l: "WIN RATE", v: lb ? `${lb.winRate}%` : "—", c: lb && lb.winRate > 70 ? GR : lb && lb.winRate > 50 ? GD : DM },
                        ].map((s, j) => (
                          <div key={j}>
                            <div className="lbl" style={{ fontSize: 7, marginBottom: 2 }}>{s.l}</div>
                            <span className="mono" style={{ fontSize: 12, fontWeight: 500, color: s.c || TX }}>{s.v}</span>
                          </div>
                        ))}
                      </div>
                      {lb && (
                        <>
                          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginBottom: 10 }}>
                            <div><div className="lbl" style={{ fontSize: 7, marginBottom: 2 }}>WINS</div><span className="mono" style={{ fontSize: 12, color: GR }}>{lb.wins}</span></div>
                            <div><div className="lbl" style={{ fontSize: 7, marginBottom: 2 }}>LOSSES</div><span className="mono" style={{ fontSize: 12, color: CR }}>{lb.losses}</span></div>
                            <div><div className="lbl" style={{ fontSize: 7, marginBottom: 2 }}>AVG SCORE</div><span className="mono" style={{ fontSize: 12 }}>{lb.avgScore}</span></div>
                            <div><div className="lbl" style={{ fontSize: 7, marginBottom: 2 }}>STREAK</div><span className="mono" style={{ fontSize: 12 }}>{lb.streak > 0 ? `🔥${lb.streak}` : "—"}</span></div>
                          </div>
                          <div className="lbl" style={{ fontSize: 7, marginBottom: 4 }}>STRONG SUIT</div>
                          <div style={{ fontSize: 11, color: `${TX}77`, lineHeight: 1.5 }}>{lb.strongSuit}</div>
                          {/* Category wins */}
                          <div style={{ display: "flex", gap: 4, marginTop: 8, flexWrap: "wrap" }}>
                            {CATEGORY_DOMINANCE.filter(c => c.leader === m.id).map(c => (
                              <Tag key={c.category} color={m.color}>{c.category} ({c.winRate}%)</Tag>
                            ))}
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* ═══ FOOTER ═══ */}
      <div style={{ padding: "14px 28px", borderTop: `1px solid ${BD}`, display: "flex", justifyContent: "space-between", marginTop: 32 }}>
        <span className="mono" style={{ fontSize: 8, color: DM }}>DevSkyy LLM Roundtable v1.0 · SkyyRose LLC · Connected to Agent Dashboard + Creative Studio + 3D Portal</span>
        <span className="mono" style={{ fontSize: 8, color: DM }}>skyyrose.co · Oakland, CA</span>
      </div>
    </div>
  );
}
