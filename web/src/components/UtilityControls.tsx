'use client'

import {useEffect, useState} from 'react'

type UtilityControlsProps = {
  search: string
  onSearchChange: (value: string) => void
}

export function UtilityControls({search, onSearchChange}: UtilityControlsProps) {
  const [dark, setDark] = useState(false)

  useEffect(() => {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light'
  }, [dark])

  return (
    <div className="utility-controls">
      <label className="search-control"><span aria-hidden="true">⌕</span><input aria-label="Search stories" value={search} onChange={(event) => onSearchChange(event.target.value)} placeholder="Search stories" /></label>
      <button className="circle-button" type="button" onClick={() => setDark(!dark)} aria-label="Toggle color theme" title="Toggle color theme">{dark ? '☀' : '◐'}</button>
    </div>
  )
}
