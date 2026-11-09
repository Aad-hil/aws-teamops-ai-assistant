import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {Copy} from "lucide-react";

type Props = {content: string};

function safeHref(href?: string) {
  if (!href) return undefined;
  try {
    const parsed = new URL(href);
    return ["https:", "http:"].includes(parsed.protocol) ? parsed.toString() : undefined;
  } catch {
    return undefined;
  }
}

export default function MarkdownMessage({content}: Props) {
  return (
    <div className="markdown-message">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        skipHtml
        urlTransform={url => safeHref(url) || ""}
        components={{
          a: ({href, children}) => {
            const url = safeHref(href);
            return url ? (
              <a href={url} target="_blank" rel="noopener noreferrer">{children}</a>
            ) : <span>{children}</span>;
          },
          img: ({alt}) => <span>{alt ? `[Image: ${alt}]` : "[Image omitted]"}</span>,
          table: ({children}) => <div className="markdown-table-scroll"><table>{children}</table></div>,
          pre: ({children}) => {
            const code = React.Children.toArray(children).find(React.isValidElement);
            const value = code && React.isValidElement<{children?: React.ReactNode}>(code)
              ? String(code.props.children ?? "") : "";
            return (
              <div className="markdown-code-block">
                <button type="button" className="copy-code" onClick={() => void navigator.clipboard.writeText(value)} aria-label="Copy code">
                  <Copy size={13}/> Copy
                </button>
                <pre>{children}</pre>
              </div>
            );
          }
        }}
      >{content}</ReactMarkdown>
    </div>
  );
}
