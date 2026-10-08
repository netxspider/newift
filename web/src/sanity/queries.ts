import {defineQuery} from 'next-sanity'

export const HOME_POSTS_QUERY = defineQuery(`
  *[_type == "post" && defined(slug.current)] | order(publishedAt desc) {
    _id, title, excerpt, publishedAt, readTime, viewCount,
    "slug": slug.current,
    "category": category->{title, "slug": slug.current},
    "author": author->{name},
    "image": coverImage{asset, alt, caption, attribution},
    "verification": verification{status, confidence},
    "story": story{trendScore}
  }
`)

export const POST_QUERY = defineQuery(`
  *[_type == "post" && slug.current == $slug][0] {
    _id, title, excerpt, body, publishedAt, updatedAt, readTime, viewCount,
    "slug": slug.current,
    "categoryId": category._ref,
    "category": category->{title, "slug": slug.current},
    "author": author->{name, role},
    "image": coverImage{asset, alt, caption, attribution, sourceUrl},
    keyPoints,
    timeline[]{time, event},
    faq[]{question, answer},
    sources[]{publisher, title, url, publishedAt, isPrimary},
    verification{status, confidence, factCheckedAt, corroboratingSourcesCount, notes},
    aiDisclosure{isAiAssisted, model, editorialRole, humanReviewed},
    story{storyClusterId, trendScore, trendVelocity, firstDetectedAt},
    "seo": {
      "title": coalesce(seo.title, title, ""),
      "description": coalesce(seo.description, excerpt, ""),
      "image": seo.image,
      "focusKeyword": seo.focusKeyword,
      "secondaryKeywords": seo.secondaryKeywords,
      "canonicalUrl": seo.canonicalUrl,
      "schemaType": coalesce(seo.schemaType, "NewsArticle"),
      "noIndex": seo.noIndex == true
    }
  }
`)

export const RELATED_POSTS_QUERY = defineQuery(`
  *[_type == "post" && defined(slug.current) && _id != $postId]
  | order((category._ref == $categoryId) desc, publishedAt desc)[0...3] {
    _id, title, excerpt, publishedAt, readTime,
    "slug": slug.current,
    "category": category->{title, "slug": slug.current},
    "image": coverImage{asset, alt}
  }
`)

export const SLUGS_QUERY = defineQuery(`
  *[_type == "post" && defined(slug.current)]{ "slug": slug.current }
`)

export const SITEMAP_QUERY = defineQuery(`
  *[_type == "post" && defined(slug.current) && seo.noIndex != true] {
    "href": "/posts/" + slug.current,
    _updatedAt,
    publishedAt
  }
`)

export const NEWS_SITEMAP_QUERY = defineQuery(`
  *[_type == "post" && defined(slug.current) && seo.noIndex != true] | order(publishedAt desc)[0...50] {
    title,
    "slug": slug.current,
    publishedAt,
    _updatedAt,
    "category": category->title
  }
`)

export const RSS_POSTS_QUERY = defineQuery(`
  *[_type == "post" && defined(slug.current) && seo.noIndex != true] | order(publishedAt desc)[0...30] {
    title,
    excerpt,
    "slug": slug.current,
    publishedAt,
    "author": author->name,
    "category": category->title
  }
`)
