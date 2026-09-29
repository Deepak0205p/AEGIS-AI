/**
 * Rehype plugin: restore superscript / subscript / underline in model output.
 *
 * Why this exists
 * ---------------
 * Markdown has no superscript or subscript syntax, and react-markdown v9 drops
 * raw HTML unless a raw-HTML plugin is enabled. So a model writing `πr^2`,
 * `H_2O`, `CO_2` or `<sup>2</sup>` had its notation silently flattened to plain
 * text (or discarded).
 *
 * This plugin handles three cases inside the rendered HAST tree:
 *   1. Caret notation      `r^2`, `10^-3`, `x^{n+1}`  -> <sup>
 *   2. Underscore notation `H_2O`, `CO_2`, `a_{12}`   -> <sub>
 *   3. Raw HTML tags       <sup> <sub> <u> <br>       -> real elements
 *
 * Safety
 * ------
 * Raw HTML is handled through a strict allowlist (sup, sub, u, ins, mark, br,
 * strong, em, code). Anything else - script, img with onerror, iframe, style -
 * is dropped rather than rendered, so a model response cannot inject markup.
 *
 * Code is never touched: text nodes inside <code>, <pre> or <kbd> are skipped,
 * so `calculate_diameter` and `f(x)^2` inside a snippet stay literal.
 */

type HastNode = {
  type: string;
  tagName?: string;
  value?: string;
  children?: HastNode[];
  [key: string]: unknown;
};

/** Tags we are willing to convert from raw HTML into real elements. */
const ALLOWED_RAW_TAGS = new Set([
  'sup', 'sub', 'u', 'ins', 'mark', 'br', 'strong', 'em', 'code', 'b', 'i', 'small',
]);

/** Elements whose text content must be left exactly as written. */
const CODE_LIKE_TAGS = new Set(['code', 'pre', 'kbd', 'samp']);

/**
 * `^2`, `^-3`, `^2.5` - numeric/operator runs only. Parentheses are deliberately
 * excluded so that `(A = πr^2)` does not swallow the closing bracket.
 * Use the brace form `x^{n+1}` when a non-numeric exponent is needed.
 */
const CARET_RE = /\^\{([^}]*)\}|\^([-+]?\d+(?:\.\d+)?)/g;

/** `_2`, `_{12}` - digits only, so snake_case identifiers are never touched. */
const UNDERSCORE_RE = /([A-Za-z0-9)\]])_(?:\{(\d{1,4})\}|(\d{1,3}))/g;

function makeElement(tagName: string, text: string): HastNode {
  return {
    type: 'element',
    tagName,
    properties: {},
    children: [{ type: 'text', value: text }],
  };
}

function toText(value: unknown): string {
  if (typeof value === 'string') return value;
  if (Array.isArray(value)) return value.map(toText).join('');
  return '';
}

/**
 * Splits one text node into plain text plus <sup>/<sub> elements.
 * Returns null when nothing changes.
 */
function transformTextNode(value: string): HastNode[] | null {
  if (!value) return null;
  if (!CARET_RE.test(value) && !UNDERSCORE_RE.test(value)) {
    CARET_RE.lastIndex = 0;
    UNDERSCORE_RE.lastIndex = 0;
    return null;
  }
  CARET_RE.lastIndex = 0;
  UNDERSCORE_RE.lastIndex = 0;

  // Collect every insertion point, then build the replacement sequence.
  type Mark = { start: number; end: number; tag: 'sup' | 'sub'; text: string };
  const marks: Mark[] = [];

  let m: RegExpExecArray | null;
  CARET_RE.lastIndex = 0;
  while ((m = CARET_RE.exec(value)) !== null) {
    const text = (m[1] !== undefined ? m[1] : m[2]) || '';
    marks.push({ start: m.index, end: m.index + m[0].length, tag: 'sup', text });
  }
  UNDERSCORE_RE.lastIndex = 0;
  while ((m = UNDERSCORE_RE.exec(value)) !== null) {
    const text = (m[2] !== undefined ? m[2] : m[3]) || '';
    marks.push({ start: m.index + 1, end: m.index + m[0].length, tag: 'sub', text });
  }

  if (marks.length === 0) return null;
  marks.sort((a, b) => a.start - b.start);

  const out: HastNode[] = [];
  let cursor = 0;
  for (const mark of marks) {
    if (mark.start < cursor) continue; // overlapping match: keep the first
    if (mark.start > cursor) {
      out.push({ type: 'text', value: value.slice(cursor, mark.start) });
    }
    out.push(makeElement(mark.tag, mark.text));
    cursor = mark.end;
  }
  if (cursor < value.length) {
    out.push({ type: 'text', value: value.slice(cursor) });
  }
  return out;
}

/** Converts a standalone allowlisted raw node (kept for direct unit testing). */
function transformRawNode(node: HastNode): HastNode | null {
  const raw = (node.value || '').trim();
  if (!raw) return null;

  const paired = /^<([a-zA-Z][a-zA-Z0-9]*)>([\s\S]*?)<\/\1>$/.exec(raw);
  if (paired) {
    const tag = paired[1].toLowerCase();
    if (!ALLOWED_RAW_TAGS.has(tag)) return null;
    if (tag === 'br') return { type: 'element', tagName: 'br', properties: {}, children: [] };
    return {
      type: 'element',
      tagName: tag,
      properties: {},
      children: [{ type: 'text', value: paired[2] }],
    };
  }

  const open = openTagOf(raw);
  if (open) {
    return { type: 'element', tagName: open.tag, properties: {}, children: [] };
  }

  return null; // anything else is discarded rather than rendered
}

/** True when this raw node is an allowlisted opening/self-closing tag. */
function openTagOf(raw: string): { tag: string; selfClosing: boolean } | null {
  const m = /^<([a-zA-Z][a-zA-Z0-9]*)(\s*\/)?\s*>$/.exec(raw.trim());
  if (!m) return null;
  const tag = m[1].toLowerCase();
  if (!ALLOWED_RAW_TAGS.has(tag)) return null;
  return { tag, selfClosing: Boolean(m[2]) };
}

/** True when this raw node is the matching closing tag. */
function isCloseTagFor(raw: string, tag: string): boolean {
  return new RegExp(`^<\\/${tag}\\s*>$`, 'i').test(raw.trim());
}

function walk(node: HastNode, insideCode: boolean): void {
  if (!node || !Array.isArray(node.children)) return;

  const isCodeLike = insideCode || (node.tagName ? CODE_LIKE_TAGS.has(node.tagName) : false);
  const source = node.children;
  const out: HastNode[] = [];

  for (let i = 0; i < source.length; i += 1) {
    const child = source[i];

    // --- raw HTML: handled tag by tag, because remark splits `<sup>x</sup>`
    //     into three separate raw nodes (`<sup>`, `x`, `</sup>`).
    if (child.type === 'raw') {
      const open = openTagOf(child.value || '');

      if (open && !open.selfClosing) {
        const element: HastNode = {
          type: 'element',
          tagName: open.tag,
          properties: {},
          children: [],
        };
        const inner = element.children as HastNode[];

        // Consume siblings until the matching close tag.
        let depth = 1;
        let j = i + 1;
        while (j < source.length) {
          const sib = source[j];
          if (sib.type === 'raw' && isCloseTagFor(sib.value || '', open.tag)) {
            depth -= 1;
            if (depth === 0) break;
          } else if (sib.type === 'raw' && openTagOf(sib.value || '')?.tag === open.tag) {
            depth += 1;
          }

          if (sib.type === 'raw') {
            const nested = openTagOf(sib.value || '');
            if (!nested) {
              // Unsupported raw markup inside an allowed tag: keep its text only.
              if (sib.value && sib.value.trim()) {
                inner.push({ type: 'text', value: sib.value });
              }
            } else {
              inner.push(sib);
            }
          } else {
            walk(sib, isCodeLike);
            inner.push(sib);
          }
          j += 1;
        }

        out.push(element);
        i = depth === 0 ? j : source.length - 1; // skip what we consumed
        continue;
      }

      if (open && open.selfClosing) {
        out.push({ type: 'element', tagName: open.tag, properties: {}, children: [] });
        continue;
      }

      // A lone closing tag, or any unsupported raw markup: drop it.
      continue;
    }

    if (child.type === 'text' && !isCodeLike) {
      const replacement = transformTextNode(child.value || '');
      if (replacement) {
        out.push(...replacement);
      } else {
        out.push(child);
      }
      continue;
    }

    walk(child, isCodeLike);
    out.push(child);
  }

  node.children = out;
}

/** The rehype plugin itself. */
export default function rehypeSupSub() {
  return (tree: HastNode) => {
    walk(tree, false);
    // A bare <u> element from the plugin needs no extra properties, but keeping
    // the tree shape stable helps React diffing.
    return tree;
  };
}

export { transformTextNode, transformRawNode, toText };
