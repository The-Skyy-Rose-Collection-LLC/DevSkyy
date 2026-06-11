module.exports = [
"[externals]/next/dist/compiled/next-server/app-route-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-route-turbo.runtime.dev.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/next-server/app-route-turbo.runtime.dev.js", () => require("next/dist/compiled/next-server/app-route-turbo.runtime.dev.js"));

module.exports = mod;
}),
"[externals]/next/dist/compiled/next-server/app-page-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-page-turbo.runtime.dev.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js", () => require("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/work-unit-async-storage.external.js [external] (next/dist/server/app-render/work-unit-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/server/app-render/work-unit-async-storage.external.js", () => require("next/dist/server/app-render/work-unit-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/work-async-storage.external.js [external] (next/dist/server/app-render/work-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/server/app-render/work-async-storage.external.js", () => require("next/dist/server/app-render/work-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/shared/lib/no-fallback-error.external.js [external] (next/dist/shared/lib/no-fallback-error.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/shared/lib/no-fallback-error.external.js", () => require("next/dist/shared/lib/no-fallback-error.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/after-task-async-storage.external.js [external] (next/dist/server/app-render/after-task-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/server/app-render/after-task-async-storage.external.js", () => require("next/dist/server/app-render/after-task-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/node:fs [external] (node:fs, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("node:fs", () => require("node:fs"));

module.exports = mod;
}),
"[externals]/node:path [external] (node:path, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("node:path", () => require("node:path"));

module.exports = mod;
}),
"[externals]/fs [external] (fs, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("fs", () => require("fs"));

module.exports = mod;
}),
"[externals]/path [external] (path, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("path", () => require("path"));

module.exports = mod;
}),
"[project]/frontend/lib/autonomy/types.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "AutonomyCockpitDataSchema",
    ()=>AutonomyCockpitDataSchema,
    "BaselineAssetCheckSchema",
    ()=>BaselineAssetCheckSchema,
    "BaselineCanonCheckSchema",
    ()=>BaselineCanonCheckSchema,
    "BaselinePageSchema",
    ()=>BaselinePageSchema,
    "CycleVerdictSchema",
    ()=>CycleVerdictSchema,
    "HealCycleEntrySchema",
    ()=>HealCycleEntrySchema,
    "HealKnowledgeSchema",
    ()=>HealKnowledgeSchema,
    "KnowledgeSignatureSchema",
    ()=>KnowledgeSignatureSchema,
    "RecurrenceTrendSchema",
    ()=>RecurrenceTrendSchema,
    "S1DetailSchema",
    ()=>S1DetailSchema,
    "S1PageDetailSchema",
    ()=>S1PageDetailSchema,
    "S2DetailSchema",
    ()=>S2DetailSchema,
    "S3DetailSchema",
    ()=>S3DetailSchema,
    "S4DetailSchema",
    ()=>S4DetailSchema,
    "SignalStatusSchema",
    ()=>SignalStatusSchema,
    "ThemeHealthBaselineSchema",
    ()=>ThemeHealthBaselineSchema,
    "normalizeVerdict",
    ()=>normalizeVerdict
]);
/**
 * Storefront Autonomy Cockpit — shared types and Zod schemas.
 *
 * No fs imports. Safe to use from client components, server components,
 * and route handlers. All types are inferred from their Zod schemas so
 * the schema IS the single source of truth.
 *
 * Shapes are derived from real heal-log.jsonl observations (2026-05-30):
 *   - Line 1: full DRY cycle with s1/s2/s3/s4 detail; cycle=1 (number)
 *   - Lines 2-3: abbreviated scheduled cycles; cycle="scheduled" (string)
 *     carrying trigger, note, liveVer fields not present in line 1.
 * z.passthrough() is used on HealCycleEntry so extra fields survive
 * round-trips without being stripped.
 */ var __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__ = __turbopack_context__.i("[project]/frontend/node_modules/zod/v4/classic/external.js [app-route] (ecmascript) <export * as z>");
;
const CycleVerdictSchema = __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].enum([
    'healthy',
    'HEALTHY',
    'regressions',
    'REGRESSIONS',
    'escalated',
    'ESCALATED'
]);
const SignalStatusSchema = __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].enum([
    'PASS',
    'FAIL',
    'UNAVAILABLE',
    'skipped'
]);
const S1PageDetailSchema = __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].object({
    http: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].number().int(),
    kb: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].number(),
    floor: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].number(),
    phpErr: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].number().int()
});
const S1DetailSchema = __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].object({
    status: SignalStatusSchema,
    pages: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].record(__TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string(), S1PageDetailSchema)
});
const S2DetailSchema = __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].object({
    status: SignalStatusSchema,
    checks: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].record(__TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string(), __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string())
});
const S3DetailSchema = __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].object({
    status: SignalStatusSchema,
    assetVersion: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string(),
    refs: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].number().int().optional(),
    minCssMain: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].number().int().optional(),
    minCssDesignTokens: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].number().int().optional(),
    minJsPremiumInteractions: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].number().int().optional()
});
const S4DetailSchema = __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].object({
    status: SignalStatusSchema,
    note: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string().optional(),
    available: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].boolean().optional()
}).passthrough();
const HealCycleEntrySchema = __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].object({
    ts: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string(),
    cycle: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].union([
        __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].number(),
        __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string()
    ]),
    signalsChecked: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].array(__TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string()).default([]),
    regressions: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].array(__TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string()).default([]),
    healed: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].array(__TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string()).default([]),
    gate: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string().optional(),
    deployed: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].boolean().default(false),
    verdict: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string(),
    dryManifest: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].unknown().nullable().optional(),
    lessons: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].array(__TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string()).optional(),
    improvements: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].array(__TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string()).optional(),
    note: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string().optional(),
    s1: S1DetailSchema.optional(),
    s2: S2DetailSchema.optional(),
    s3: S3DetailSchema.optional(),
    s4: S4DetailSchema.optional()
}).passthrough();
const KnowledgeSignatureSchema = __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].object({
    signature: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string(),
    surface: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string(),
    rootCause: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string(),
    fixPattern: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string(),
    recurrences: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].number().int(),
    firstSeen: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string(),
    lastSeen: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string(),
    lastOutcome: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].enum([
        'healed',
        'escalated',
        'dry'
    ]),
    preventionAdded: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string().nullable()
});
const RecurrenceTrendSchema = __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].object({
    cycle: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].number().int(),
    meanRecurrences: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].number(),
    signaturesActive: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].number().int()
});
const HealKnowledgeSchema = __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].object({
    version: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].number().int(),
    cycles: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].number().int(),
    note: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string().optional(),
    signatures: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].array(KnowledgeSignatureSchema),
    preventions: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].array(__TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string()),
    metric_recurrence_trend: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].array(RecurrenceTrendSchema)
});
const BaselinePageSchema = __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].object({
    path: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string(),
    expectedHttp: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].number().int(),
    observedKB: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].number(),
    sizeFloorKB: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].number(),
    phpError: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].boolean(),
    label: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string()
});
const BaselineCanonCheckSchema = __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].object({
    id: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string(),
    surface: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string(),
    path: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string(),
    grep: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string(),
    expectedPresent: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].boolean(),
    observedPresent: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].boolean(),
    severity: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string(),
    description: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string()
});
const BaselineAssetCheckSchema = __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].object({
    id: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string(),
    description: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string().optional(),
    expectedVersion: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string().optional(),
    observedVersion: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string().optional(),
    matchesSource: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].boolean().optional(),
    url: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string().optional(),
    expectedHttp: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].number().int().optional(),
    observedHttp: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].number().int().optional()
}).passthrough();
const ThemeHealthBaselineSchema = __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].object({
    version: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].number().int(),
    assetVersion: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string(),
    capturedAt: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string(),
    note: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].string().optional(),
    pages: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].array(BaselinePageSchema),
    canonChecks: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].array(BaselineCanonCheckSchema),
    assetChecks: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].array(BaselineAssetCheckSchema)
});
const AutonomyCockpitDataSchema = __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].object({
    /** Most-recent line from heal-log.jsonl regardless of detail level */ latestCycle: HealCycleEntrySchema.nullable(),
    /** Most-recent line that contains s1/s2/s3 detail keys */ latestWithDetail: HealCycleEntrySchema.nullable(),
    /** All parsed cycle entries, chronological */ allCycles: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].array(HealCycleEntrySchema),
    /** Full heal-knowledge.json payload */ knowledge: HealKnowledgeSchema,
    /** theme-health-baseline.json */ baseline: ThemeHealthBaselineSchema,
    /** true when fs adapter is in use (local host), false when mock (Vercel) */ isLive: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$zod$2f$v4$2f$classic$2f$external$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__$2a$__as__z$3e$__["z"].boolean()
});
function normalizeVerdict(raw) {
    const lower = raw.toLowerCase();
    if (lower === 'healthy') return 'healthy';
    if (lower === 'regressions') return 'regressions';
    return 'escalated';
}
}),
"[project]/frontend/lib/autonomy/mock.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

/**
 * Vercel-safe mock adapter.
 * This is the PRODUCTION read path when .claude/state/ files are unreachable
 * (i.e., every Vercel deployment). Not a test fixture.
 * No fs imports.
 */ __turbopack_context__.s([
    "mockAdapter",
    ()=>mockAdapter
]);
const mockBaseline = {
    version: 1,
    assetVersion: '1.5.25',
    capturedAt: '2026-05-29T00:00:00Z',
    note: 'Captured by baseline-seeding agent.',
    pages: [
        {
            path: '/',
            expectedHttp: 200,
            observedKB: 217.0,
            sizeFloorKB: 184.4,
            phpError: false,
            label: 'Homepage'
        },
        {
            path: '/shop/',
            expectedHttp: 200,
            observedKB: 140.1,
            sizeFloorKB: 119.1,
            phpError: false,
            label: 'Shop'
        },
        {
            path: '/cart/',
            expectedHttp: 200,
            observedKB: 201.0,
            sizeFloorKB: 170.8,
            phpError: false,
            label: 'Cart'
        },
        {
            path: '/pre-order/',
            expectedHttp: 200,
            observedKB: 263.0,
            sizeFloorKB: 223.5,
            phpError: false,
            label: 'Pre-order'
        },
        {
            path: '/about/',
            expectedHttp: 200,
            observedKB: 148.4,
            sizeFloorKB: 126.1,
            phpError: false,
            label: 'About'
        },
        {
            path: '/experience-black-rose/',
            expectedHttp: 200,
            observedKB: 147.4,
            sizeFloorKB: 125.3,
            phpError: false,
            label: 'Experience — Black Rose'
        },
        {
            path: '/experience-love-hurts/',
            expectedHttp: 200,
            observedKB: 143.6,
            sizeFloorKB: 122.1,
            phpError: false,
            label: 'Experience — Love Hurts'
        },
        {
            path: '/experience-signature/',
            expectedHttp: 200,
            observedKB: 149.0,
            sizeFloorKB: 126.6,
            phpError: false,
            label: 'Experience — Signature'
        },
        {
            path: '/experience-kids-capsule/',
            expectedHttp: 200,
            observedKB: 142.2,
            sizeFloorKB: 120.9,
            phpError: false,
            label: 'Experience — Kids Capsule'
        },
        {
            path: '/this-page-does-not-exist-404check/',
            expectedHttp: 404,
            observedKB: 146.1,
            sizeFloorKB: 124.2,
            phpError: false,
            label: '404 sentinel'
        }
    ],
    canonChecks: [
        {
            id: 'home-four-collections',
            surface: 'homepage',
            path: '/',
            grep: 'Four Collections',
            expectedPresent: true,
            observedPresent: true,
            severity: 'high',
            description: "Homepage must mention 'Four Collections'"
        },
        {
            id: 'home-no-three-worlds',
            surface: 'homepage',
            path: '/',
            grep: 'Three Worlds',
            expectedPresent: false,
            observedPresent: false,
            severity: 'high',
            description: "Homepage must NOT contain deprecated 'Three Worlds' copy"
        },
        {
            id: 'home-tagline',
            surface: 'homepage',
            path: '/',
            grep: 'Luxury Grows from Concrete',
            expectedPresent: true,
            observedPresent: true,
            severity: 'critical',
            description: 'Brand tagline must be present on homepage'
        },
        {
            id: 'cart-no-complete-the-look',
            surface: 'cart',
            path: '/cart/',
            grep: 'Complete the Look',
            expectedPresent: false,
            observedPresent: false,
            severity: 'high',
            description: "Cart must NOT contain 'Complete the Look' cross-sell"
        },
        {
            id: 'experience-br-lockup-image',
            surface: 'experience-black-rose',
            path: '/experience-black-rose/',
            grep: 'hero-overlay',
            expectedPresent: true,
            observedPresent: true,
            severity: 'high',
            description: 'Experience pages must use lockup image'
        }
    ],
    assetChecks: [
        {
            id: 'asset-version-on-home',
            description: 'Homepage HTML must reference ?ver=SKYYROSE_VERSION on theme assets',
            expectedVersion: '1.5.25',
            observedVersion: '1.5.25',
            matchesSource: true
        },
        {
            id: 'min-css-main',
            url: 'https://skyyrose.co/wp-content/themes/skyyrose-flagship/assets/css/main.min.css?ver=1.5.25',
            expectedHttp: 200,
            observedHttp: 200
        },
        {
            id: 'min-css-design-tokens',
            url: 'https://skyyrose.co/wp-content/themes/skyyrose-flagship/assets/css/design-tokens.min.css?ver=1.5.25',
            expectedHttp: 200,
            observedHttp: 200
        }
    ]
};
const mockKnowledge = {
    version: 1,
    cycles: 0,
    signatures: [],
    preventions: [],
    metric_recurrence_trend: []
};
const mockCycleWithDetail = {
    ts: '2026-05-30T03:56:37Z',
    cycle: 1,
    signalsChecked: [
        'S1',
        'S2',
        'S3'
    ],
    regressions: [],
    healed: [],
    gate: 'N/A (no regressions)',
    deployed: false,
    verdict: 'HEALTHY',
    lessons: [
        'S1/S2/S3 all clean on first dry cycle.'
    ],
    improvements: [],
    dryManifest: null,
    s1: {
        status: 'PASS',
        pages: {
            Homepage: {
                http: 200,
                kb: 217.0,
                floor: 184.4,
                phpErr: 0
            },
            Shop: {
                http: 200,
                kb: 140.1,
                floor: 119.1,
                phpErr: 0
            },
            Cart: {
                http: 200,
                kb: 201.0,
                floor: 170.8,
                phpErr: 0
            },
            'Pre-order': {
                http: 200,
                kb: 263.0,
                floor: 223.5,
                phpErr: 0
            },
            About: {
                http: 200,
                kb: 148.4,
                floor: 126.1,
                phpErr: 0
            },
            'Exp-BlackRose': {
                http: 200,
                kb: 147.4,
                floor: 125.3,
                phpErr: 0
            },
            'Exp-LoveHurts': {
                http: 200,
                kb: 143.6,
                floor: 122.1,
                phpErr: 0
            },
            'Exp-Signature': {
                http: 200,
                kb: 149.0,
                floor: 126.6,
                phpErr: 0
            },
            'Exp-KidsCapsule': {
                http: 200,
                kb: 142.2,
                floor: 120.9,
                phpErr: 0
            },
            '404-sentinel': {
                http: 404,
                kb: 146.1,
                floor: 124.2,
                phpErr: 0
            }
        }
    },
    s2: {
        status: 'PASS',
        checks: {
            'home-four-collections': 'present',
            'home-no-three-worlds': 'absent',
            'home-tagline': 'present(4)',
            'cart-no-complete-the-look': 'absent',
            'experience-br-lockup-image': 'present(3)'
        }
    },
    s3: {
        status: 'PASS',
        assetVersion: '1.5.25',
        refs: 45,
        minCssMain: 200,
        minCssDesignTokens: 200,
        minJsPremiumInteractions: 200
    }
};
const mockCycle2 = {
    ts: '2026-05-30T07:44:53Z',
    cycle: 'scheduled',
    signalsChecked: [
        'S1',
        'S2',
        'S3'
    ],
    regressions: [],
    healed: [],
    gate: 'n/a',
    deployed: false,
    verdict: 'healthy',
    note: 'live=1.5.25 matches baseline; source=1.5.26 undeployed'
};
const mockCycle3 = {
    ts: '2026-05-30T13:44:13Z',
    cycle: 'scheduled',
    signalsChecked: [
        'S1',
        'S2',
        'S3'
    ],
    regressions: [],
    healed: [],
    gate: 'n/a',
    deployed: false,
    verdict: 'healthy'
};
const allCycles = [
    mockCycle3,
    mockCycle2,
    mockCycleWithDetail
];
const mockAdapter = {
    async cockpit () {
        return {
            latestCycle: mockCycle3,
            latestWithDetail: mockCycleWithDetail,
            allCycles,
            knowledge: mockKnowledge,
            baseline: mockBaseline,
            isLive: false
        };
    }
};
}),
"[project]/frontend/lib/autonomy/file.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "fsAdapter",
    ()=>fsAdapter
]);
/**
 * Server-only fs adapter. Reads heal-log.jsonl, heal-knowledge.json,
 * and theme-health-baseline.json from the repo root (one level above
 * frontend/ since process.cwd() is frontend/ at build time).
 *
 * Falls back to mock-adapter output when files are missing (ENOENT)
 * rather than throwing — so Vercel builds stay green.
 */ var __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$server$2d$only$2f$empty$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/frontend/node_modules/next/dist/compiled/server-only/empty.js [app-route] (ecmascript)");
var __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/fs [external] (fs, cjs)");
var __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/path [external] (path, cjs)");
var __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$autonomy$2f$types$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/frontend/lib/autonomy/types.ts [app-route] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$autonomy$2f$mock$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/frontend/lib/autonomy/mock.ts [app-route] (ecmascript)");
;
;
;
;
;
function repoRoot() {
    // process.cwd() = frontend/ when running `next dev` / `next build`
    // Go one level up to reach the repo root where .claude/ and tasks/ live.
    return __TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(process.cwd(), '..');
}
function readJsonFile(filePath) {
    try {
        const raw = __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["default"].readFileSync(filePath, 'utf8');
        return JSON.parse(raw);
    } catch  {
        return null;
    }
}
function parseHealLog(filePath) {
    try {
        const raw = __TURBOPACK__imported__module__$5b$externals$5d2f$fs__$5b$external$5d$__$28$fs$2c$__cjs$29$__["default"].readFileSync(filePath, 'utf8');
        const lines = raw.split('\n').filter((l)=>l.trim().length > 0);
        const entries = [];
        for (const line of lines){
            try {
                const parsed = JSON.parse(line);
                const result = __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$autonomy$2f$types$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["HealCycleEntrySchema"].safeParse(parsed);
                if (result.success) {
                    entries.push(result.data);
                }
            } catch  {
            // skip malformed lines silently
            }
        }
        return entries;
    } catch  {
        return [];
    }
}
function hasSignalDetail(entry) {
    return entry.s1 !== undefined || entry.s2 !== undefined || entry.s3 !== undefined;
}
const fsAdapter = {
    async cockpit () {
        const root = repoRoot();
        const knowledgeRaw = readJsonFile(__TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(root, '.claude/state/heal-knowledge.json'));
        const baselineRaw = readJsonFile(__TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(root, '.claude/state/theme-health-baseline.json'));
        const allCyclesAsc = parseHealLog(__TURBOPACK__imported__module__$5b$externals$5d2f$path__$5b$external$5d$__$28$path$2c$__cjs$29$__["default"].join(root, 'tasks/heal-log.jsonl'));
        // If essential files are missing, fall back to mock
        if (!knowledgeRaw || !baselineRaw) {
            return __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$autonomy$2f$mock$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["mockAdapter"].cockpit();
        }
        const knowledgeResult = __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$autonomy$2f$types$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["HealKnowledgeSchema"].safeParse(knowledgeRaw);
        const baselineResult = __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$autonomy$2f$types$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["ThemeHealthBaselineSchema"].safeParse(baselineRaw);
        if (!knowledgeResult.success || !baselineResult.success) {
            return __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$autonomy$2f$mock$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["mockAdapter"].cockpit();
        }
        // Reverse-chron for UI (newest first)
        const allCycles = [
            ...allCyclesAsc
        ].reverse();
        const latestCycle = allCycles[0] ?? null;
        const latestWithDetail = allCycles.find(hasSignalDetail) ?? null;
        return {
            latestCycle,
            latestWithDetail,
            allCycles,
            knowledge: knowledgeResult.data,
            baseline: baselineResult.data,
            isLive: true
        };
    }
};
}),
"[project]/frontend/lib/autonomy/index.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "autonomyAdapter",
    ()=>autonomyAdapter
]);
/**
 * Storefront Autonomy — adapter selector (server-only).
 *
 * Checks at module init whether the fs data files are reachable.
 * Exports autonomyAdapter pointing to whichever adapter is live.
 *
 * On Vercel (rootDirectory=frontend), .claude/state/ lives above
 * frontend/ and is outside Vercel's upload boundary. accessSync
 * fails → mockAdapter is selected → cockpit shows realistic mock data.
 *
 * Locally, when running `npm run dev` from frontend/, process.cwd()
 * is frontend/. The repo root is ../. accessSync succeeds → fsAdapter
 * reads real heal-log.jsonl, heal-knowledge.json, baseline.json.
 *
 * This is the ONLY file that app/api/autonomy/route.ts imports.
 */ var __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$server$2d$only$2f$empty$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/frontend/node_modules/next/dist/compiled/server-only/empty.js [app-route] (ecmascript)");
var __TURBOPACK__imported__module__$5b$externals$5d2f$node$3a$fs__$5b$external$5d$__$28$node$3a$fs$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/node:fs [external] (node:fs, cjs)");
var __TURBOPACK__imported__module__$5b$externals$5d2f$node$3a$path__$5b$external$5d$__$28$node$3a$path$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/node:path [external] (node:path, cjs)");
var __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$autonomy$2f$file$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/frontend/lib/autonomy/file.ts [app-route] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$autonomy$2f$mock$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/frontend/lib/autonomy/mock.ts [app-route] (ecmascript)");
;
;
;
;
;
const knowledgePath = __TURBOPACK__imported__module__$5b$externals$5d2f$node$3a$path__$5b$external$5d$__$28$node$3a$path$2c$__cjs$29$__["default"].join(process.cwd(), '..', '.claude', 'state', 'heal-knowledge.json');
const canUseFs = (()=>{
    try {
        __TURBOPACK__imported__module__$5b$externals$5d2f$node$3a$fs__$5b$external$5d$__$28$node$3a$fs$2c$__cjs$29$__["default"].accessSync(knowledgePath, __TURBOPACK__imported__module__$5b$externals$5d2f$node$3a$fs__$5b$external$5d$__$28$node$3a$fs$2c$__cjs$29$__["default"].constants.R_OK);
        return true;
    } catch  {
        return false;
    }
})();
const autonomyAdapter = canUseFs ? __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$autonomy$2f$file$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["fsAdapter"] : __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$autonomy$2f$mock$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["mockAdapter"];
}),
"[project]/frontend/app/api/autonomy/route.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "GET",
    ()=>GET
]);
/**
 * GET /api/autonomy
 * Returns AutonomyCockpitData from whichever adapter is available.
 * Pattern matches app/api/monitoring/health/route.ts exactly.
 * Note: cacheComponents mode prohibits export const dynamic — route handlers
 * in this mode are already dynamic per request. No override needed.
 */ var __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/frontend/node_modules/next/server.js [app-route] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$autonomy$2f$index$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/frontend/lib/autonomy/index.ts [app-route] (ecmascript)");
;
;
async function GET() {
    try {
        const data = await __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$autonomy$2f$index$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["autonomyAdapter"].cockpit();
        return __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json(data, {
            status: 200
        });
    } catch (error) {
        return __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
            error: 'Failed to load autonomy cockpit data',
            message: error instanceof Error ? error.message : 'Unknown error'
        }, {
            status: 503
        });
    }
}
}),
];

//# sourceMappingURL=%5Broot-of-the-server%5D__07be7928._.js.map