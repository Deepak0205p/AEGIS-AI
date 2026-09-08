'use client';

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

/**
 * Pre-processes markdown content to clean up escaped characters,
 * malformed math tags, leaked raw tokens, or irregular whitespace.
 */
function cleanMarkdownText(raw: string): string {
  if (!raw) return '';
  let text = raw;

  // Clean LaTeX text wraps like $\\text{FCV}$, $\\text{D-105}$, \\text{V-1}, etc.
  text = text.replace(/\$\s*\\text\{([^}]+)\}\s*\$/g, '$1');
  text = text.replace(/\\text\{([^}]+)\}/g, '$1');
  text = text.replace(/\$([A-Za-z0-9\-_]+)\$/g, '$1');

  // Clean unrendered escaped characters like \[ or \] or \( or \)
  text = text.replace(/\\\[([\s\S]*?)\\\]/g, '\n\n```\n$1\n```\n\n');
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

export const MarkdownContent = ({ content }: { content: string }) => {
  const cleanedContent = cleanMarkdownText(content);
  const displayContent = cleanedContent.length > 0 ? cleanedContent : 'No response received.';

  return (
    <div className="prose prose-sm dark:prose-invert max-w-none break-words text-slate-800 dark:text-[#e3e3e3] leading-relaxed text-[14.5px] sm:text-[15px]">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
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

          // Code blocks & Inline code
          code: ({ node, inline, className, children, ...props }: any) => {
            if (inline) {
              return (
                <code className="px-1.5 py-0.5 mx-0.5 rounded-md bg-slate-100 dark:bg-white/[0.08] text-blue-700 dark:text-blue-300 font-mono text-[13px] border border-slate-200/60 dark:border-white/10" {...props}>
                  {children}
                </code>
              );
            }
            return (
              <div className="my-3 rounded-xl overflow-hidden border border-slate-200 dark:border-white/10 bg-slate-900 text-slate-100 text-xs sm:text-[13px] font-mono shadow-md">
                <div className="px-4 py-3 overflow-x-auto scrollbar-thin">
                  <code {...props}>{children}</code>
                </div>
              </div>
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
