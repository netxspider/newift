import {client} from '@/sanity/client'
import {HOME_POSTS_QUERY} from '@/sanity/queries'
import {urlFor} from '@/sanity/image'

export type Story = {
  _id: string
  title: string
  excerpt: string
  slug: string
  publishedAt?: string
  readTime?: number
  viewCount?: number
  category?: {title?: string; slug?: string}
  author?: {name?: string}
  image?: {asset?: unknown; alt?: string}
  imageUrl?: string
}

export async function getHomeStories(): Promise<Story[]> {
  try {
    const posts = (await client.fetch(HOME_POSTS_QUERY, {}, {next: {revalidate: 60}})) as Story[]
    if (!posts?.length) return []
    return posts.map((post) => ({
      ...post,
      imageUrl: post.image?.asset ? urlFor(post.image.asset).width(1200).height(800).fit('crop').auto('format').url() : undefined,
    }))
  } catch {
    return []
  }
}
