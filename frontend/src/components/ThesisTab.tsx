import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export function ThesisTab({ ticker, markdown }: { ticker: string; markdown: string | null }) {
  if (!markdown) {
    return (
      <div className="p-6">
        <div className="rounded-lg border border-dashed border-border bg-surface p-8 text-center">
          <p className="text-sm text-ink-2 font-serif mb-2">No thesis file for {ticker}</p>
          <p className="text-xs text-ink-3">
            Run <code className="font-mono bg-border px-1.5 py-0.5 rounded">/thesis-update</code> in Claude Code to generate one.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="prose prose-sm max-w-none
        prose-headings:font-serif prose-headings:text-ink prose-headings:font-normal
        prose-h1:text-2xl prose-h2:text-base prose-h2:font-sans prose-h2:font-semibold prose-h2:tracking-wide prose-h2:text-ink-2 prose-h2:uppercase prose-h2:text-[11px] prose-h2:mt-6
        prose-p:text-ink-2 prose-p:leading-relaxed prose-p:text-sm
        prose-li:text-ink-2 prose-li:text-sm
        prose-strong:text-ink prose-strong:font-semibold
        prose-table:text-xs prose-th:font-mono prose-th:text-ink-3 prose-td:text-ink-2
        prose-code:font-mono prose-code:text-xs prose-code:bg-surface prose-code:px-1 prose-code:rounded
        prose-hr:border-border">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{markdown}</ReactMarkdown>
      </div>
    </div>
  )
}
