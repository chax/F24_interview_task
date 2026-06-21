import type { FileEntry } from '../api/files'

type SearchResultsProps = {
  query: string
  results: FileEntry[]
  onBack: () => void
  onNavigateToFile: (file: FileEntry) => void
}

export function SearchResults({ query, results, onBack, onNavigateToFile }: SearchResultsProps) {
  return (
    <section className="folder-content">
      <header className="content-header">
        <button type="button" className="back-link" onClick={onBack}>
          ← Back to folder view
        </button>
        <h2>Search results for "{query}"</h2>
      </header>

      <div className="entry-table">
        <div className="search-result-header">
          <span>Name</span>
          <span>Path</span>
        </div>
        <div className="entry-list">
          {results.length === 0 ? (
            <p className="hint">No files found.</p>
          ) : (
            results.map((file) => (
              <div className="search-result-row" key={file.id}>
                <span className="entry-name">{file.name}</span>
                <button
                  type="button"
                  className="search-result-path"
                  onClick={() => onNavigateToFile(file)}
                >
                  {file.path}
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </section>
  )
}
