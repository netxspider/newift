import {client} from '@/sanity/client'
import {RSS_POSTS_QUERY} from '@/sanity/queries'

export async function GET() {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://newift.com'

  let posts: Array<{
    title: string
    excerpt?: string
    slug: string
    publishedAt?: string
    author?: string
    category?: string
  }> = []

  try {
    posts = (await client.fetch(RSS_POSTS_QUERY, {}, {next: {revalidate: 3600}})) || []
  } catch {
    posts = []
  }

  const escapeXml = (unsafe: string = '') =>
    unsafe
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&apos;')

  const itemsXml = posts
    .map((post) => {
      const postUrl = `${baseUrl}/posts/${post.slug}`
      const pubDate = post.publishedAt
        ? new Date(post.publishedAt).toUTCString()
        : new Date().toUTCString()

      return `
    <item>
      <title>${escapeXml(post.title)}</title>
      <link>${postUrl}</link>
      <guid isPermaLink="true">${postUrl}</guid>
      <description>${escapeXml(post.excerpt || post.title)}</description>
      <pubDate>${pubDate}</pubDate>
      ${post.category ? `<category>${escapeXml(post.category)}</category>` : ''}
      ${post.author ? `<author>${escapeXml(post.author)}</author>` : ''}
    </item>`
    })
    .join('')

  const rssFeed = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Newift — What’s trending now, delivered swift.</title>
    <link>${baseUrl}</link>
    <description>Fast, easy-to-read coverage of trending stories, viral events, technology, and breaking updates.</description>
    <language>en-us</language>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    <atom:link href="${baseUrl}/rss.xml" rel="self" type="application/rss+xml"/>
    ${itemsXml}
  </channel>
</rss>`

  return new Response(rssFeed, {
    headers: {
      'Content-Type': 'application/xml; charset=utf-8',
      'Cache-Control': 's-maxage=3600, stale-while-revalidate',
    },
  })
}
