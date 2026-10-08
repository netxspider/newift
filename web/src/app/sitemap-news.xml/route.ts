import {client} from '@/sanity/client'
import {NEWS_SITEMAP_QUERY} from '@/sanity/queries'

export async function GET() {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://newift.com'

  let posts: Array<{
    title: string
    slug: string
    publishedAt?: string
    _updatedAt?: string
    category?: string
  }> = []

  try {
    posts = (await client.fetch(NEWS_SITEMAP_QUERY, {}, {next: {revalidate: 1800}})) || []
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

  const urlsXml = posts
    .map((post) => {
      const postUrl = `${baseUrl}/posts/${post.slug}`
      const pubDate = post.publishedAt
        ? new Date(post.publishedAt).toISOString()
        : new Date().toISOString()

      return `
  <url>
    <loc>${postUrl}</loc>
    <news:news>
      <news:publication>
        <news:name>Newift</news:name>
        <news:language>en</news:language>
      </news:publication>
      <news:publication_date>${pubDate}</news:publication_date>
      <news:title>${escapeXml(post.title)}</news:title>
    </news:news>
  </url>`
    })
    .join('')

  const newsSitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
  ${urlsXml}
</urlset>`

  return new Response(newsSitemap, {
    headers: {
      'Content-Type': 'application/xml; charset=utf-8',
      'Cache-Control': 's-maxage=1800, stale-while-revalidate',
    },
  })
}
