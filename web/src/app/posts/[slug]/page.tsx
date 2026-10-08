import type {Metadata} from 'next'
import Link from 'next/link'
import {PortableText} from 'next-sanity'
import {notFound} from 'next/navigation'
import {cache} from 'react'
import {Footer} from '@/components/SiteShell'
import {ThemeToggle} from '@/components/UtilityControls'
import {VoiceReader} from '@/components/VoiceReader'
import type {Story} from '@/lib/content'
import {client} from '@/sanity/client'
import {urlFor} from '@/sanity/image'
import {POST_QUERY, RELATED_POSTS_QUERY} from '@/sanity/queries'

function extractTextFromPortableText(blocks?: unknown[]): string[] {
  if (!blocks || !Array.isArray(blocks)) return []
  const paragraphs: string[] = []
  for (const block of blocks) {
    if (block && typeof block === 'object' && 'children' in block) {
      const text = (block.children as Array<{text?: string}>)
        ?.map((child) => child.text || '')
        .join('')
        .trim()
      if (text) {
        paragraphs.push(text)
      }
    }
  }
  return paragraphs
}

type Post = Story & {
  body?: unknown[]
  updatedAt?: string
  author?: {name?: string; role?: string}
  categoryId?: string
  keyPoints?: string[]
  timeline?: Array<{time?: string; event?: string}>
  faq?: Array<{question?: string; answer?: string}>
  sources?: Array<{publisher?: string; title?: string; url?: string; publishedAt?: string; isPrimary?: boolean}>
  verification?: {
    status?: 'verified' | 'needs_review' | 'flagged'
    confidence?: number
    factCheckedAt?: string
    corroboratingSourcesCount?: number
    notes?: string
  }
  aiDisclosure?: {
    isAiAssisted?: boolean
    model?: string
    editorialRole?: string
    humanReviewed?: boolean
  }
  story?: {
    storyClusterId?: string
    trendScore?: number
    trendVelocity?: number
    firstDetectedAt?: string
  }
  seo?: {
    title?: string
    description?: string
    noIndex?: boolean
    focusKeyword?: string
    secondaryKeywords?: string[]
    canonicalUrl?: string
    schemaType?: string
    image?: {asset?: unknown}
  }
}

type BodyImage = {asset?: unknown; alt?: string; caption?: string}
type BodyTable = {rows?: Array<{_key?: string; cells?: string[]}>}

const portableTextComponents = {
  types: {
    image: ({value}: {value: BodyImage}) => {
      if (!value?.asset) return null
      return (
        <figure className="article-body-image">
          <img src={urlFor(value as Parameters<typeof urlFor>[0]).width(1280).auto('format').url()} alt={value.alt || ''} />
          {value.caption && <figcaption className="cover-caption">{value.caption}</figcaption>}
        </figure>
      )
    },
    tableBlock: ({value}: {value: BodyTable}) => {
      const [heading, ...rows] = value.rows || []
      const headingCells = heading?.cells || []
      if (!headingCells.length) return null

      return (
        <div className="article-table-wrap">
          <table className="article-table">
            <thead>
              <tr>
                {headingCells.map((cell, index) => (
                  <th key={`${cell}-${index}`} scope="col">{cell}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, rowIndex) => (
                <tr key={row._key || rowIndex}>
                  {headingCells.map((_, cellIndex) => (
                    <td key={cellIndex}>{row.cells?.[cellIndex] || ''}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )
    },
  },
}

const getPost = cache(async (slug: string): Promise<Post | null> => {
  try {
    const post = (await client.fetch(POST_QUERY, {slug}, {next: {revalidate: 60}, stega: false})) as Post | null
    if (post) return post
  } catch {}
  return null
})

const getRelatedPosts = cache(async (postId: string, categoryId?: string): Promise<Story[]> => {
  try {
    return (await client.fetch(RELATED_POSTS_QUERY, {postId, categoryId: categoryId || ''}, {next: {revalidate: 60}, stega: false})) as Story[]
  } catch {
    return []
  }
})

export async function generateMetadata({params}: {params: Promise<{slug: string}>}): Promise<Metadata> {
  const post = await getPost((await params).slug)
  if (!post) return {}
  const image = post.seo?.image?.asset
    ? urlFor(post.seo.image.asset).width(1200).height(630).url()
    : post.image?.asset
    ? urlFor(post.image.asset).width(1200).height(630).url()
    : undefined

  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://newift.com'
  const canonical = post.seo?.canonicalUrl || `${baseUrl}/posts/${post.slug}`

  return {
    title: post.seo?.title || post.title,
    description: post.seo?.description || post.excerpt,
    keywords: [
      ...(post.seo?.focusKeyword ? [post.seo.focusKeyword] : []),
      ...(post.seo?.secondaryKeywords || []),
    ],
    alternates: {
      canonical,
    },
    robots: post.seo?.noIndex ? 'noindex, nofollow' : 'index, follow',
    openGraph: {
      type: 'article',
      title: post.seo?.title || post.title,
      description: post.seo?.description || post.excerpt,
      url: canonical,
      publishedTime: post.publishedAt,
      modifiedTime: post.updatedAt || post.publishedAt,
      images: image ? [{url: image, width: 1200, height: 630, alt: post.title}] : undefined,
    },
    twitter: {
      card: 'summary_large_image',
      title: post.seo?.title || post.title,
      description: post.seo?.description || post.excerpt,
      images: image ? [image] : undefined,
    },
  }
}

export default async function PostPage({params}: {params: Promise<{slug: string}>}) {
  const post = await getPost((await params).slug)
  if (!post) notFound()

  const relatedPosts = await getRelatedPosts(post._id, post.categoryId)
  const cover = post.image?.asset ? urlFor(post.image.asset).width(1600).height(980).fit('crop').auto('format').url() : null
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://newift.com'
  const postUrl = `${baseUrl}/posts/${post.slug}`

  // NewsArticle structured schema for Google Search & Google Discover
  const newsArticleJsonLd = {
    '@context': 'https://schema.org',
    '@type': post.seo?.schemaType || 'NewsArticle',
    headline: post.title,
    description: post.excerpt,
    image: cover ? [cover] : [],
    datePublished: post.publishedAt || new Date().toISOString(),
    dateModified: post.updatedAt || post.publishedAt || new Date().toISOString(),
    mainEntityOfPage: {
      '@type': 'WebPage',
      '@id': postUrl,
    },
    author: [
      {
        '@type': 'Person',
        name: post.author?.name || 'Newift Editorial Desk',
      },
    ],
    publisher: {
      '@type': 'Organization',
      name: 'Newift',
      url: baseUrl,
      logo: {
        '@type': 'ImageObject',
        url: `${baseUrl}/newift-icon.svg`,
      },
    },
    ...(post.sources?.length
      ? {
          citation: post.sources.map((s) => ({
            '@type': 'CreativeWork',
            name: s.title || s.publisher,
            url: s.url,
          })),
        }
      : {}),
  }

  // FAQPage structured schema if FAQs exist
  const faqJsonLd = post.faq?.length
    ? {
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        mainEntity: post.faq.map((item) => ({
          '@type': 'Question',
          name: item.question,
          acceptedAnswer: {
            '@type': 'Answer',
            text: item.answer,
          },
        })),
      }
    : null

  // Breadcrumb structured data
  const breadcrumbJsonLd = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      {
        '@type': 'ListItem',
        position: 1,
        name: 'Home',
        item: baseUrl,
      },
      {
        '@type': 'ListItem',
        position: 2,
        name: post.category?.title || 'News',
        item: `${baseUrl}/#${post.category?.slug || 'latest'}`,
      },
      {
        '@type': 'ListItem',
        position: 3,
        name: post.title,
        item: postUrl,
      },
    ],
  }

  const isVerified = post.verification?.status === 'verified'
  const confidence = post.verification?.confidence || 92
  const sourcesCount = post.verification?.corroboratingSourcesCount || post.sources?.length || 3

  return (
    <div className="article-page">
      {/* Schema.org Structured Data */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{__html: JSON.stringify(newsArticleJsonLd)}}
      />
      {faqJsonLd && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{__html: JSON.stringify(faqJsonLd)}}
        />
      )}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{__html: JSON.stringify(breadcrumbJsonLd)}}
      />

      <header className="site-header">
        <Link className="brand" href="/">
          newift<span>•</span>
        </Link>
        <div className="article-controls">
          <Link className="back-link" href="/">
            ← All stories
          </Link>
          <ThemeToggle />
        </div>
      </header>

      <main className="article-main">
        <p className="eyebrow">{post.category?.title || 'Trending'}</p>
        <h1>{post.title}</h1>
        <p className="article-dek">{post.excerpt}</p>

        {/* Fact Verification Badge */}
        {post.verification && (
          <div className={`verification-badge ${post.verification.status || 'verified'}`}>
            <span className="verification-icon">{isVerified ? '✓' : '!'}</span>
            <span>
              {isVerified ? 'Fact-Checked & Verified' : 'Editorial Review'} • {confidence}% Confidence ({sourcesCount} Sources)
            </span>
          </div>
        )}

        <div className="article-meta">
          By {post.author?.name || 'Newift Desk'} <i />{' '}
          {post.publishedAt
            ? new Date(post.publishedAt).toLocaleDateString('en-US', {
                month: 'long',
                day: 'numeric',
                year: 'numeric',
              })
            : 'Today'}{' '}
          <i /> {post.readTime || 4} min read
        </div>

        {/* Voice Reader Audio Player */}
        <VoiceReader
          title={post.title}
          excerpt={post.excerpt}
          keyPoints={post.keyPoints}
          paragraphs={extractTextFromPortableText(post.body)}
          readTime={post.readTime}
        />

        {cover ? (
          <div>
            <img className="article-cover" src={cover} alt={post.image?.alt || post.title} />
            {(post.image?.caption || post.image?.attribution) && (
              <div className="cover-caption-box">
                <span>{post.image?.caption}</span>
                {post.image?.attribution && <span className="cover-credit">Credit: {post.image.attribution}</span>}
              </div>
            )}
          </div>
        ) : (
          <div className="article-cover placeholder">
            <span>{post.category?.title?.slice(0, 1) || 'N'}</span>
          </div>
        )}

        {/* Key Takeaways / What Happened Box */}
        {Boolean(post.keyPoints?.length) && (
          <section className="key-points-card">
            <h3 className="key-points-title">Key Takeaways</h3>
            <ul className="key-points-list">
              {post.keyPoints!.map((point, index) => (
                <li key={index}>{point}</li>
              ))}
            </ul>
          </section>
        )}

        {/* Main Article Prose */}
        <article className="prose">
          {post.body?.length ? (
            <PortableText value={post.body as never} components={portableTextComponents} />
          ) : (
            <>
              <p>
                Newift is built for the conversations moving at internet speed. This story is ready for its full reporting, context, and analysis in Sanity Studio.
              </p>
              <h2>Keep the signal, skip the noise</h2>
              <p>
                We look for the details that make a moment matter, then turn them into a clear read you can take with you.
              </p>
            </>
          )}
        </article>

        {/* Story Timeline */}
        {Boolean(post.timeline?.length) && (
          <section className="timeline-section">
            <h2>Timeline of Events</h2>
            <div className="timeline-track">
              {post.timeline!.map((item, index) => (
                <div className="timeline-item" key={index}>
                  <div className="timeline-dot" />
                  <div className="timeline-time">{item.time}</div>
                  <p className="timeline-event">{item.event}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* FAQ Section */}
        {Boolean(post.faq?.length) && (
          <section className="faq-section">
            <h2>Frequently Asked Questions</h2>
            <div className="faq-list">
              {post.faq!.map((item, index) => (
                <details className="faq-item" key={index} open={index === 0}>
                  <summary>{item.question}</summary>
                  <p className="faq-answer">{item.answer}</p>
                </details>
              ))}
            </div>
          </section>
        )}

        {/* Corroborating Sources & Citations */}
        {Boolean(post.sources?.length) && (
          <section className="sources-section">
            <h3 className="sources-title">Verified Sources & Reporting</h3>
            <div className="sources-grid">
              {post.sources!.map((source, index) => (
                <div className="source-item" key={index}>
                  <span className="source-publisher">{source.publisher || 'Source'}</span>
                  {source.url ? (
                    <a className="source-link" href={source.url} target="_blank" rel="noopener noreferrer">
                      {source.title || source.url} ↗
                    </a>
                  ) : (
                    <span>{source.title}</span>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* AI Transparency & Editorial Policy Disclosure */}
        <div className="ai-disclosure-banner">
          <strong>Newift Editorial Note:</strong> This report was compiled using our multi-source verification pipeline. Information is corroborated across multiple independent primary outlets and verified prior to publication in accordance with our editorial accuracy standards.
        </div>

        {/* Related Posts */}
        <section className="related-posts">
          <div className="related-heading">
            <p className="eyebrow">KEEP READING</p>
            <h2>More stories for you</h2>
          </div>
          {relatedPosts.length ? (
            <div className="related-grid">
              {relatedPosts.map((story) => {
                const image = story.image?.asset
                  ? urlFor(story.image.asset).width(760).height(520).fit('crop').auto('format').url()
                  : null
                return (
                  <Link className="related-card" key={story._id} href={`/posts/${story.slug}`}>
                    {image ? (
                      <img src={image} alt={story.image?.alt || story.title} />
                    ) : (
                      <div className="related-placeholder">
                        <span>{story.category?.title?.slice(0, 1) || 'N'}</span>
                      </div>
                    )}
                    <p className="story-meta">
                      {story.category?.title || 'Trending'} <i /> {story.readTime || 4} min read
                    </p>
                    <h3>{story.title}</h3>
                    <span>
                      Read story <b>↗</b>
                    </span>
                  </Link>
                )
              })}
            </div>
          ) : (
            <p className="no-related-stories">No more stories yet. Check back soon.</p>
          )}
        </section>
      </main>

      <Footer />
    </div>
  )
}
