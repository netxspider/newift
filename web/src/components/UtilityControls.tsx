'use client'

import {useEffect, useState} from 'react'

type UtilityControlsProps = {
  search: string
  onSearchChange: (value: string) => void
}

function getInitialTheme() {
  if (typeof document === 'undefined') return false

  return window.localStorage.getItem('theme') === 'dark' || document.documentElement.dataset.theme === 'dark'
}

export function ThemeToggle() {
  const [dark, setDark] = useState(getInitialTheme)

  useEffect(() => {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light'
    window.localStorage.setItem('theme', dark ? 'dark' : 'light')
  }, [dark])

  return <button className="circle-button" type="button" onClick={() => setDark(!dark)} aria-label="Toggle color theme" title="Toggle color theme">{dark ? '☀' : '◐'}</button>
}

export function UtilityControls({search, onSearchChange}: UtilityControlsProps) {
  return (
    <div className="utility-controls">
      <label className="search-control"><span aria-hidden="true">⌕</span><input aria-label="Search stories" value={search} onChange={(event) => onSearchChange(event.target.value)} placeholder="Search stories" /></label>
      <ThemeToggle />
    </div>
  )
}
