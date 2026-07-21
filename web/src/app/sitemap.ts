import type {MetadataRoute} from 'next'
import {client} from '@/sanity/client'
import {SITEMAP_QUERY} from '@/sanity/queries'

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000'
  const staticPages = ['', '/about', '/privacy', '/terms', '/editorial-guidelines'].map((path) => ({url: new URL(path || '/', baseUrl).toString(), lastModified: new Date()}))
  try {
    const posts = (await client.fetch(SITEMAP_QUERY)) as {href: string; _updatedAt: string}[]
    return [...staticPages, ...posts.map((post) => ({url: new URL(post.href, baseUrl).toString(), lastModified: new Date(post._updatedAt), changeFrequency: 'weekly' as const, priority: 0.8}))]
  } catch { return staticPages }
}
