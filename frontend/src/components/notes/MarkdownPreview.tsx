import React from 'react';

interface MarkdownPreviewProps {
  content: string;
}

/**
 * Validates URLs: only allow safe http, https, and mailto protocols.
 */
function sanitizeUrl(url: string): string {
  const trimmed = url.trim();
  if (/^(https?:\/\/|mailto:)/i.test(trimmed)) {
    return trimmed;
  }
  return '#';
}

/**
 * Parses markdown into safe React elements without dangerouslySetInnerHTML.
 */
export const MarkdownPreview: React.FC<MarkdownPreviewProps> = ({ content }) => {
  if (!content.trim()) {
    return <p className="text-slate-500 italic text-sm">Nothing to preview</p>;
  }

  const lines = content.split('\n');
  const elements: React.ReactNode[] = [];

  let inCodeBlock = false;
  let codeBlockLines: string[] = [];

  const parseInline = (text: string): React.ReactNode[] => {
    // Process inline code `code`, bold **bold**, italic *italic*, links [text](url)
    const tokens: React.ReactNode[] = [];
    const regex = /(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*|\[[^\]]+\]\([^)]+\))/g;
    let lastIndex = 0;
    let match: RegExpExecArray | null;

    while ((match = regex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        tokens.push(text.substring(lastIndex, match.index));
      }

      const matchText = match[0];
      if (matchText.startsWith('`') && matchText.endsWith('`')) {
        tokens.push(
          <code
            key={match.index}
            className="px-1.5 py-0.5 rounded bg-slate-800 text-emerald-400 font-mono text-xs"
          >
            {matchText.slice(1, -1)}
          </code>
        );
      } else if (matchText.startsWith('**') && matchText.endsWith('**')) {
        tokens.push(
          <strong key={match.index} className="font-semibold text-slate-100">
            {matchText.slice(2, -2)}
          </strong>
        );
      } else if (matchText.startsWith('*') && matchText.endsWith('*')) {
        tokens.push(
          <em key={match.index} className="italic text-slate-200">
            {matchText.slice(1, -1)}
          </em>
        );
      } else if (matchText.startsWith('[') && matchText.includes('](')) {
        const linkText = matchText.substring(1, matchText.indexOf(']('));
        const rawUrl = matchText.substring(matchText.indexOf('](') + 2, matchText.length - 1);
        const safeUrl = sanitizeUrl(rawUrl);
        tokens.push(
          <a
            key={match.index}
            href={safeUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-emerald-400 hover:underline underline-offset-2"
          >
            {linkText}
          </a>
        );
      }

      lastIndex = regex.lastIndex;
    }

    if (lastIndex < text.length) {
      tokens.push(text.substring(lastIndex));
    }

    return tokens;
  };

  lines.forEach((line, idx) => {
    // Code blocks
    if (line.startsWith('```')) {
      if (inCodeBlock) {
        elements.push(
          <pre
            key={`code-${idx}`}
            className="p-3 my-2 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-emerald-300 overflow-x-auto"
          >
            <code>{codeBlockLines.join('\n')}</code>
          </pre>
        );
        codeBlockLines = [];
        inCodeBlock = false;
      } else {
        inCodeBlock = true;
      }
      return;
    }

    if (inCodeBlock) {
      codeBlockLines.push(line);
      return;
    }

    // Headings
    if (line.startsWith('### ')) {
      elements.push(
        <h3 key={idx} className="text-base font-semibold text-slate-100 mt-3 mb-1">
          {parseInline(line.substring(4))}
        </h3>
      );
    } else if (line.startsWith('## ')) {
      elements.push(
        <h2 key={idx} className="text-lg font-bold text-slate-100 mt-4 mb-1.5 pb-1 border-b border-slate-800">
          {parseInline(line.substring(3))}
        </h2>
      );
    } else if (line.startsWith('# ')) {
      elements.push(
        <h1 key={idx} className="text-xl font-bold text-slate-100 mt-5 mb-2 pb-1.5 border-b border-slate-800">
          {parseInline(line.substring(2))}
        </h1>
      );
    }
    // Blockquote
    else if (line.startsWith('> ')) {
      elements.push(
        <blockquote
          key={idx}
          className="border-l-4 border-emerald-500/60 pl-3 py-1 my-2 text-slate-300 bg-slate-900/40 rounded-r-lg italic text-sm"
        >
          {parseInline(line.substring(2))}
        </blockquote>
      );
    }
    // Checklists: - [ ] or - [x]
    else if (/^[-*]\s+\[([ xX])\]\s+/.test(line)) {
      const isChecked = /^[-*]\s+\[[xX]\]\s+/.test(line);
      const text = line.replace(/^[-*]\s+\[[ xX]\]\s+/, '');
      elements.push(
        <div key={idx} className="flex items-center gap-2 my-1 text-sm text-slate-300">
          <input
            type="checkbox"
            checked={isChecked}
            readOnly
            className="rounded border-slate-700 text-emerald-500 focus:ring-0 focus:ring-offset-0 bg-slate-900 cursor-default"
          />
          <span className={isChecked ? 'line-through text-slate-500' : ''}>
            {parseInline(text)}
          </span>
        </div>
      );
    }
    // Bulleted list: - or *
    else if (/^[-*]\s+/.test(line)) {
      elements.push(
        <li key={idx} className="ml-5 list-disc text-sm text-slate-300 my-0.5">
          {parseInline(line.replace(/^[-*]\s+/, ''))}
        </li>
      );
    }
    // Numbered list: 1. 2. etc
    else if (/^\d+\.\s+/.test(line)) {
      elements.push(
        <li key={idx} className="ml-5 list-decimal text-sm text-slate-300 my-0.5">
          {parseInline(line.replace(/^\d+\.\s+/, ''))}
        </li>
      );
    }
    // Empty line
    else if (line.trim() === '') {
      elements.push(<div key={idx} className="h-2" />);
    }
    // Paragraph
    else {
      elements.push(
        <p key={idx} className="text-sm text-slate-300 my-1 leading-relaxed">
          {parseInline(line)}
        </p>
      );
    }
  });

  return <div className="space-y-1 prose-slate max-w-none">{elements}</div>;
};
