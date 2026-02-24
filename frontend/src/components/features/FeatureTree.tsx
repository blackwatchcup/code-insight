import { useState } from 'react'

interface FeatureNode {
  id: string
  name: string
  type: string
  category: string
  description: string
  file_path: string
  line_start: number
  line_end: number
  children: FeatureNode[]
  metadata: Record<string, any>
}

interface Props {
  data: FeatureNode
  onSelect: (node: FeatureNode) => void
}

export function FeatureTree({ data, onSelect }: Props) {
  const [expanded, setExpanded] = useState(false)

  const hasChildren = data.children && data.children.length > 0

  const handleClick = () => {
    if (hasChildren) {
      setExpanded(!expanded)
    } else {
      onSelect(data)
    }
  }

  const getIconByType = (type: string) => {
    switch (type) {
      case 'page':
        return '📄'
      case 'api':
        return '🔌'
      case 'system':
        return '⚙️'
      case 'model':
        return '📊'
      case 'function':
        return '⚡'
      case 'route':
        return '🔀'
      case 'component':
        return '🧩'
      default:
        return '📁'
    }
  }

  return (
    <div className="ml-4">
      <div
        className="flex items-center p-2 hover:bg-gray-100 cursor-pointer rounded transition-colors"
        onClick={handleClick}
      >
        {hasChildren && (
          <span className="mr-2 text-gray-400 text-xs">
            {expanded ? '▼' : '▶'}
          </span>
        )}
        <span className="mr-2">{getIconByType(data.type)}</span>
        <span className="font-medium">{data.name}</span>
        <span className="ml-2 text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
          {data.type}
        </span>
      </div>

      {expanded && hasChildren && (
        <div className="border-l ml-3 pl-2 border-gray-200">
          {data.children.map(child => (
            <FeatureTree
              key={child.id}
              data={child}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  )
}
