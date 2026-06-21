import { useEffect, useState } from 'react'

type SearchBarProps = {
  onFetchSuggestions: (query: string, fromRoot: boolean) => Promise<string[]>
  onSubmit: (query: string, fromRoot: boolean) => void
}

export function SearchBar({ onFetchSuggestions, onSubmit }: SearchBarProps) {
  const [query, setQuery] = useState('')
  const [fromRoot, setFromRoot] = useState(false)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [showDropdown, setShowDropdown] = useState(false)

  useEffect(() => {
    let ignore = false
    const trimmed = query.trim()
    const timer = setTimeout(() => {
      if (!trimmed) {
        if (!ignore) setSuggestions([])
        return
      }
      onFetchSuggestions(trimmed, fromRoot).then((names) => {
        if (!ignore) setSuggestions(names)
      })
    }, 250)
    return () => {
      ignore = true
      clearTimeout(timer)
    }
  }, [query, fromRoot, onFetchSuggestions])

  function submit(value: string) {
    if (!value.trim()) return
    setShowDropdown(false)
    onSubmit(value.trim(), fromRoot)
  }

  function selectSuggestion(name: string) {
    setQuery(name)
    submit(name)
  }

  return (
    <div className="search-bar">
      <div className="search-input-wrapper">
        <input
          type="text"
          placeholder="Search files…"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value)
            setShowDropdown(true)
          }}
          onFocus={() => setShowDropdown(true)}
          onBlur={() => setShowDropdown(false)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') submit(query)
            if (e.key === 'Escape') setShowDropdown(false)
          }}
        />
        {showDropdown && suggestions.length > 0 && (
          <ul className="search-dropdown" onMouseDown={(e) => e.preventDefault()}>
            {suggestions.map((name) => (
              <li key={name} onClick={() => selectSuggestion(name)}>
                {name}
              </li>
            ))}
          </ul>
        )}
      </div>
      <label className="search-checkbox">
        <input
          type="checkbox"
          checked={fromRoot}
          onChange={(e) => setFromRoot(e.target.checked)}
        />
        Search from root
      </label>
      <button type="button" onClick={() => submit(query)}>
        Search
      </button>
    </div>
  )
}
