import { Children, type ReactNode } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import rehypeRaw from "rehype-raw";
import type { Components } from "react-markdown";

interface ArticlePreviewProps {
  markdown: string | null;
  isLoading: boolean;
}

function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

function extractText(children: ReactNode): string {
  let text = "";
  Children.forEach(children, (child) => {
    if (typeof child === "string") text += child;
    else if (typeof child === "number") text += String(child);
    else if (child && typeof child === "object" && "props" in child) {
      text += extractText((child as { props: { children?: ReactNode } }).props.children);
    }
  });
  return text;
}

const markdownComponents: Components = {
  a: ({ children, href, ...props }) => (
    <a href={href} target="_blank" rel="noopener noreferrer" {...props}>
      {children}
    </a>
  ),
  h2: ({ children, ...props }) => {
    const id = slugify(extractText(children));
    return <h2 id={id} {...props}>{children}</h2>;
  },
  h3: ({ children, ...props }) => {
    const id = slugify(extractText(children));
    return <h3 id={id} {...props}>{children}</h3>;
  },
  pre: ({ children, ...props }) => (
    <pre {...props}>
      {children}
    </pre>
  ),
  table: ({ children, ...props }) => (
    <div className="overflow-x-auto">
      <table {...props}>{children}</table>
    </div>
  ),
};

export default function ArticlePreview({ markdown, isLoading }: ArticlePreviewProps) {
  if (isLoading && !markdown) {
    return (
      <div className="flex flex-col items-center justify-center h-[60%] text-[#6b7280] text-center px-8">
        <div className="text-5xl mb-3 opacity-40">&#9997;</div>
        <p className="text-sm">Your article will appear here once the research agent completes...</p>
        <div className="w-28 h-0.5 bg-[#e5e2de] rounded mt-4 overflow-hidden relative">
          <div className="absolute inset-0 bg-[#44312a] animate-pulse rounded" />
        </div>
      </div>
    );
  }

  if (!markdown) {
    return (
      <div className="flex flex-col items-center justify-center h-[60%] text-[#6b7280] text-center px-8">
        <div className="text-5xl mb-3 opacity-40">&#128196;</div>
        <p className="text-sm">No article yet. Start a research session to generate one.</p>
      </div>
    );
  }

  return (
    <div className="max-w-[72ch] mx-auto px-4 py-6 md:px-8 md:py-8 overflow-x-auto">
      <article className="article-prose max-w-full">
        <Markdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeHighlight, rehypeRaw]}
          components={markdownComponents}
        >
          {markdown}
        </Markdown>
      </article>
    </div>
  );
}
