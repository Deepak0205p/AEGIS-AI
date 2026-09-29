/**
 * Prisma schema drift verification.
 *
 * The authoritative schema for this project is created by
 * `backend/db.py::_init_schema` (Python + psycopg). Prisma cannot replace it:
 * the FastAPI backend is the only component on the request hot path, and Prisma
 * is a Node/TypeScript ORM.
 *
 * So the risk is that the checked-in `prisma/schema.prisma` and the live
 * PostgreSQL schema drift apart. This script detects that instead of assuming
 * it away. It introspects the live database with `prisma db pull --print` and
 * diffs the result against the committed schema.
 *
 *   node scripts/prisma-verify.mjs          # verify (exit 1 on drift)
 *   node scripts/prisma-verify.mjs --print  # show the live schema
 *
 * Requires DATABASE_URL and a reachable PostgreSQL instance.
 */
import { execFileSync } from 'node:child_process';
import { readFileSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';

const ROOT = resolve(import.meta.dirname, '..');
const SCHEMA = join(ROOT, 'prisma', 'schema.prisma');

/**
 * Loads repo-root `.env` into process.env without overriding real values.
 *
 * Prisma reads `DATABASE_URL` from the process environment only, so without
 * this every command would need the variable exported by hand.
 */
function loadDotEnv() {
  const p = join(ROOT, '.env');
  if (!existsSync(p)) return;
  for (const raw of readFileSync(p, 'utf8').split('\n')) {
    const line = raw.trim();
    if (!line || line.startsWith('#') || !line.includes('=')) continue;
    const i = line.indexOf('=');
    const k = line.slice(0, i).trim();
    let v = line.slice(i + 1).trim();
    if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) {
      v = v.slice(1, -1);
    }
    if (k && process.env[k] === undefined) process.env[k] = v;
  }
}
loadDotEnv();

if (!process.env.DATABASE_URL) {
  console.error(
    'DATABASE_URL is not set and was not found in the repo-root .env.\n' +
    '  Run:  python scripts\\setup_postgres_windows.py    (or: docker compose up -d)\n' +
    '  which writes DATABASE_URL into .env for you.'
  );
  process.exit(2);
}

if (!existsSync(SCHEMA)) {
  console.error(`Schema not found: ${SCHEMA}`);
  process.exit(2);
}

const printOnly = process.argv.includes('--print');

/**
 * Runs the Prisma CLI.
 *
 * `execFileSync('npx.cmd', ...)` fails on Windows with `EINVAL` because
 * Node cannot spawn a `.cmd` shim without a shell, and `shell: true` would
 * re-introduce argument-quoting problems with the schema path. Invoking
 * Prisma's JS entry with the current Node binary avoids both problems.
 */
function runPrisma(args) {
  const entry = join(ROOT, 'node_modules', 'prisma', 'build', 'index.js');
  if (!existsSync(entry)) {
    console.error('Prisma CLI not found. Run:  npm install');
    process.exit(2);
  }
  return execFileSync(process.execPath, [entry, ...args], {
    cwd: ROOT,
    encoding: 'utf8',
    maxBuffer: 32 * 1024 * 1024,
    stdio: ['ignore', 'pipe', 'pipe'],
  });
}

function pullLiveSchema() {
  const stdout = runPrisma(['db', 'pull', '--print', '--schema', SCHEMA]);
  if (!stdout || !stdout.includes('model ')) {
    console.error('prisma db pull produced no schema output.');
    process.exit(2);
  }
  return stdout;
}

/**
 * Removes a redundant `map:` from a `@@unique([...], map: "name")` line.
 *
 * Done with string slicing rather than a regex: the pattern contains nested
 * bracket/paren groups that are easy to get subtly wrong, and this form has
 * nothing to misparse. Note the column list is terminated by `]` followed by
 * `,` (not `])`), so the closing bracket is located on its own.
 */
function stripUniqueMap(line) {
  const prefix = '@@unique([';
  if (!line.startsWith(prefix)) return line;
  const listStart = prefix.length;
  const listEnd = line.indexOf(']', listStart);
  if (listEnd === -1) return line;
  const cols = line.slice(listStart, listEnd);
  const rest = line.slice(listEnd + 1).trim();   // ', map: "x")' or ''
  if (!rest.startsWith(',')) return line;        // no map: to strip
  if (!rest.includes('map:')) return line;       // some other option; leave alone
  return `@@unique([${cols}])`;
}

/**
 * Reduces a Prisma schema to its PHYSICAL structure for comparison.
 *
 * Two classes of line are excluded because they have no database counterpart:
 *
 *   1. Relation declarations (`members ChannelMember[]`, `channel ChatChannel
 *      @relation(...)`). These are client-side convenience only. The Python
 *      schema in `backend/db.py` creates NO foreign keys - referential
 *      integrity is handled in application code - so `prisma db pull` can never
 *      rediscover them and would otherwise report permanent false drift.
 *   2. Explicit `map:` names on `@@unique`, where the mapped name is simply
 *      Prisma's own default for that table+columns.
 *
 * What IS compared: models, field names, types, `@id`/`@unique`, nullability,
 * `@default`, `@db.*` native types, and `@@index` / `@@unique` / `@@map`.
 */
function normalise(src) {
  return src
    .split('\n')
    // Trim BEFORE stripping comments. In JavaScript regex, `.` does not match
    // `\r` (it is a line terminator), so `/\/\/.*$/` fails to match when the
    // file uses CRLF endings - which is the default for git on Windows. That
    // silently turned every comment line into a phantom schema difference.
    .map((l) => l.trim())
    .map((l) => l.replace(/\/\/.*$/, '').trim())
    .filter((l) => l.length > 0)
    // Drop relation fields and @relation(...) lines.
    .filter((l) => !l.includes('@relation'))
    .filter((l) => !/^\w+\s+\w+\[\]$/.test(l))
    .map((l) => l.replace(/\s*@db\.Text\b/g, ''))
    .map((l) => stripUniqueMap(l))
    .map((l) => l.replace(/\s+/g, ' ').trim())
    .filter((l) => l.length > 0)
    .join('\n');
}

const live = pullLiveSchema();

if (printOnly) {
  console.log(live);
  process.exit(0);
}

const committed = readFileSync(SCHEMA, 'utf8');

// Prisma appends an enrichment report to `db pull --print`; drop it.
const liveClean = live.split('// *** WARNING ***')[0];

const a = normalise(committed);
const b = normalise(liveClean);
const aLines = new Set(a.split('\n'));
const bLines = new Set(b.split('\n'));

const onlyInCommitted = [...aLines].filter((l) => !bLines.has(l));
const onlyInLive = [...bLines].filter((l) => !aLines.has(l));

console.log('AEGIS AI  |  Prisma <-> live PostgreSQL schema verification');
console.log('-'.repeat(66));
console.log('Compares physical structure: models, fields, types, nullability,');
console.log('defaults, @id / @unique, native types, @@index, @@unique, @@map.');
console.log('Prisma relation declarations are excluded (no FKs exist in the DB).');
console.log('');

if (onlyInCommitted.length === 0 && onlyInLive.length === 0) {
  console.log('MATCH: prisma/schema.prisma agrees with the live database.');
  process.exit(0);
}

console.log(`DRIFT DETECTED (${onlyInCommitted.length} in schema.prisma, ${onlyInLive.length} in the database)\n`);

if (onlyInCommitted.length) {
  console.log('In prisma/schema.prisma but not in the database:');
  for (const l of onlyInCommitted.slice(0, 30)) console.log(`  - ${l}`);
  console.log('');
}
if (onlyInLive.length) {
  console.log('In the database but not in prisma/schema.prisma:');
  for (const l of onlyInLive.slice(0, 30)) console.log(`  + ${l}`);
  console.log('');
}
console.log('The authoritative schema is backend/db.py::_init_schema.');
console.log('Fix: update that file, drop/recreate the database, run prisma generate,');
console.log('then re-run:  python scripts\\init_db.py && node scripts/prisma-verify.mjs');
process.exit(1);
