import { useState } from 'react'
import type { EntryKind, FileEntry } from '../api/files'
import type { PathSegment } from './FileExplorer'

const dateFormatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: 'medium',
  timeStyle: 'short',
})

function formatDate(iso: string): string {
  return dateFormatter.format(new Date(iso))
}

type EntryRowProps = {
  entry: FileEntry
  kind: EntryKind
  onOpen?: () => void
  onRename: (newName: string) => Promise<void>
  onDelete: (recursive?: boolean) => Promise<void>
}

function EntryRow({ entry, kind, onOpen, onRename, onDelete }: EntryRowProps) {
  const [mode, setMode] = useState<'idle' | 'rename' | 'confirm-delete'>('idle')
  const [nameInput, setNameInput] = useState(entry.name)
  const [busy, setBusy] = useState(false)

  async function submitRename() {
    const trimmed = nameInput.trim()
    if (!trimmed || trimmed === entry.name) {
      setMode('idle')
      return
    }
    setBusy(true)
    try {
      await onRename(trimmed)
      setMode('idle')
    } catch {
      // error already surfaced via the shared banner; stay in rename mode
    } finally {
      setBusy(false)
    }
  }

  async function runDelete(recursive: boolean) {
    setBusy(true)
    try {
      await onDelete(recursive)
    } catch {
      // error already surfaced via the shared banner; stay in confirm-delete mode
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="entry-row">
      <span className="entry-icon" aria-hidden="true">
        {kind === 'folder' ? '📁' : '📄'}
      </span>
      {mode === 'rename' ? (
        <input
          autoFocus
          className="entry-rename-input"
          value={nameInput}
          onChange={(e) => setNameInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') submitRename()
            if (e.key === 'Escape') setMode('idle')
          }}
        />
      ) : (
        <span
          className={`entry-name${kind === 'folder' ? ' clickable' : ''}`}
          onDoubleClick={onOpen}
        >
          {entry.name}
        </span>
      )}

      <span className="entry-date">{formatDate(entry.created)}</span>
      <span className="entry-date">{formatDate(entry.modified)}</span>

      <div className="entry-actions">
        {mode === 'idle' && (
          <>
            <button
              type="button"
              onClick={() => {
                setNameInput(entry.name)
                setMode('rename')
              }}
            >
              Rename
            </button>
            <button type="button" onClick={() => setMode('confirm-delete')}>
              Delete
            </button>
          </>
        )}
        {mode === 'rename' && (
          <>
            <button type="button" disabled={busy} onClick={submitRename}>
              Save
            </button>
            <button type="button" disabled={busy} onClick={() => setMode('idle')}>
              Cancel
            </button>
          </>
        )}
        {mode === 'confirm-delete' && kind === 'folder' && (
          <>
            <span className="confirm-label">Delete?</span>
            <button type="button" disabled={busy} onClick={() => runDelete(false)}>
              Delete
            </button>
            <button type="button" disabled={busy} onClick={() => runDelete(true)}>
              Delete with contents
            </button>
            <button type="button" disabled={busy} onClick={() => setMode('idle')}>
              Cancel
            </button>
          </>
        )}
        {mode === 'confirm-delete' && kind === 'file' && (
          <>
            <span className="confirm-label">Delete?</span>
            <button type="button" disabled={busy} onClick={() => runDelete(false)}>
              Yes
            </button>
            <button type="button" disabled={busy} onClick={() => setMode('idle')}>
              Cancel
            </button>
          </>
        )}
      </div>
    </div>
  )
}

type DraftRowProps = {
  kind: EntryKind
  defaultName: string
  onCommit: (name: string) => Promise<void>
  onCancel: () => void
}

function DraftRow({ kind, defaultName, onCommit, onCancel }: DraftRowProps) {
  const [nameInput, setNameInput] = useState(defaultName)
  const [busy, setBusy] = useState(false)

  async function submit() {
    const trimmed = nameInput.trim()
    if (!trimmed) return
    setBusy(true)
    try {
      await onCommit(trimmed)
    } catch {
      // error already surfaced via the shared banner; stay open for correction
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="entry-row entry-row-draft">
      <span className="entry-icon" aria-hidden="true">
        {kind === 'folder' ? '📁' : '📄'}
      </span>
      <input
        autoFocus
        className="entry-rename-input entry-rename-input-draft"
        value={nameInput}
        onChange={(e) => setNameInput(e.target.value)}
        onFocus={(e) => e.target.select()}
        onKeyDown={(e) => {
          if (e.key === 'Enter') submit()
          if (e.key === 'Escape') onCancel()
        }}
      />
      <div className="entry-actions">
        <button type="button" disabled={busy} onClick={submit}>
          Save
        </button>
        <button type="button" disabled={busy} onClick={onCancel}>
          Cancel
        </button>
      </div>
    </div>
  )
}

type FolderContentProps = {
  path: PathSegment[]
  folders: FileEntry[] | undefined
  files: FileEntry[] | undefined
  onCreateFolder: (name: string) => Promise<void>
  onCreateFile: (name: string) => Promise<void>
  onRename: (kind: EntryKind, entry: FileEntry, newName: string) => Promise<void>
  onDelete: (kind: EntryKind, entry: FileEntry, recursive?: boolean) => Promise<void>
  onNavigate: (id: number | null) => void
  error: string | null
  onDismissError: () => void
}

export function FolderContent({
  path,
  folders,
  files,
  onCreateFolder,
  onCreateFile,
  onRename,
  onDelete,
  onNavigate,
  error,
  onDismissError,
}: FolderContentProps) {
  const [draft, setDraft] = useState<EntryKind | null>(null)

  // Reset any in-progress draft when navigating to a different folder, so it
  // doesn't silently get created in the new location. Adjusting state during
  // render (rather than in an effect) avoids an extra post-commit render pass.
  const currentFolderId = path.length > 0 ? path[path.length - 1].id : null
  const [draftFolderId, setDraftFolderId] = useState(currentFolderId)
  if (currentFolderId !== draftFolderId) {
    setDraftFolderId(currentFolderId)
    setDraft(null)
  }

  const loading = folders === undefined || files === undefined

  const sortedFolders = [...(folders ?? [])].sort((a, b) => a.name.localeCompare(b.name))
  const sortedFiles = [...(files ?? [])].sort((a, b) => a.name.localeCompare(b.name))

  return (
    <section className="folder-content">
      <header className="content-header">
        <nav className="breadcrumb" aria-label="Current path">
          {path.map((segment, i) => {
            const isLast = i === path.length - 1
            const isRoot = segment.id === null
            const label = isRoot ? '/' : isLast ? segment.name : `${segment.name}/`
            return isLast ? (
              <span className="breadcrumb-current" key={segment.id ?? 'root'}>
                {label}
              </span>
            ) : (
              <button
                type="button"
                className="breadcrumb-link"
                key={segment.id ?? 'root'}
                onClick={() => onNavigate(segment.id)}
              >
                {label}
              </button>
            )
          })}
        </nav>
      </header>

      {error && (
        <div className="error-banner">
          <span>{error}</span>
          <button type="button" onClick={onDismissError} aria-label="Dismiss error">
            ×
          </button>
        </div>
      )}

      <div className="create-bar">
        <button type="button" onClick={() => setDraft('folder')}>
          New Folder
        </button>
        <button type="button" onClick={() => setDraft('file')}>
          New File
        </button>
      </div>

      <div className="entry-list-header">
        <span aria-hidden="true" />
        <span>Name</span>
        <span>Created</span>
        <span>Modified</span>
        <span>Actions</span>
      </div>

      <div className="entry-list">
        {draft && (
          <DraftRow
            key={draft}
            kind={draft}
            defaultName={draft === 'folder' ? 'New Folder' : 'New File'}
            onCommit={async (name) => {
              if (draft === 'folder') await onCreateFolder(name)
              else await onCreateFile(name)
              setDraft(null)
            }}
            onCancel={() => setDraft(null)}
          />
        )}
        {loading ? (
          <p className="hint">Loading…</p>
        ) : sortedFolders.length === 0 && sortedFiles.length === 0 && !draft ? (
          <p className="hint">This folder is empty.</p>
        ) : (
          <>
            {sortedFolders.map((folder) => (
              <EntryRow
                key={`folder-${folder.id}`}
                entry={folder}
                kind="folder"
                onOpen={() => onNavigate(folder.id)}
                onRename={(name) => onRename('folder', folder, name)}
                onDelete={(recursive) => onDelete('folder', folder, recursive)}
              />
            ))}
            {sortedFiles.map((file) => (
              <EntryRow
                key={`file-${file.id}`}
                entry={file}
                kind="file"
                onRename={(name) => onRename('file', file, name)}
                onDelete={(recursive) => onDelete('file', file, recursive)}
              />
            ))}
          </>
        )}
      </div>
    </section>
  )
}
