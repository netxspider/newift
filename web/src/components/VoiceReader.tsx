'use client'

import {useEffect, useRef, useState, useCallback} from 'react'

export interface VoiceReaderProps {
  title: string
  excerpt?: string
  keyPoints?: string[]
  paragraphs?: string[]
  readTime?: number
}

const SPEED_OPTIONS = [1, 1.25, 1.5] as const

export function VoiceReader({
  title,
  excerpt,
  keyPoints = [],
  paragraphs = [],
  readTime = 3,
}: VoiceReaderProps) {
  const [isSupported, setIsSupported] = useState(true)
  const [isPlaying, setIsPlaying] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [speedIndex, setSpeedIndex] = useState(0)
  const [currentChunk, setCurrentChunk] = useState(0)
  const [totalChunks, setTotalChunks] = useState(0)

  const chunksRef = useRef<string[]>([])
  const currentChunkRef = useRef(0)
  const isPlayingRef = useRef(false)
  const speedRef = useRef<number>(1)

  // Initialize SpeechSynthesis and build text chunks
  useEffect(() => {
    if (typeof window !== 'undefined') {
      if (!('speechSynthesis' in window)) {
        setIsSupported(false)
        return
      }

      const textBlocks: string[] = []
      if (title) textBlocks.push(title)
      if (excerpt) textBlocks.push(excerpt)
      if (keyPoints.length > 0) {
        textBlocks.push(`Key takeaways: ${keyPoints.join('. ')}`)
      }
      if (paragraphs.length > 0) {
        textBlocks.push(...paragraphs)
      }

      chunksRef.current = textBlocks
      setTotalChunks(textBlocks.length)
    }

    return () => {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel()
      }
    }
  }, [title, excerpt, keyPoints, paragraphs])

  // Keep ref synchronized with state
  useEffect(() => {
    speedRef.current = SPEED_OPTIONS[speedIndex]
  }, [speedIndex])

  const speakChunk = useCallback((index: number) => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return

    const chunks = chunksRef.current
    if (index >= chunks.length) {
      setIsPlaying(false)
      setIsPaused(false)
      setCurrentChunk(0)
      currentChunkRef.current = 0
      isPlayingRef.current = false
      return
    }

    currentChunkRef.current = index
    setCurrentChunk(index)

    const utterance = new SpeechSynthesisUtterance(chunks[index])
    utterance.rate = speedRef.current
    utterance.pitch = 1.0

    // Choose preferred natural English voice if available
    const voices = window.speechSynthesis.getVoices()
    const preferredVoice =
      voices.find(
        (v) =>
          v.lang.startsWith('en') &&
          (v.name.includes('Natural') ||
            v.name.includes('Google') ||
            v.name.includes('Premium') ||
            v.name.includes('Samantha') ||
            v.name.includes('Daniel')),
      ) ||
      voices.find((v) => v.lang.startsWith('en')) ||
      null

    if (preferredVoice) {
      utterance.voice = preferredVoice
    }

    utterance.onend = () => {
      if (isPlayingRef.current) {
        // Natural editorial pause between sections
        setTimeout(() => {
          if (isPlayingRef.current) {
            speakChunk(index + 1)
          }
        }, 220)
      }
    }

    utterance.onerror = (e) => {
      // SpeechSynthesis 'interrupted' is normal when user cancels or pauses
      if (e.error !== 'interrupted') {
        setIsPlaying(false)
        setIsPaused(false)
        isPlayingRef.current = false
      }
    }

    window.speechSynthesis.speak(utterance)
  }, [])

  const handlePlayToggle = () => {
    if (!isSupported) return

    if (isPlaying) {
      if (isPaused) {
        window.speechSynthesis.resume()
        setIsPaused(false)
      } else {
        window.speechSynthesis.pause()
        setIsPaused(true)
      }
      return
    }

    // Start playback
    window.speechSynthesis.cancel()
    setIsPlaying(true)
    setIsPaused(false)
    isPlayingRef.current = true
    speakChunk(currentChunkRef.current)
  }

  const handleStop = () => {
    if (!isSupported) return
    window.speechSynthesis.cancel()
    setIsPlaying(false)
    setIsPaused(false)
    setCurrentChunk(0)
    currentChunkRef.current = 0
    isPlayingRef.current = false
  }

  const handleCycleSpeed = () => {
    const nextIndex = (speedIndex + 1) % SPEED_OPTIONS.length
    setSpeedIndex(nextIndex)
    const newSpeed = SPEED_OPTIONS[nextIndex]
    speedRef.current = newSpeed

    // If currently speaking, restart current chunk at new rate
    if (isPlaying && !isPaused) {
      window.speechSynthesis.cancel()
      speakChunk(currentChunkRef.current)
    }
  }

  if (!isSupported) {
    return null
  }

  return (
    <div
      className={`voice-reader-bar ${isPlaying ? 'is-active' : ''}`}
      role="region"
      aria-label="Audio Story Player"
    >
      <div className="voice-reader-left">
        <button
          type="button"
          className="voice-play-btn"
          onClick={handlePlayToggle}
          aria-label={isPlaying ? (isPaused ? 'Resume speaking' : 'Pause speaking') : 'Listen to story'}
          title={isPlaying ? (isPaused ? 'Resume' : 'Pause') : 'Listen to story'}
        >
          {isPlaying && !isPaused ? (
            /* Pause Icon */
            <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
              <rect x="5" y="4" width="4" height="16" rx="1.5" />
              <rect x="15" y="4" width="4" height="16" rx="1.5" />
            </svg>
          ) : (
            /* Speaker / Play Icon */
            <svg
              width="17"
              height="17"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" fill="currentColor" />
              <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
              <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
            </svg>
          )}
        </button>

        <div className="voice-info">
          <div className="voice-title-wrap">
            <span className="voice-title">
              {isPlaying ? (isPaused ? 'Audio briefing paused' : 'Speaking story...') : 'Listen to this story'}
            </span>
            {isPlaying && !isPaused && (
              <span className="voice-equalizer" aria-hidden="true">
                <span className="eq-bar bar-1" />
                <span className="eq-bar bar-2" />
                <span className="eq-bar bar-3" />
                <span className="eq-bar bar-4" />
              </span>
            )}
          </div>
          <span className="voice-sub">
            {isPlaying
              ? `Section ${currentChunk + 1} of ${totalChunks || 1}`
              : `Audio briefing • ~${readTime} min listen`}
          </span>
        </div>
      </div>

      <div className="voice-reader-right">
        {isPlaying && (
          <button
            type="button"
            className="voice-icon-btn voice-stop-btn"
            onClick={handleStop}
            aria-label="Stop audio"
            title="Stop audio"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
              <rect x="4" y="4" width="16" height="16" rx="2" />
            </svg>
          </button>
        )}

        <button
          type="button"
          className="voice-speed-btn"
          onClick={handleCycleSpeed}
          aria-label={`Speech rate: ${SPEED_OPTIONS[speedIndex]}x. Click to change.`}
          title="Change playback speed"
        >
          {SPEED_OPTIONS[speedIndex]}x
        </button>
      </div>
    </div>
  )
}
