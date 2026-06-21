import { useTreeContext } from './treeContext'

type FolderTreeNodeProps = {
  id: number | null
  name: string
  depth: number
}

export function FolderTreeNode({ id, name, depth }: FolderTreeNodeProps) {
  const { childrenByParent, expanded, selectedFolderId, toggleExpand, selectFolder } = useTreeContext()
  const isExpanded = expanded.has(id)
  const isSelected = selectedFolderId === id
  const children = childrenByParent.get(id)

  return (
    <div className="tree-node">
      <div className={`tree-row${isSelected ? ' selected' : ''}`} style={{ paddingLeft: 8 + depth * 16 }}>
        <button
          type="button"
          className="tree-caret"
          onClick={() => toggleExpand(id)}
          aria-label={isExpanded ? 'Collapse folder' : 'Expand folder'}
        >
          {isExpanded ? '▾' : '▸'}
        </button>
        <span className="tree-label" onClick={() => selectFolder(id)}>
          {name}
        </span>
      </div>
      {isExpanded && (
        <div className="tree-children">
          {children === undefined ? (
            <div className="tree-hint" style={{ paddingLeft: 8 + (depth + 1) * 16 }}>
              Loading…
            </div>
          ) : children.length === 0 ? (
            <div className="tree-hint" style={{ paddingLeft: 8 + (depth + 1) * 16 }}>
              empty
            </div>
          ) : (
            children.map((child) => (
              <FolderTreeNode key={child.id} id={child.id} name={child.name} depth={depth + 1} />
            ))
          )}
        </div>
      )}
    </div>
  )
}
