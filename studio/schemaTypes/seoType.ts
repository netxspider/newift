import {defineField, defineType} from 'sanity'
import {SearchIcon} from '@sanity/icons/Search'

export const seoType = defineType({
  name: 'seo',
  title: 'SEO',
  type: 'object',
  icon: SearchIcon,
  fields: [
    defineField({name: 'title', title: 'SEO title', type: 'string', validation: (Rule) => Rule.max(70)}),
    defineField({
      name: 'description',
      title: 'SEO description',
      type: 'text',
      rows: 3,
      validation: (Rule) => Rule.max(170),
    }),
    defineField({name: 'focusKeyword', title: 'Focus Keyword', type: 'string'}),
    defineField({
      name: 'secondaryKeywords',
      title: 'Secondary Keywords',
      type: 'array',
      of: [{type: 'string'}],
    }),
    defineField({name: 'canonicalUrl', title: 'Canonical URL', type: 'url'}),
    defineField({
      name: 'schemaType',
      title: 'Structured Data Type',
      type: 'string',
      initialValue: 'NewsArticle',
      options: {
        list: [
          {title: 'NewsArticle', value: 'NewsArticle'},
          {title: 'Article', value: 'Article'},
          {title: 'AnalysisNewsArticle', value: 'AnalysisNewsArticle'},
        ],
      },
    }),
    defineField({
      name: 'image',
      title: 'Social share image',
      type: 'image',
      options: {hotspot: true},
      fields: [defineField({name: 'alt', type: 'string', title: 'Alternative text'})],
    }),
    defineField({name: 'noIndex', type: 'boolean', title: 'Hide from search engines', initialValue: false}),
  ],
})
