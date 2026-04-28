/**
 * DataTable — Stripe 风格数据表格
 * 支持：列定义、排序、空状态、自定义单元格渲染
 */

/**
 * @param {{
 *   columns: Array<{ key: string, label: string, sortable?: boolean, width?: string, render?: (val, row) => ReactNode }>,
 *   data: any[],
 *   loading?: boolean,
 *   emptyMessage?: string,
 *   className?: string,
 *   onRowClick?: (row) => void,
 *   selectedIds?: Set<number|string>,
 *   onSelectChange?: (selected: Set) => void,
 *   rowKey?: string,
 * }} props
 */
export function DataTable({
  columns = [],
  data = [],
  loading = false,
  emptyMessage = '暂无数据',
  className = '',
  onRowClick,
  selectedIds,
  onSelectChange,
  rowKey = 'id',
}) {
  const allSelected = data.length > 0 && data.every(row => selectedIds?.has(row[rowKey]))
  const someSelected = data.some(row => selectedIds?.has(row[rowKey]))

  function toggleAll() {
    if (!onSelectChange) return
    if (allSelected) {
      const next = new Set(selectedIds)
      data.forEach(row => next.delete(row[rowKey]))
      onSelectChange(next)
    } else {
      const next = new Set(selectedIds || [])
      data.forEach(row => next.add(row[rowKey]))
      onSelectChange(next)
    }
  }

  function toggleRow(id) {
    if (!onSelectChange || !selectedIds) return
    const next = new Set(selectedIds)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    onSelectChange(next)
  }

  return (
    <div className={['table-wrapper', className].filter(Boolean).join(' ')}>
      <table className="data-table">
        <thead>
          <tr>
            {onSelectChange && (
              <th className="w-10 pr-0">
                <input
                  type="checkbox"
                  className="w-4 h-4 rounded cursor-pointer"
                  style={{ accentColor: '#8b5cf6' }}
                  checked={allSelected}
                  ref={el => el && (el.indeterminate = !allSelected && someSelected)}
                  onChange={toggleAll}
                />
              </th>
            )}
            {columns.map(col => (
              <th
                key={col.key}
                style={col.width ? { width: col.width } : undefined}
                className={col.sortable ? 'cursor-pointer select-none' : ''}
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>

        <tbody>
          {loading ? (
            <tr>
              <td colSpan={columns.length + (onSelectChange ? 1 : 0)} className="text-center py-16">
                <div className="flex items-center justify-center gap-3 text-text-secondary">
                  <span className="spinner" />
                  加载中...
                </div>
              </td>
            </tr>
          ) : data.length === 0 ? (
            <tr>
              <td colSpan={columns.length + (onSelectChange ? 1 : 0)} className="text-center py-16">
                <span className="text-text-muted text-sm">{emptyMessage}</span>
              </td>
            </tr>
          ) : (
            data.map((row, i) => {
              const isSelected = selectedIds?.has(row[rowKey])
              return (
                <tr
                  key={row[rowKey] ?? i}
                  onClick={() => onRowClick?.(row)}
                  className={[
                    onRowClick ? 'cursor-pointer' : '',
                    isSelected ? '!bg-accent-light' : '',
                  ].filter(Boolean).join(' ')}
                >
                  {onSelectChange && (
                    <td className="pr-0" onClick={e => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        className="w-4 h-4 rounded cursor-pointer"
                        style={{ accentColor: '#8b5cf6' }}
                        checked={isSelected}
                        onChange={() => toggleRow(row[rowKey])}
                      />
                    </td>
                  )}
                  {columns.map(col => (
                    <td key={col.key}>
                      {col.render
                        ? col.render(row[col.key], row)
                        : (row[col.key] ?? '—')}
                    </td>
                  ))}
                </tr>
              )
            })
          )}
        </tbody>
      </table>
    </div>
  )
}
