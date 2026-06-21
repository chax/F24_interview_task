import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  ApiError,
  createFile,
  createFolder,
  deleteEntry,
  getFilesByName,
  listFiles,
  listFolders,
  renameEntry,
  searchFiles,
  type EntryKind,
  type FileEntry,
} from '../api/files'
import { FolderTreeNode } from './FolderTree'
import { FolderContent } from './FolderContent'
import { SearchResults } from './SearchResults'
import { TreeContext, type TreeContextValue } from './treeContext'
import './FileExplorer.css'

function describeError(err: unknown): string {
  if (err instanceof ApiError) return err.message
  return 'Something went wrong. Please try again.'
}

// SQLite reuses a deleted row's id for the next insert once it's no longer the
// max id in the table, so a freshly created folder can land on an id that an
// old, now-deleted folder used to occupy. Without this, the stale cache entries
// keyed by that id (its children list, its own entry, its expanded state) would
// get served up as if they belonged to the new folder.
function collectCachedDescendantIds(
  rootId: number,
  childrenByParent: Map<number | null, FileEntry[]>,
): number[] {
  const ids: number[] = [rootId]
  const queue: number[] = [rootId]
  while (queue.length > 0) {
    const current = queue.shift()!
    const children = childrenByParent.get(current)
    if (!children) continue
    for (const child of children) {
      ids.push(child.id)
      queue.push(child.id)
    }
  }
  return ids
}

export type PathSegment = { id: number | null; name: string }

export function FileExplorer() {
  const [childrenByParent, setChildrenByParent] = useState<Map<number | null, FileEntry[]>>(new Map())
  const [entriesById, setEntriesById] = useState<Map<number, FileEntry>>(new Map())
  const [expanded, setExpanded] = useState<Set<number | null>>(new Set([null]))
  const [selectedFolderId, setSelectedFolderId] = useState<number | null>(null)
  const [files, setFiles] = useState<FileEntry[] | undefined>(undefined)
  const [error, setError] = useState<string | null>(null)
  const [searchResults, setSearchResults] = useState<FileEntry[] | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [highlightedFileId, setHighlightedFileId] = useState<number | null>(null)

  const loadFolderChildren = useCallback(async (parentId: number | null) => {
    try {
      const data = await listFolders(parentId)
      setChildrenByParent((prev) => new Map(prev).set(parentId, data))
      setEntriesById((prev) => {
        const next = new Map(prev)
        for (const entry of data) next.set(entry.id, entry)
        return next
      })
    } catch (err) {
      setError(describeError(err))
    }
  }, [])

  const loadFiles = useCallback(async (parentId: number | null) => {
    setFiles(undefined)
    try {
      const data = await listFiles(parentId)
      setFiles(data)
    } catch (err) {
      setError(describeError(err))
    }
  }, [])

  useEffect(() => {
    let ignore = false
    listFolders(null)
      .then((data) => {
        if (ignore) return
        setChildrenByParent((prev) => new Map(prev).set(null, data))
        setEntriesById((prev) => {
          const next = new Map(prev)
          for (const entry of data) next.set(entry.id, entry)
          return next
        })
      })
      .catch((err) => {
        if (!ignore) setError(describeError(err))
      })
    listFiles(null)
      .then((data) => {
        if (!ignore) setFiles(data)
      })
      .catch((err) => {
        if (!ignore) setError(describeError(err))
      })
    return () => {
      ignore = true
    }
  }, [])

  const toggleExpand = useCallback(
    (folderId: number | null) => {
      setExpanded((prev) => {
        const next = new Set(prev)
        if (next.has(folderId)) {
          next.delete(folderId)
        } else {
          next.add(folderId)
          if (!childrenByParent.has(folderId)) {
            loadFolderChildren(folderId)
          }
        }
        return next
      })
    },
    [childrenByParent, loadFolderChildren],
  )

  const selectFolder = useCallback(
    (folderId: number | null) => {
      setSelectedFolderId(folderId)
      setSearchResults(null)
      setHighlightedFileId(null)
      setError(null)
      loadFiles(folderId)
      if (!childrenByParent.has(folderId)) {
        loadFolderChildren(folderId)
      }
      setExpanded((prev) => {
        if (prev.has(folderId)) return prev
        const next = new Set(prev)
        next.add(folderId)
        return next
      })
    },
    [childrenByParent, loadFiles, loadFolderChildren],
  )

  // Every folder ever rendered (tree node, content row, or breadcrumb segment) was
  // necessarily fetched via loadFolderChildren first, so it's already in entriesById
  // by the time it's clickable. Ancestor names here can go briefly stale if renamed
  // while a deeper descendant is selected, since only the current folder's children
  // get refreshed on rename/delete; acceptable for this app's scope.
  const path = useMemo<PathSegment[]>(() => {
    const segments: PathSegment[] = []
    let currentId = selectedFolderId
    while (currentId !== null) {
      const entry = entriesById.get(currentId)
      if (!entry) break
      segments.unshift({ id: entry.id, name: entry.name })
      currentId = entry.parent_id
    }
    segments.unshift({ id: null, name: '/' })
    return segments
  }, [selectedFolderId, entriesById])

  const fetchSearchSuggestions = useCallback(
    async (query: string, fromRoot: boolean): Promise<string[]> => {
      try {
        return await searchFiles(query, fromRoot ? null : selectedFolderId)
      } catch (err) {
        setError(describeError(err))
        return []
      }
    },
    [selectedFolderId],
  )

  async function handleSearchSubmit(query: string, fromRoot: boolean) {
    setError(null)
    try {
      const results = await getFilesByName(query, fromRoot ? null : selectedFolderId)
      setSearchQuery(query)
      setSearchResults(results)
    } catch (err) {
      setError(describeError(err))
    }
  }

  function handleNavigateToFile(file: FileEntry) {
    selectFolder(file.parent_id)
    setHighlightedFileId(file.id)
  }

  async function handleCreateFolder(name: string) {
    setError(null)
    try {
      await createFolder(name, selectedFolderId)
      await loadFolderChildren(selectedFolderId)
    } catch (err) {
      setError(describeError(err))
      throw err
    }
  }

  async function handleCreateFile(name: string) {
    setError(null)
    try {
      await createFile(name, selectedFolderId)
      await loadFiles(selectedFolderId)
    } catch (err) {
      setError(describeError(err))
      throw err
    }
  }

  async function handleRename(kind: EntryKind, entry: FileEntry, newName: string) {
    setError(null)
    try {
      await renameEntry(kind, entry.id, newName)
      if (kind === 'folder') {
        await loadFolderChildren(selectedFolderId)
      } else {
        await loadFiles(selectedFolderId)
      }
    } catch (err) {
      setError(describeError(err))
      throw err
    }
  }

  async function handleDelete(kind: EntryKind, entry: FileEntry, recursive = false) {
    setError(null)
    try {
      await deleteEntry(kind, entry.id, recursive)
      if (kind === 'folder') {
        const staleIds = collectCachedDescendantIds(entry.id, childrenByParent)
        setChildrenByParent((prev) => {
          const next = new Map(prev)
          for (const id of staleIds) next.delete(id)
          return next
        })
        setEntriesById((prev) => {
          const next = new Map(prev)
          for (const id of staleIds) next.delete(id)
          return next
        })
        setExpanded((prev) => {
          const next = new Set(prev)
          for (const id of staleIds) next.delete(id)
          return next
        })
        await loadFolderChildren(selectedFolderId)
      } else {
        await loadFiles(selectedFolderId)
      }
    } catch (err) {
      setError(describeError(err))
      throw err
    }
  }

  const treeContextValue = useMemo<TreeContextValue>(
    () => ({ childrenByParent, expanded, selectedFolderId, toggleExpand, selectFolder }),
    [childrenByParent, expanded, selectedFolderId, toggleExpand, selectFolder],
  )

  return (
    <div className="file-explorer">
      <TreeContext.Provider value={treeContextValue}>
        <nav className="tree-pane">
          <h1 className="tree-title">Folders</h1>
          <FolderTreeNode id={null} name="/" depth={0} />
        </nav>
      </TreeContext.Provider>
      {searchResults !== null ? (
        <SearchResults
          query={searchQuery}
          results={searchResults}
          onBack={() => setSearchResults(null)}
          onNavigateToFile={handleNavigateToFile}
        />
      ) : (
        <FolderContent
          path={path}
          folders={childrenByParent.get(selectedFolderId)}
          files={files}
          onCreateFolder={handleCreateFolder}
          onCreateFile={handleCreateFile}
          onRename={handleRename}
          onDelete={handleDelete}
          onNavigate={selectFolder}
          onFetchSearchSuggestions={fetchSearchSuggestions}
          onSearchSubmit={handleSearchSubmit}
          highlightedFileId={highlightedFileId}
          onClearHighlight={() => setHighlightedFileId(null)}
          error={error}
          onDismissError={() => setError(null)}
        />
      )}
    </div>
  )
}
