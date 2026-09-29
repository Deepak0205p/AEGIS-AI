/**
 * Read-only Prisma health check + data probe.
 *
 * Proves the generated Prisma Client can actually connect to the live
 * PostgreSQL instance and read every application table. Read-only: it issues
 * SELECTs and never writes.
 *
 *   node scripts/prisma-check.mjs
 *
 * This is a genuine second, independent confirmation that the database is
 * reachable and shaped as expected -- the FastAPI backend uses psycopg, not
 * Prisma, so this exercises a different driver on purpose.
 */
import { PrismaClient } from '@prisma/client';
import { readFileSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';

const ROOT = resolve(import.meta.dirname, '..');

/** Loads repo-root `.env` so DATABASE_URL does not need exporting by hand. */
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
    '  Run:  python scripts\\setup_postgres_windows.py    (or: docker compose up -d)'
  );
  process.exit(2);
}

const prisma = new PrismaClient();

let pass = 0;
let fail = 0;

function check(name, ok, detail = '') {
  if (ok) pass++;
  else fail++;
  console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${name.padEnd(46)}${detail}`);
}

const TABLES = [
  ['Message', 'messages'],
  ['ChatSummary', 'chat_summaries'],
  ['File', 'files'],
  ['FeedbackReport', 'feedback_reports'],
  ['ChatChannel', 'chat_channels'],
  ['ChannelMember', 'channel_members'],
  ['ChannelMessage', 'channel_messages'],
  ['UserActivityLog', 'user_activity_logs'],
];

async function main() {
  console.log('AEGIS AI  |  Prisma Client live check (read-only)');
  console.log('='.repeat(66));

  // 1. Connectivity
  let connected = false;
  try {
    const r = await prisma.$queryRaw`SELECT version() AS v`;
    connected = true;
    check('connect to PostgreSQL', true, String(r[0].v).split(' ').slice(0, 2).join(' '));
  } catch (e) {
    check('connect to PostgreSQL', false, String(e.message).slice(0, 90));
    console.log('\nIs the server running?  start_postgres.bat   (or: docker compose up -d)');
    process.exit(1);
  }

  // 2. Every model is queryable
  for (const [model, table] of TABLES) {
    try {
      const count = await prisma[model].count();
      check(`model ${model} -> ${table}`, true, `${count} row(s)`);
    } catch (e) {
      check(`model ${model} -> ${table}`, false, String(e.message).slice(0, 90));
    }
  }

  // 3. A real filtered read, proving typed field mapping works
  console.log('');
  try {
    const pending = await prisma.file.count({ where: { verificationStatus: 'PENDING_STAGE_1' } });
    check('typed filter on File.verificationStatus', true, `${pending} pending`);
  } catch (e) {
    check('typed filter on File.verificationStatus', false, String(e.message).slice(0, 90));
  }
  try {
    const active = await prisma.chatChannel.count({ where: { department: 'ALL' } });
    check('typed filter on ChatChannel.department', true, `${active} public channel(s)`);
  } catch (e) {
    check('typed filter on ChatChannel.department', false, String(e.message).slice(0, 90));
  }
  try {
    const risky = await prisma.userActivityLog.count({ where: { riskLevel: { in: ['SUSPICIOUS', 'CRITICAL'] } } });
    check('audit ledger readable', true, `${risky} flagged event(s)`);
  } catch (e) {
    check('audit ledger readable', false, String(e.message).slice(0, 90));
  }

  console.log('');
  const total = pass + fail;
  console.log(`${pass}/${total} passed`);
  await prisma.$disconnect();
  process.exit(fail ? 1 : 0);
}

main().catch(async (e) => {
  console.error('unexpected error:', e);
  await prisma.$disconnect().catch(() => {});
  process.exit(1);
});
