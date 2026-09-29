import { getApiBase } from '@/lib/apiBase';
import { useAuthStore } from '@/store/useAuthStore';
import { apiFetch } from '@/lib/apiFetch';

export type CodeRunStatus = 'SUCCESS' | 'ERROR' | 'UNSUPPORTED';

export interface CodeRunSqlResult {
  columns: string[];
  rows: (string | number | null)[][];
  row_count: number;
  truncated: boolean;
  sandbox_schema?: string;
}

export interface CodeRunResult {
  status: CodeRunStatus;
  language: string;
  engine: string;
  stdout: string;
  stderr: string;
  exit_code: number;
  duration_ms: number;
  isolated: boolean;
  truncated: boolean;
  message: string;
  /** Did an engine actually run? False for guard rejections and UNSUPPORTED. */
  executed: boolean;
  sql?: CodeRunSqlResult;
  generated_files?: { name: string; size_bytes: number }[];
}

const OFFLINE_RESULT: CodeRunResult = {
  status: 'ERROR',
  language: 'unknown',
  engine: 'sovereign backend',
  stdout: '',
  stderr: 'The backend could not be reached, so nothing was executed.',
  exit_code: -1,
  duration_ms: 0,
  isolated: false,
  truncated: false,
  message: 'Backend unreachable — nothing was executed.',
  executed: false,
};

export interface RunCodeOptions {
  stdinInput?: string;
  filename?: string;
}

/**
 * Executes code on the sovereign backend and returns the genuine result.
 * Never fabricates output: transport failures come back as an explicit
 * `executed: false` error so the UI can say what really happened.
 */
export async function runCode(
  language: string,
  code: string,
  options: RunCodeOptions = {}
): Promise<CodeRunResult> {
  try {
    const token = useAuthStore.getState().token;
    const res = await apiFetch(`${getApiBase()}/api/sandbox/run-code`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        language,
        code,
        stdin_input: options.stdinInput ?? null,
        filename: options.filename ?? null,
      }),
    });

    const data = await res.json().catch(() => null);
    if (!res.ok || !data || typeof data.status !== 'string') {
      return {
        ...OFFLINE_RESULT,
        language,
        stderr: data?.detail || `Backend returned HTTP ${res.status} for the run request.`,
        message: data?.detail || `Run request failed (HTTP ${res.status}).`,
      };
    }
    return data as CodeRunResult;
  } catch (err: any) {
    return {
      ...OFFLINE_RESULT,
      language,
      stderr: err?.message || OFFLINE_RESULT.stderr,
      message: 'Backend unreachable — nothing was executed.',
    };
  }
}

function section(title: string, body: string): string {
  const trimmed = (body || '').trim();
  return trimmed ? `${title}\n${trimmed}` : '';
}

/** Builds the console transcript from real fields only. */
export function formatRunReport(result: CodeRunResult): string {
  const parts: string[] = [];

  const verdict =
    result.status === 'SUCCESS'
      ? `Execution finished (exit code ${result.exit_code})`
      : result.status === 'UNSUPPORTED'
        ? 'Not executed — no engine available'
        : result.executed
          ? `Execution failed (exit code ${result.exit_code})`
          : 'Rejected before execution';

  parts.push(verdict);
  parts.push(`Engine: ${result.engine}`);
  parts.push(`Duration: ${Number(result.duration_ms || 0).toFixed(0)} ms`);
  parts.push(
    `Isolation: ${
      result.isolated
        ? 'sandboxed (filesystem/network restricted)'
        : 'NOT container-isolated — treat output as untrusted'
    }`
  );

  if (result.sql) {
    const capped = result.sql.truncated ? ` (capped, showing first ${result.sql.rows.length})` : '';
    parts.push(
      `Rows: ${result.sql.row_count}${capped} · schema: ${result.sql.sandbox_schema || 'sandbox'}`
    );
  }

  const stdout = section('--- stdout ---', result.stdout);
  if (stdout) parts.push(stdout);

  const stderr = section('--- stderr ---', result.stderr);
  if (stderr) parts.push(stderr);

  const generated = result.generated_files || [];
  if (generated.length > 0) {
    parts.push(
      section(
        '--- generated files ---',
        generated.map((f) => `${f.name} (${f.size_bytes} bytes)`).join('\n')
      )
    );
  }

  if (result.truncated) parts.push('[output truncated by the runner]');
  if (result.message) parts.push(`Note: ${result.message}`);

  return parts.join('\n');
}
