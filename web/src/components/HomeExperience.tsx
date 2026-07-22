'use client'

import Link from 'next/link'
import {useMemo, useState} from 'react'
import type {Story} from '@/lib/content'
import {UtilityControls} from './UtilityControls'
import {Footer} from './SiteShell'

function relativeDate(date?: string) {
  if (!date) return 'Just now'
  const hours = Math.max(1, Math.round((Date.now() - new Date(date).getTime()) / 3_600_000))
  return hours < 24 ? `${hours}h ago` : `${Math.round(hours / 24)}d ago`
}

function StoryVisual({story, variant = ''}: {story: Story; variant?: string}) {
  return story.imageUrl ? <img className={`story-image ${variant}`} src={story.imageUrl} alt={story.image?.alt || story.title} /> : <div className={`story-image placeholder ${variant}`} aria-hidden="true"><span>{story.category?.title?.slice(0, 1) || 'N'}</span></div>
}

function StoryMeta({story}: {story: Story}) {
  return <p className="story-meta">{story.category?.title || 'Trending'} <i /> {relativeDate(story.publishedAt)} <i /> {story.readTime || 4} min read</p>
}

export function HomeExperience({stories}: {stories: Story[]}) {
  const [sortBy, setSortBy] = useState<'latest' | 'popular'>('latest')
  const [visible, setVisible] = useState(10)
  const [search, setSearch] = useState('')
  const [email, setEmail] = useState('')
  const [consent, setConsent] = useState(false)
  const [subscriptionState, setSubscriptionState] = useState<'idle' | 'submitting' | 'success' | 'error'>('idle')
  const normalizedSearch = search.trim().toLocaleLowerCase()
  const latestStories = useMemo(() => [...stories]
    .filter((story) => !normalizedSearch || [story.title, story.excerpt, story.category?.title, story.author?.name].some((value) => value?.toLocaleLowerCase().includes(normalizedSearch)))
    .sort((a, b) => +new Date(b.publishedAt || 0) - +new Date(a.publishedAt || 0)), [stories, normalizedSearch])
  const featured = latestStories[0]
  const rest = useMemo(() => [...latestStories.slice(1)].sort((a, b) => sortBy === 'popular' ? (b.viewCount || 0) - (a.viewCount || 0) : +new Date(b.publishedAt || 0) - +new Date(a.publishedAt || 0)), [latestStories, sortBy])
  const categoryStories = (title: string) => latestStories.filter((story) => story.category?.title === title).slice(0, 3)

  const subscribe = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!email || !consent || subscriptionState === 'submitting') return

    setSubscriptionState('submitting')
    try {
      const response = await fetch('/', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: new URLSearchParams({'form-name': 'newsletter', email, consent: 'agreed'}).toString(),
      })
      if (!response.ok) throw new Error('Subscription failed')
      setSubscriptionState('success')
      setEmail('')
      setConsent(false)
    } catch {
      setSubscriptionState('error')
    }
  }

  return (
    <div className="site-frame">
      <header className="site-header"><Link className="brand" href="/">newift<span>•</span></Link><UtilityControls search={search} onSearchChange={setSearch} /></header>
      <main>
        <section className="hero"><p className="eyebrow">THE PULSE, CURATED</p><h1 data-cursor-label="NEWIFT">What&apos;s trending now,<br /><em>delivered swift.</em></h1><p className="hero-copy">Newift brings you fast, real-time coverage on today’s top trending stories, viral events, tech, pop culture, and breaking updates from around the web.</p><a className="text-link" href="#latest">Explore the latest <span>↓</span></a></section>

        {normalizedSearch && <section className="search-status" aria-live="polite"><p className="eyebrow">SEARCH</p><p>{latestStories.length ? `${latestStories.length} ${latestStories.length === 1 ? 'story' : 'stories'} matching “${search.trim()}”` : `No stories matching “${search.trim()}”`}</p></section>}
        {featured ? <><section className="headline-grid" id="latest">
          <article className="featured-card"><Link href={`/posts/${featured.slug}`}><StoryVisual story={featured} variant="featured-visual" /></Link><div className="featured-content"><StoryMeta story={featured} /><Link href={`/posts/${featured.slug}`}><h2>{featured.title}</h2></Link><p>{featured.excerpt}</p><div className="byline"><span>By {featured.author?.name || 'Newift Desk'}</span><Link href={`/posts/${featured.slug}`}>Read story <span>↗</span></Link></div></div></article>
          <aside className="latest-panel"><div className="section-heading"><div><p className="eyebrow">DON&apos;T MISS</p><h2>Latest stories</h2></div><select aria-label="Sort stories" value={sortBy} onChange={(event) => setSortBy(event.target.value as 'latest' | 'popular')}><option value="latest">Latest</option><option value="popular">Popular</option></select></div><div className="latest-scroll">{rest.length ? rest.slice(0, visible).map((story, index) => <Link className="compact-story" key={story._id} href={`/posts/${story.slug}`}><span className="story-number">{String(index + 2).padStart(2, '0')}</span><div><StoryMeta story={story} /><h3>{story.title}</h3></div><span className="arrow">↗</span></Link>) : <p className="empty-list">New post coming up soon.</p>}{visible < rest.length && <button className="load-button" onClick={() => setVisible((count) => count + 10)}>Load more stories <span>↓</span></button>}</div></aside>
        </section>

        <section className="category-section"><div className="category-rows">{['Global', 'Tech', 'Entertainment'].map((category, index) => {const picks = categoryStories(category); return <div className="category-row" key={category}><div className="category-label"><span>0{index + 1}</span><h3>{category}</h3><a href="#latest">View all <b>↗</b></a></div><div className="category-picks">{picks.length ? picks.map((story) => <Link className="category-story" href={`/posts/${story.slug}`} key={story._id}><StoryVisual story={story} /><StoryMeta story={story} /><h4>{story.title}</h4></Link>) : <p className="empty-category">No {category.toLowerCase()} stories yet.</p>}</div></div>})}</div></section></> : <section className="empty-stories" id="latest"><p className="eyebrow">{normalizedSearch ? 'NO MATCHES' : 'THE FEED IS CLEAR'}</p><h2>{normalizedSearch ? 'Try another search.' : 'Stories will appear here when they’re published.'}</h2><p>{normalizedSearch ? 'Search titles, descriptions, categories, or authors.' : 'Open Newift Studio to publish your first post.'}</p></section>}

        <section className="newsletter"><div><p className="eyebrow">STAY IN THE KNOW</p><h2>Good news.<br /><em>In your inbox.</em></h2><p>One smart, no-noise briefing on the stories moving the internet. Delivered weekly.</p></div><form name="newsletter" method="POST" data-netlify="true" data-netlify-honeypot="bot-field" onSubmit={subscribe}><input type="hidden" name="form-name" value="newsletter" /><p className="form-trap"><label>Leave this field empty <input name="bot-field" /></label></p><div className="newsletter-input"><input aria-label="Email address" name="email" type="email" value={email} onChange={(event) => {setEmail(event.target.value); if (subscriptionState !== 'idle') setSubscriptionState('idle')}} placeholder="Your email address" required /><button type="submit" disabled={!consent || subscriptionState === 'submitting'}>{subscriptionState === 'success' ? 'You’re in!' : subscriptionState === 'submitting' ? 'Adding…' : 'Subscribe'} <span>↗</span></button></div><label className="consent"><input name="consent" value="agreed" type="checkbox" checked={consent} onChange={(event) => {setConsent(event.target.checked); if (subscriptionState !== 'idle') setSubscriptionState('idle')}} /> <span>I agree to receive the Newift newsletter and accept the <Link href="/privacy">privacy policy</Link>.</span></label>{subscriptionState === 'success' && <p className="success-message">Thanks — your next briefing is on its way.</p>}{subscriptionState === 'error' && <p className="newsletter-error">We couldn&apos;t save your subscription. Please try again.</p>}</form></section>
      </main>
      <Footer />
    </div>
  )
}
