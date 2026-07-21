'use client'

import {useEffect, useRef, useState} from 'react'

type CursorState = 'idle' | 'active' | 'hero'

export function CursorBubble() {
  const bubble = useRef<HTMLDivElement>(null)
  const [state, setState] = useState<CursorState>('idle')
  const [label, setLabel] = useState('')

  useEffect(() => {
    const move = (event: PointerEvent) => {
      bubble.current?.style.setProperty('--cursor-x', `${event.clientX}px`)
      bubble.current?.style.setProperty('--cursor-y', `${event.clientY}px`)
    }
    const over = (event: PointerEvent) => {
      const element = (event.target as Element | null)?.closest<HTMLElement>('[data-cursor-label], a, button, input, select')
      if (!element) return
      const cursorLabel = element.dataset.cursorLabel
      setState(cursorLabel ? 'hero' : 'active')
      setLabel(cursorLabel || '')
    }
    const out = (event: PointerEvent) => {
      const next = (event.relatedTarget as Element | null)?.closest<HTMLElement>('[data-cursor-label], a, button, input, select')
      if (next) return
      setState('idle')
      setLabel('')
    }
    window.addEventListener('pointermove', move, {passive: true})
    document.addEventListener('pointerover', over)
    document.addEventListener('pointerout', out)
    return () => {
      window.removeEventListener('pointermove', move)
      document.removeEventListener('pointerover', over)
      document.removeEventListener('pointerout', out)
    }
  }, [])

  return <div ref={bubble} className={`cursor-bubble cursor-${state}`} aria-hidden="true"><span>{label}</span></div>
}
