import { createContext, useContext } from 'react'
import type { FileEntry } from '../api/files'

export type TreeContextValue = {
  childrenByParent: Map<number | null, FileEntry[]>
  expanded: Set<number | null>
  selectedFolderId: number | null
  toggleExpand: (folderId: number | null) => void
  selectFolder: (folderId: number | null) => void
}

export const TreeContext = createContext<TreeContextValue | null>(null)

export function useTreeContext(): TreeContextValue {
  const ctx = useContext(TreeContext)
  if (!ctx) {
    throw new Error('useTreeContext must be used within a TreeContext.Provider')
  }
  return ctx
}
