import type {Metadata} from 'next'
import Link from 'next/link'
import {PortableText} from 'next-sanity'
import {notFound} from 'next/navigation'
import {cache} from 'react'
import {Footer} from '@/components/SiteShell'
import type {Story} from '@/lib/content'
import {client} from '@/sanity/client'
import {urlFor} from '@/sanity/image'
import {POST_QUERY} from '@/sanity/queries'

type Post = Story & {body?: unknown[]; author?: {name?: string; role?: string}; seo?: {title?: string; description?: string; noIndex?: boolean; image?: {asset?: unknown}}}

type BodyImage = {asset?: unknown; alt?: string}
type BodyTable = {rows?: Array<{_key?: string; cells?: string[]}>}

const portableTextComponents = {
  types: {
    image: ({value}: {value: BodyImage}) => {
      if (!value?.asset) return null

      return (
        <figure className="article-body-image">
          <img src={urlFor(value as Parameters<typeof urlFor>[0]).width(1280).auto('format').url()} alt={value.alt || ''} />
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
            <thead><tr>{headingCells.map((cell, index) => <th key={`${cell}-${index}`} scope="col">{cell}</th>)}</tr></thead>
            <tbody>{rows.map((row, rowIndex) => <tr key={row._key || rowIndex}>{headingCells.map((_, cellIndex) => <td key={cellIndex}>{row.cells?.[cellIndex] || ''}</td>)}</tr>)}</tbody>
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

export async function generateMetadata({params}: {params: Promise<{slug: string}>}): Promise<Metadata> {
  const post = await getPost((await params).slug)
  if (!post) return {}
  const image = post.seo?.image?.asset ? urlFor(post.seo.image.asset).width(1200).height(630).url() : undefined
  return {title: post.seo?.title || post.title, description: post.seo?.description || post.excerpt, robots: post.seo?.noIndex ? 'noindex' : undefined, openGraph: image ? {images: [{url: image, width: 1200, height: 630}]} : undefined}
}

export default async function PostPage({params}: {params: Promise<{slug: string}>}) {
  const post = await getPost((await params).slug)
  if (!post) notFound()
  const cover = post.image?.asset ? urlFor(post.image.asset).width(1600).height(980).fit('crop').auto('format').url() : null
  return <div className="article-page"><header className="site-header"><Link className="brand" href="/">newift<span>•</span></Link><Link className="back-link" href="/">← All stories</Link></header><main className="article-main"><p className="eyebrow">{post.category?.title || 'Trending'}</p><h1>{post.title}</h1><p className="article-dek">{post.excerpt}</p><div className="article-meta">By {post.author?.name || 'Newift Desk'} <i /> {post.publishedAt ? new Date(post.publishedAt).toLocaleDateString('en-US', {month: 'long', day: 'numeric', year: 'numeric'}) : 'Today'} <i /> {post.readTime || 4} min read</div>{cover ? <img className="article-cover" src={cover} alt={post.image?.alt || post.title} /> : <div className="article-cover placeholder"><span>{post.category?.title?.slice(0, 1) || 'N'}</span></div>}<article className="prose">{post.body?.length ? <PortableText value={post.body as never} components={portableTextComponents} /> : <><p>Newift is built for the conversations moving at internet speed. This story is ready for its full reporting, context, and analysis in Sanity Studio.</p><h2>Keep the signal, skip the noise</h2><p>We look for the details that make a moment matter, then turn them into a clear read you can take with you. Add the full article in the standalone Newift Studio to replace this preview.</p></>}</article></main><Footer /></div>
}
