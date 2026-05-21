import { Component, type ErrorInfo, type ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import rehypeRaw from "rehype-raw";

interface MarkdownRendererProps {
  content: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

class MarkdownErrorBoundary extends Component<
  { children: ReactNode; fallbackContent: string },
  ErrorBoundaryState
> {
  constructor(props: { children: ReactNode; fallbackContent: string }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("MarkdownRenderer error:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <pre
          style={{
            whiteSpace: "pre-wrap",
            fontFamily: "monospace",
            fontSize: "0.875rem",
            padding: "1rem",
            background: "#f9fafb",
            border: "1px solid #e5e7eb",
            borderRadius: "0.375rem",
            overflow: "auto",
          }}
        >
          {this.props.fallbackContent}
        </pre>
      );
    }
    return this.props.children;
  }
}

export default function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return (
    <MarkdownErrorBoundary fallbackContent={content}>
      <div className="markdown-body">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeRaw, rehypeHighlight]}
        >
          {content}
        </ReactMarkdown>
      </div>
    </MarkdownErrorBoundary>
  );
}
