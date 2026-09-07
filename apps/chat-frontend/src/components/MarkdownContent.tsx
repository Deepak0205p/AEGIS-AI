'use client';

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export const MarkdownContent = ({ content }: { content: string }) => {
  const displayContent = (content && content.trim().length > 0) 
    ? content 
    : 'No response received. Please try again.';

  return (
    <div className="prose prose-sm dark:prose-invert max-w-none break-words text-slate-800 dark:text-[#e3e3e3] leading-relaxed text-[14.5px] sm:text-[15px]">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{displayContent}</ReactMarkdown>
    </div>
  );
};

export default MarkdownContent;
