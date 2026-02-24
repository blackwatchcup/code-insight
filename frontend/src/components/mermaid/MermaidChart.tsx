import { useEffect, useRef } from 'react'
import mermaid from 'mermaid'

interface Props {
  code: string
  className?: string
}

export function MermaidChart({ code, className }: Props) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'neutral',
      securityLevel: 'loose',
    })

    if (ref.current && code) {
      mermaid.render('mermaid-svg', code).then(({ svg }) => {
        if (ref.current) {
          ref.current.innerHTML = svg
        }
      }).catch((error) => {
        console.error('Mermaid render error:', error)
        if (ref.current) {
          ref.current.innerHTML = `<div class="text-red-500">图表渲染失败</div>`
        }
      })
    }
  }, [code])

  return <div ref={ref} className={className} />
}
