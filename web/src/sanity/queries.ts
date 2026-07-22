import {defineQuery} from 'next-sanity'

export const HOME_POSTS_QUERY = defineQuery(`
  *[_type == "post" && defined(slug.current)] | order(publishedAt desc) {
    _id, title, excerpt, publishedAt, readTime, viewCount,
    "slug": slug.current,
    "category": category->{title, "slug": slug.current},
    "author": author->{name},
    "image": coverImage{asset, alt}
  }
`)

export const POST_QUERY = defineQuery(`
  *[_type == "post" && slug.current == $slug][0] {
    _id, title, excerpt, body, publishedAt, readTime, viewCount,
    "slug": slug.current,
    "category": category->{title, "slug": slug.current},
    "author": author->{name, role},
    "image": coverImage{asset, alt},
    "seo": {
      "title": coalesce(seo.title, title, ""),
      "description": coalesce(seo.description, excerpt, ""),
      "image": seo.image,
      "noIndex": seo.noIndex == true
    }
  }
`)

export const SLUGS_QUERY = defineQuery(`
  *[_type == "post" && defined(slug.current)]{ "slug": slug.current }
`)

export const SITEMAP_QUERY = defineQuery(`
  *[_type == "post" && defined(slug.current) && seo.noIndex != true] {
    "href": "/posts/" + slug.current,
    _updatedAt
  }
`)
