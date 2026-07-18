export const meta = {
  name: "adversarial-planning",
  description:
    "Two different models debate a plan before build: Claude (Fable) drafts, Codex challenges (≤3 rounds), Codex executes the converged plan, the planner reviews the real diff.",
  whenToUse:
    "Plans expensive to get wrong: new rigs/animation pipelines, migrations, architecture decisions. Not for small obviously-correct changes.",
  phases: [{ title: "Debate" }, { title: "Execute" }, { title: "Review" }],
};

// ── args ────────────────────────────────────────────────────────────────────
// { task: string (required),
//   codexModel?: string  (default 'gpt-5.6-sol' — pass the string you CONFIRMED
//                         via the pre-flight test call; never a guessed one),
//   plannerModel?: string (default 'fable'),
//   maxRounds?: number    (default 3) }
if (!args || !args.task) {
  throw new Error(
    "adversarial-planning: args.task (the plan to debate) is required",
  );
}
const TASK = args.task;
const CODEX_MODEL = args.codexModel || "gpt-5.6-sol"; // re-verified live 2026-07-12; still runtime-verify
// Hardening: CODEX_MODEL is interpolated into the `codex exec -m ...` shell command the
// relay subagent runs. args is trusted, but reject anything outside a model-string charset
// so a stray paste/typo can't break — or inject into — that command.
if (!/^[A-Za-z0-9._-]+$/.test(CODEX_MODEL)) {
  throw new Error(
    `adversarial-planning: refusing unsafe codexModel ${JSON.stringify(CODEX_MODEL)} — must match [A-Za-z0-9._-]`,
  );
}
const PLANNER_MODEL = args.plannerModel || "fable";
const MAX_ROUNDS = args.maxRounds || 3;

// ── schemas: force structure so revisions have something concrete to diff ─────
const PLAN_SCHEMA = {
  type: "object",
  required: ["summary", "steps", "risks"],
  additionalProperties: false,
  properties: {
    summary: { type: "string" },
    steps: {
      type: "array",
      items: {
        type: "object",
        required: ["action", "files", "verify"],
        additionalProperties: false,
        properties: {
          action: { type: "string" },
          files: { type: "array", items: { type: "string" } },
          verify: {
            type: "string",
            description: "how THIS step is proven done — a check that can fail",
          },
        },
      },
    },
    risks: { type: "array", items: { type: "string" } },
    open_questions: { type: "array", items: { type: "string" } },
  },
};

// The challenge relay: a Claude subagent shells out to `codex exec` and returns
// Codex's RAW words (codex_verbatim) plus a machine-usable verdict derived from
// them. This is what fixes the old `challengeTurn.satisfied` bug — the loop needs
// a boolean, but the verbatim is preserved so nothing Codex said is laundered.
const CHALLENGE_SCHEMA = {
  type: "object",
  required: ["codex_verbatim", "satisfied", "specific_challenge"],
  additionalProperties: false,
  properties: {
    codex_verbatim: {
      type: "string",
      description: "Codex's final message, unedited",
    },
    satisfied: {
      type: "boolean",
      description:
        "true ONLY if Codex judged the plan executable as written. Read from Codex, not your own opinion.",
    },
    specific_challenge: {
      type: "string",
      description:
        'the single most important thing Codex said would change its mind; "" when satisfied',
    },
  },
};

const REVIEW_SCHEMA = {
  type: "object",
  required: ["ship", "deviations", "summary"],
  additionalProperties: false,
  properties: {
    ship: { type: "boolean" },
    deviations: {
      type: "array",
      items: { type: "string" },
      description: "where the executed diff departed from the plan",
    },
    summary: { type: "string" },
  },
};

// A challenge/execution turn: instruct a subagent to drive `codex exec` via Bash.
// Prompt is written to a file and piped over stdin (never interpolated into the
// shell command) so plan JSON with quotes can't break the call.
function codexTurn(round, phase, sandbox, instruction, planObj, schema) {
  // Prompt + output live in a per-run mktemp dir (created by the relay subagent),
  // piped over stdin so plan JSON with quotes can't break the shell command, and
  // uniquely named so concurrent runs of this workflow never collide on /tmp.
  const diffStep =
    sandbox === "workspace-write"
      ? `   Also run \`git diff --stat\` afterward and append its output to codex_verbatim under a "--- git diff --stat ---" header, so the reviewer sees the real diff.\n`
      : "";
  const relay =
    `You are a relay to a DIFFERENT model (Codex). Do exactly this, do not add your own judgment:\n` +
    `1. Run the following as ONE Bash command so the same temp dir ("$d") is used throughout — a fresh dir per run, never a fixed /tmp path:\n` +
    `   d="$(mktemp -d)"\n` +
    `   cat > "$d/prompt.txt" <<'CODEX_PROMPT'\n${instruction}\n\nPLAN (JSON):\n${JSON.stringify(planObj, null, 2)}\nCODEX_PROMPT\n` +
    `   codex exec -m ${CODEX_MODEL} -s ${sandbox} --json -o "$d/out.json" < "$d/prompt.txt"\n` +
    `   cat "$d/out.json"\n` +
    `2. The printed "$d/out.json" content is Codex's final message.\n` +
    diffStep +
    `3. Return the structured fields: put Codex's raw final message verbatim in codex_verbatim ` +
    `and read satisfied / specific_challenge from what CODEX actually said — not your opinion.\n` +
    `If codex errors on the model string or reachability, put the exact error in codex_verbatim, ` +
    `set satisfied=false, and put the error in specific_challenge.`;
  return agent(relay, {
    label: `${phase}-r${round}`,
    phase: phase === "challenge" ? "Debate" : "Execute",
    schema,
  });
}

// ── the loop ─────────────────────────────────────────────────────────────────
phase("Debate");
let plan = null;
const transcript = [];
let round = 1;
for (; round <= MAX_ROUNDS; round++) {
  const finalRound = round === MAX_ROUNDS;
  const plannerPrompt = !plan
    ? `Draft the initial plan for this task. Real steps, files touched, a per-step verification that can FAIL, and known risks — not vibes.\n\nTASK:\n${TASK}`
    : finalRound
      ? `Final round — no more hedging. Lock in your single best plan now, folding in what survived the debate.\nCurrent plan: ${JSON.stringify(plan)}\nLast challenge: ${JSON.stringify(transcript.at(-1).challenge.specific_challenge)}`
      : `Revise ONLY against this specific challenge (not a full rewrite):\n${JSON.stringify(transcript.at(-1).challenge.specific_challenge)}\nCurrent plan: ${JSON.stringify(plan)}`;

  plan = await agent(plannerPrompt, {
    label: `plan-r${round}`,
    phase: "Debate",
    model: PLANNER_MODEL,
    schema: PLAN_SCHEMA,
  });

  const challenge = await codexTurn(
    round,
    "challenge",
    "read-only",
    finalRound
      ? "No more argument. State plainly whether this plan is executable as written, and set satisfied accordingly."
      : "Challenge this plan skeptically. Name specifically what would change your mind — a missing edge case, an untested assumption, or a step whose verification cannot actually be run as described.",
    plan,
    CHALLENGE_SCHEMA,
  );

  transcript.push({ round, plan, challenge });
  if (challenge && challenge.satisfied) {
    log(`Converged at round ${round} — Codex satisfied.`);
    break;
  }
}

// ── execute the converged plan (Codex, workspace-write = real file edits) ─────
phase("Execute");
const execution = await codexTurn(
  round <= MAX_ROUNDS ? round : MAX_ROUNDS,
  "execute",
  "workspace-write",
  "Execute this plan exactly. After finishing, the caller will diff the repo — do only what the plan says.",
  plan,
  CHALLENGE_SCHEMA, // reuse: codex_verbatim = Codex's execution log; satisfied = did it complete
);

// ── planner reviews the REAL result against the plan, not the abstract ────────
phase("Review");
const review = await agent(
  `Review the ACTUAL executed result against the original plan — not the plan in the abstract. ` +
    `Did it do what was planned? What deviated? Ship or not?\n` +
    `PLAN: ${JSON.stringify(plan)}\n` +
    `EXECUTION (Codex verbatim log): ${JSON.stringify(execution.codex_verbatim)}`,
  {
    label: "final-review",
    phase: "Review",
    model: PLANNER_MODEL,
    schema: REVIEW_SCHEMA,
  },
);

return {
  rounds: transcript.length,
  converged: transcript.at(-1)?.challenge?.satisfied === true,
  plan,
  transcript,
  execution,
  review,
};
