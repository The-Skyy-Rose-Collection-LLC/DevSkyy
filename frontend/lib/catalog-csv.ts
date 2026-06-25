/**
 * Pure CSV transforms for the canonical SkyyRose catalog.
 *
 * This module is intentionally DEPENDENCY-FREE: no `node:fs`, no `server-only`,
 * no `@/` aliases. That keeps it unit-testable in isolation (a bare `tsx`
 * script can import it) and reusable from both the read path (`catalog.ts`) and
 * the write path (`catalog-write.ts`) — one CSV-parsing authority, not two.
 *
 * Write strategy: SINGLE-LINE SPLICE. `applyPatch` re-serializes only the one
 * row whose SKU matches and leaves every other line byte-for-byte unchanged.
 * This preserves all 24 columns — including the 8 `render_*` pipeline columns
 * that the typed `CatalogProduct` view drops — and produces minimal diffs.
 */

/** Columns an editor is allowed to write. Everything else (sku, collection,
 *  garment_type_lock, dossier_slug, and the SOT-governed image columns) is
 *  read-only and preserved verbatim. */
export const EDITABLE_COLUMNS = [
  'name',
  'price',
  'badge',
  'sizes',
  'color',
  'edition_size',
  'published',
  'is_preorder',
  'description',
] as const;

export type EditableColumn = (typeof EDITABLE_COLUMNS)[number];

/** A patch maps editable column names to their raw CSV cell string. */
export type CatalogPatch = Partial<Record<EditableColumn, string>>;

const EDITABLE_SET: ReadonlySet<string> = new Set(EDITABLE_COLUMNS);

/** Split one CSV line into cells, honoring quotes and escaped (`""`) quotes. */
export function splitCsvRow(line: string): string[] {
  const out: string[] = [];
  let cur = '';
  let inQuotes = false;
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i];
    if (ch === '"') {
      if (inQuotes && line[i + 1] === '"') {
        cur += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (ch === ',' && !inQuotes) {
      out.push(cur);
      cur = '';
    } else {
      cur += ch;
    }
  }
  out.push(cur);
  return out;
}

/** Quote a cell only when it contains a comma, quote, or newline. */
export function escapeCsvCell(value: string): string {
  if (/[",\r\n]/.test(value)) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}

export function serializeCsvRow(cells: string[]): string {
  return cells.map(escapeCsvCell).join(',');
}

/**
 * Collapse CR/LF runs to a single space so a value stays on one CSV line.
 * The catalog is single-line-per-row by invariant (`catalog.ts` parses with a
 * naive line split); callers normalize free-text values through this before
 * writing so a pasted paragraph break can't corrupt the file.
 */
export function collapseNewlines(value: string): string {
  return value.replace(/\r\n|\r|\n/g, ' ');
}

export interface ApplyPatchResult {
  /** The full CSV text after the splice (unchanged input if nothing changed). */
  text: string;
  /** True only if the target row's serialized form actually differs. */
  changed: boolean;
  /** The target row's cells, keyed by column name, BEFORE the patch. */
  before: Record<string, string>;
  /** The target row's cells, keyed by column name, AFTER the patch. */
  after: Record<string, string>;
}

/**
 * Apply `patch` to the row whose first column (`sku`) equals `sku`, returning
 * new CSV text with only that one line re-serialized.
 *
 * Throws on: unknown/non-editable patch key, missing `sku` column, SKU not
 * found, malformed row (cell count != header count), or a CSV with embedded
 * newlines (line-splice would be unsafe — caller should regenerate instead).
 */
export function applyPatch(
  csvText: string,
  sku: string,
  patch: CatalogPatch
): ApplyPatchResult {
  const usesCRLF = csvText.includes('\r\n');
  const NL = usesCRLF ? '\r\n' : '\n';
  const endsWithNL = csvText.endsWith('\n');
  const body = endsWithNL ? csvText.slice(0, -NL.length) : csvText;
  const lines = body.split(NL);

  if (lines.length < 2) {
    throw new Error('CSV has no data rows');
  }

  const headers = splitCsvRow(lines[0]).map((h) => h.trim());
  if (headers[0] !== 'sku') {
    throw new Error("Expected 'sku' as the first CSV column");
  }

  for (const key of Object.keys(patch)) {
    if (!EDITABLE_SET.has(key)) {
      throw new Error(`Column not editable: ${key}`);
    }
    if (!headers.includes(key)) {
      throw new Error(`Column missing from CSV header: ${key}`);
    }
    // The whole pipeline (catalog.ts `parseCsv` splits on /\r?\n/) assumes one
    // physical line per record. A newline inside a value would split the row
    // and corrupt the catalog, so reject it here — safe by construction. The
    // API layer collapses newlines (see `collapseNewlines`) before reaching us.
    const value = patch[key as EditableColumn];
    if (value !== undefined && /[\r\n]/.test(value)) {
      throw new Error(`Patch value for "${key}" contains a newline; catalog cells must be single-line`);
    }
  }

  // Embedded-newline guard: a quoted cell containing a newline would make
  // line-based splicing corrupt the file. Detect by re-parsing and comparing
  // the data-row count to the number of body lines.
  const parsedRowCount = parseDataRows(csvText).length;
  if (parsedRowCount !== lines.length - 1) {
    throw new Error(
      'CSV contains embedded newlines — line-splice is unsafe; regenerate the file instead'
    );
  }

  let targetLine = -1;
  for (let i = 1; i < lines.length; i += 1) {
    const first = splitCsvRow(lines[i])[0]?.trim();
    if (first === sku) {
      targetLine = i;
      break;
    }
  }
  if (targetLine === -1) {
    throw new Error(`SKU not found: ${sku}`);
  }

  const cells = splitCsvRow(lines[targetLine]);
  if (cells.length !== headers.length) {
    throw new Error(
      `Row ${sku} has ${cells.length} cells, expected ${headers.length}`
    );
  }

  const before: Record<string, string> = {};
  headers.forEach((h, idx) => {
    before[h] = cells[idx] ?? '';
  });

  const newCells = [...cells];
  for (const [key, value] of Object.entries(patch)) {
    const idx = headers.indexOf(key);
    newCells[idx] = value ?? '';
  }

  const after: Record<string, string> = {};
  headers.forEach((h, idx) => {
    after[h] = newCells[idx] ?? '';
  });

  const newLine = serializeCsvRow(newCells);
  if (newLine === lines[targetLine]) {
    return { text: csvText, changed: false, before, after };
  }

  const newLines = [...lines];
  newLines[targetLine] = newLine;
  const text = newLines.join(NL) + (endsWithNL ? NL : '');
  return { text, changed: true, before, after };
}

/** Parse all data rows (cell arrays) — used by the embedded-newline guard and
 *  available for tests. Header row excluded; fully blank rows skipped. */
export function parseDataRows(csvText: string): string[][] {
  const rows: string[][] = [];
  let field = '';
  let cells: string[] = [];
  let inQuotes = false;
  let started = false;

  const pushField = () => {
    cells.push(field);
    field = '';
  };
  const pushRow = () => {
    pushField();
    if (!(cells.length === 1 && cells[0] === '')) {
      rows.push(cells);
    }
    cells = [];
    started = false;
  };

  for (let i = 0; i < csvText.length; i += 1) {
    const ch = csvText[i];
    if (inQuotes) {
      if (ch === '"') {
        if (csvText[i + 1] === '"') {
          field += '"';
          i += 1;
        } else {
          inQuotes = false;
        }
      } else {
        field += ch;
      }
      continue;
    }
    if (ch === '"') {
      inQuotes = true;
      started = true;
    } else if (ch === ',') {
      pushField();
      started = true;
    } else if (ch === '\n') {
      pushRow();
    } else if (ch === '\r') {
      // swallow — handled by the following \n
    } else {
      field += ch;
      started = true;
    }
  }
  if (started || field !== '' || cells.length > 0) {
    pushRow();
  }

  // Drop the header row.
  return rows.slice(1);
}
