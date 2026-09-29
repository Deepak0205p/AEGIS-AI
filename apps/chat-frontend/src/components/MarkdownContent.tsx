'use client';

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Play,
  Copy,
  Check,
  Code2,
  Terminal,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Sparkles,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Edit3
} from 'lucide-react';
import { useCanvasStore } from '@/store/useCanvasStore';
import { getApiBase } from '@/lib/apiBase';
import { runCode, formatRunReport, CodeRunResult } from '@/lib/codeRunner';
import rehypeSupSub from '@/lib/rehypeSupSub';

/**
 * Pre-processes markdown content to clean up escaped characters,
 * malformed math tags, leaked raw tokens, or irregular whitespace.
 */
function cleanMarkdownText(raw: string): string {
  if (!raw) return '';
  let text = raw;

  // Clean LaTeX text wraps like $\text{FCV}$, $\text{D-105}$, \text{V-1}, etc.
  text = text.replace(/\$\s*\\text\{([^}]+)\}\s*\$/g, '$1');
  text = text.replace(/\\text\{([^}]+)\}/g, '$1');
  text = text.replace(/\$([A-Za-z0-9\-_]+)\$/g, '$1');

  // Clean unrendered escaped characters like \[ or \] or \( or \)
  text = text.replace(/\\\[([\s\S]*?)\\\]/g, '\n\n```python\n$1\n```\n\n');
  text = text.replace(/\\\(([\s\S]*?)\\\)/g, '`$1`');
  
  // Clean raw LaTeX symbol tags if leaked
  text = text.replace(/\\rightarrow/g, '→');
  text = text.replace(/\\leftarrow/g, '←');
  text = text.replace(/\\cdot/g, '·');
  text = text.replace(/\\degree/g, '°');
  text = text.replace(/\\pm/g, '±');
  text = text.replace(/\\approx/g, '≈');
  text = text.replace(/\\le/g, '≤');
  text = text.replace(/\\ge/g, '≥');
  text = text.replace(/\\times/g, '×');

  // Normalize excessive blank lines
  text = text.replace(/\n{4,}/g, '\n\n\n');

  return text.trim();
}

/**
 * Professional Interactive Python Code Block
 * Supports:
 * - One-click Copy
 * - Instant Run in Air-Gapped Sandbox with genuine live stdout / stderr terminal
 * - Edit in Studio Terminal / Canvas
 */
interface PythonBlockProps {
  code: string;
  language?: string;
}

const PythonCodeBlock = ({ code, language = 'python' }: PythonBlockProps) => {
  const { openCanvas, updateEditedContent } = useCanvasStore();
  const [copied, setCopied] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [terminalOpen, setTerminalOpen] = useState(false);
  const [result, setResult] = useState<CodeRunResult | null>(null);
  const [transportError, setTransportError] = useState<string | null>(null);

  const cleanCode = code.replace(/\n$/, '');

  const handleCopy = () => {
    navigator.clipboard.writeText(cleanCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleOpenStudio = () => {
    const filename = `sandbox_script_${Date.now().toString().slice(-4)}.py`;
    const dynamicId = `deliv-py-${Date.now()}`;
    
    updateEditedContent(dynamicId, { code: cleanCode });
    
    openCanvas({
      id: dynamicId,
      filename,
      type: 'py',
      size_bytes: cleanCode.length,
      size_formatted: `${(cleanCode.length / 1024).toFixed(1)} KB`,
      source_scenario: 'Interactive Code Studio',
      source_requirement: 'Python Sandbox Execution',
      generating_model: 'Local interpreter',
      generated_timestamp: new Date().toLocaleTimeString(),
      // Not computed: a placeholder string here would look like a real digest.
      sha256_hash: 'unavailable',
      summary: 'Interactive Python editor and runner (local subprocess; no container isolation).',
      key_metrics: [
        { label: 'Language', value: 'Python (local interpreter)' },
        { label: 'Isolation', value: 'None - local subprocess' },
        { label: 'Status', value: 'Ready to Run' }
      ],
      // No invented standards references.
      sop_citations: []
    } as any);
  };

  const handleRunSandbox = async () => {
    setIsRunning(true);
    setTerminalOpen(true);
    setResult(null);
    setTransportError(null);

    // Uses the shared runner so the reported engine, isolation and exit code
    // come straight from the backend - no invented "sandbox" framing.
    const runResult = await runCode('python', cleanCode);
    setResult(runResult);
    setIsRunning(false);
  };

  const report = result ? formatRunReport(result) : '';
  const success = result?.status === 'SUCCESS' && result.exit_code === 0;

  return (
    <div className="my-4 rounded-xl border border-slate-700/80 bg-[#080d1a] shadow-xl overflow-hidden text-left">
      {/* 1. TOP HEADER BAR */}
      <div className="flex items-center justify-between px-3 sm:px-4 py-2 bg-[#0d1527] border-b border-slate-800 text-xs">
        {/* Left: Language & Execution Environment */}
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-lg bg-blue-950/70 border border-blue-800/60 text-blue-400 font-mono text-[11px] font-semibold">
            <Code2 className="h-3.5 w-3.5 text-blue-400" />
            <span>Python</span>
          </div>
          <span className="hidden sm:inline-block text-[11px] text-slate-400 font-medium">
            {result
              ? result.isolated
                ? 'container-isolated runner'
                : 'local runner — not container-isolated'
              : 'local runner — not container-isolated'}
          </span>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center space-x-1.5 sm:space-x-2">
          {/* Copy Button */}
          <button
            onClick={handleCopy}
            className="flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/60 text-[11px] font-medium transition-colors"
            title="Copy Python Code"
          >
            {copied ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3 text-slate-400" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>

          {/* Open in Full Studio Terminal */}
          <button
            onClick={handleOpenStudio}
            className="flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-200 hover:text-white border border-slate-700/60 text-[11px] font-medium transition-colors cursor-pointer"
            title="Open Interactive Code Studio & Terminal"
          >
            <Edit3 className="h-3 w-3 text-blue-400" />
            <span className="hidden xs:inline">Edit in Studio</span>
          </button>

          {/* Run in Sandbox Button */}
          <button
            onClick={handleRunSandbox}
            disabled={isRunning}
            className="flex items-center space-x-1.5 px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-[11px] font-bold shadow-md shadow-emerald-950/50 transition-all hover:scale-[1.02] active:scale-95 cursor-pointer disabled:opacity-50"
            title="Execute Python code in isolated sandbox"
          >
            <Play className={`h-3 w-3 fill-current ${isRunning ? 'animate-spin' : ''}`} />
            <span>{isRunning ? 'Running...' : 'Run Code'}</span>
          </button>
        </div>
      </div>

      {/* 2. CODE BLOCK BODY */}
      <div className="p-3 sm:p-4 overflow-x-auto text-[13px] font-mono leading-relaxed bg-[#060a14] text-slate-100 scrollbar-thin">
        <pre className="m-0 p-0">
          <code>{cleanCode}</code>
        </pre>
      </div>

      {/* 3. LIVE SANDBOX EXECUTION OUTPUT CONSOLE */}
      {terminalOpen && (
        <div className="border-t border-slate-800 bg-[#040711]">
          {/* Terminal Title Bar */}
          <div className="flex items-center justify-between px-3 py-1.5 bg-[#090f1f] border-b border-slate-800/80 text-[11px]">
            <div className="flex items-center space-x-2">
              <Terminal className="h-3.5 w-3.5 text-emerald-400" />
              <span className="font-mono font-bold text-slate-200">SANDBOX OUTPUT</span>
              {isRunning && (
                <span className="text-amber-400 flex items-center gap-1">
                  <RefreshCw className="h-3 w-3 animate-spin" />
                  Executing...
                </span>
              )}
              {result && (
                <>
                  {success ? (
                    <span className="flex items-center gap-1 px-1.5 py-0.2 rounded bg-emerald-950/80 border border-emerald-700/60 text-emerald-400 font-medium text-[10px]">
                      <CheckCircle2 className="h-2.5 w-2.5 text-emerald-400" />
                      Exit 0
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 px-1.5 py-0.2 rounded bg-rose-950/80 border border-rose-700/60 text-rose-400 font-medium text-[10px]">
                      <XCircle className="h-2.5 w-2.5 text-rose-400" />
                      {result.status === 'UNSUPPORTED' ? 'Not run' : `Exit ${result.exit_code}`}
                    </span>
                  )}
                  <span className="text-slate-500 font-mono text-[10px]">
                    {Math.round(Number(result.duration_ms || 0))}ms
                  </span>
                </>
              )}
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => setTerminalOpen(false)}
                className="text-slate-400 hover:text-white text-[11px] p-0.5"
              >
                Hide
              </button>
            </div>
          </div>

          {/* Console Content */}
          <div className="p-3 text-xs font-mono max-h-56 overflow-y-auto whitespace-pre-wrap">
            {isRunning && (
              <span className="text-slate-400 italic">Running on the backend...</span>
            )}
            {!isRunning && result && (
              <div>
                <div className="text-slate-300">{report}</div>
                {result.stdout && (
                  <div className="text-emerald-400 leading-relaxed mt-2 whitespace-pre-wrap">{result.stdout}</div>
                )}
              </div>
            )}
            {!isRunning && transportError && (
              <div className="text-rose-400">{transportError}</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Read-only fenced code block for languages the chat cannot execute.
 * It offers Copy only - never a Run button that would fail or, worse,
 * execute the wrong language.
 */
const StaticCodeBlock = ({ code, language }: { code: string; language: string }) => {
  const [copied, setCopied] = useState(false);

  return (
    <div className="my-4 rounded-xl border border-slate-700/80 bg-[#080d1a] shadow-xl overflow-hidden text-left">
      <div className="flex items-center justify-between px-3 sm:px-4 py-2 bg-[#0d1527] border-b border-slate-800 text-xs">
        <div className="flex items-center gap-2">
          <Code2 className="h-3.5 w-3.5 text-slate-400" />
          <span className="text-slate-300 font-mono text-[11px] font-semibold uppercase">{language}</span>
        </div>
        <button
          onClick={() => {
            navigator.clipboard.writeText(code);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
          }}
          className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/60 text-[11px] font-medium transition-colors"
          title={`Copy ${language} code`}
        >
          {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3 text-slate-400" />}
          <span>{copied ? 'Copied' : 'Copy'}</span>
        </button>
      </div>
      <div className="p-3 sm:p-4 overflow-x-auto text-[13px] font-mono leading-relaxed bg-[#060a14] text-slate-100">
        <pre className="m-0 p-0">
          <code>{code}</code>
        </pre>
      </div>
    </div>
  );
};

export const MarkdownContent = ({ content }: { content: string }) => {
  const cleanedContent = cleanMarkdownText(content);
  const displayContent = cleanedContent.length > 0 ? cleanedContent : 'No response received.';

  return (
    <div className="prose prose-sm dark:prose-invert max-w-none break-words text-slate-800 dark:text-[#e3e3e3] leading-relaxed text-[14.5px] sm:text-[15px]">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeSupSub]}
        components={{
          // Styled Tables
          table: ({ node, ...props }) => (
            <div className="my-4 w-full overflow-x-auto rounded-xl border border-slate-200 dark:border-white/10 shadow-xs">
              <table className="w-full text-left text-xs sm:text-sm border-collapse" {...props} />
            </div>
          ),
          thead: ({ node, ...props }) => (
            <thead className="bg-slate-100/80 dark:bg-white/[0.06] border-b border-slate-200 dark:border-white/10 font-semibold text-slate-900 dark:text-white" {...props} />
          ),
          th: ({ node, ...props }) => (
            <th className="px-3.5 py-2.5 font-semibold text-slate-900 dark:text-white border-r last:border-r-0 border-slate-200 dark:border-white/10" {...props} />
          ),
          td: ({ node, ...props }) => (
            <td className="px-3.5 py-2 border-t border-r last:border-r-0 border-slate-200/80 dark:border-white/[0.06] text-slate-700 dark:text-slate-300" {...props} />
          ),
          tr: ({ node, ...props }) => (
            <tr className="hover:bg-slate-50/50 dark:hover:bg-white/[0.02] transition-colors" {...props} />
          ),

          // Styled Headings
          h1: ({ node, ...props }) => (
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-white mt-6 mb-3 first:mt-0 flex items-center gap-2 border-b border-slate-200 dark:border-white/10 pb-2" {...props} />
          ),
          h2: ({ node, ...props }) => (
            <h2 className="text-lg sm:text-xl font-bold tracking-tight text-slate-900 dark:text-white mt-5 mb-2.5 first:mt-0" {...props} />
          ),
          h3: ({ node, ...props }) => (
            <h3 className="text-base sm:text-lg font-semibold text-slate-800 dark:text-slate-100 mt-4 mb-2" {...props} />
          ),

          // Styled Lists
          ul: ({ node, ...props }) => (
            <ul className="my-2.5 pl-5 list-disc space-y-1.5 marker:text-blue-500 dark:marker:text-blue-400" {...props} />
          ),
          ol: ({ node, ...props }) => (
            <ol className="my-2.5 pl-5 list-decimal space-y-1.5 marker:text-blue-500 dark:marker:text-blue-400 font-medium" {...props} />
          ),
          li: ({ node, ...props }) => (
            <li className="leading-relaxed" {...props} />
          ),

          // Styled Blockquotes / Notes
          blockquote: ({ node, ...props }) => (
            <blockquote className="my-3.5 pl-4 py-1.5 border-l-3 border-blue-500 bg-blue-50/50 dark:bg-blue-500/[0.08] dark:border-blue-400 rounded-r-xl italic text-slate-700 dark:text-slate-300 text-[14px]" {...props} />
          ),

          // Fenced code blocks.
          //
          // react-markdown v9 removed the `inline` prop, so branching on it
          // renders *every* code span - including inline words like `volume` -
          // as a full runnable block. A fenced block is always wrapped in <pre>,
          // so the block is detected here and the `code` handler below is left
          // to style inline spans only.
          pre: ({ node, children, ...props }: any) => {
            const child = React.Children.count(children) === 1
              ? (React.Children.toArray(children)[0] as React.ReactElement<any>)
              : null;
            const className = child?.props?.className || '';
            const match = /language-([\w+#-]+)/.exec(className);
            const language = (match?.[1] || 'python').toLowerCase();
            const codeText = String(child?.props?.children ?? '').replace(/\n$/, '');

            if (!codeText) return <pre {...props}>{children}</pre>;

            if (language === 'python' || language === 'py') {
              return <PythonCodeBlock code={codeText} language="python" />;
            }
            // Other languages are shown verbatim; the chat only runs Python, so
            // no misleading "Run" button is offered for them.
            return <StaticCodeBlock code={codeText} language={language} />;
          },

          // Inline code spans only (block code is handled by `pre` above).
          code: ({ node, className, children, ...props }: any) => (
            <code
              className="px-1.5 py-0.5 mx-0.5 rounded-md bg-slate-100 dark:bg-white/[0.08] text-blue-700 dark:text-blue-300 font-mono text-[13px] border border-slate-200/60 dark:border-white/10"
              {...props}
            >
              {children}
            </code>
          ),

          // Standard Markdown Links
          a: ({ node, href, children, ...props }: any) => {
            const linkHref = href || '';
            const isFileLink = linkHref.includes('/api/files/') || linkHref.startsWith('/api/files/');
            if (isFileLink) {
              const fileId = linkHref.replace(/^.*\/api\/files\/(download\/)?/, '').trim();
              return (
                <button
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    useCanvasStore.getState().openCanvas(fileId);
                  }}
                  className="inline-flex items-center gap-1 font-semibold text-blue-600 dark:text-[#a8c7fa] hover:underline cursor-pointer"
                  title="Open in Workspace"
                >
                  {children}
                </button>
              );
            }
            return (
              <a
                href={linkHref}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 dark:text-[#a8c7fa] hover:underline inline-flex items-center gap-0.5 font-medium"
                {...props}
              >
                {children}
                <ExternalLink className="h-3 w-3 inline-block ml-0.5 opacity-70" />
              </a>
            );
          },

          // Strong emphasis
          strong: ({ node, ...props }) => (
            <strong className="font-semibold text-slate-900 dark:text-white" {...props} />
          ),

          // Horizontal rule
          hr: ({ node, ...props }) => (
            <hr className="my-5 border-slate-200 dark:border-white/10" {...props} />
          ),
        }}
      >
        {displayContent}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownContent;
