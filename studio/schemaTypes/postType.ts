import {DocumentTextIcon} from '@sanity/icons/DocumentText'
import {defineArrayMember, defineField, defineType} from 'sanity'

export const postType = defineType({
  name: 'post',
  title: 'Post',
  type: 'document',
  icon: DocumentTextIcon,
  groups: [
    {name: 'content', title: 'Content', default: true},
    {name: 'publishing', title: 'Publishing'},
    {name: 'seo', title: 'SEO'},
  ],
  fields: [
    defineField({name: 'title', type: 'string', group: 'content', validation: (Rule) => Rule.required().max(120)}),
    defineField({
      name: 'slug',
      type: 'slug',
      group: 'publishing',
      options: {source: 'title', maxLength: 96},
      validation: (Rule) => Rule.required(),
    }),
    defineField({name: 'excerpt', type: 'text', rows: 3, group: 'content', validation: (Rule) => Rule.required().max(220)}),
    defineField({
      name: 'coverImage',
      type: 'image',
      title: 'Cover image',
      group: 'content',
      options: {hotspot: true},
      fields: [defineField({name: 'alt', type: 'string', title: 'Alternative text', validation: (Rule) => Rule.required()})],
    }),
    defineField({name: 'author', type: 'reference', to: [{type: 'author'}], group: 'content'}),
    defineField({name: 'category', type: 'reference', to: [{type: 'category'}], group: 'content', validation: (Rule) => Rule.required()}),
    defineField({name: 'publishedAt', type: 'datetime', group: 'publishing', validation: (Rule) => Rule.required()}),
    defineField({name: 'readTime', type: 'number', title: 'Read time (minutes)', group: 'publishing', validation: (Rule) => Rule.min(1).integer()}),
    defineField({name: 'viewCount', type: 'number', title: 'Views', group: 'publishing', initialValue: 0, validation: (Rule) => Rule.min(0).integer()}),
    defineField({
      name: 'isFeatured',
      type: 'boolean',
      title: 'Feature on home page (deprecated)',
      group: 'publishing',
      deprecated: {reason: 'The newest published post is automatically featured on the home page.'},
      readOnly: true,
      hidden: ({value}) => value === undefined,
      initialValue: undefined,
    }),
    defineField({
      name: 'body',
      type: 'array',
      group: 'content',
      of: [
        defineArrayMember({type: 'block', styles: [{title: 'Normal', value: 'normal'}, {title: 'Heading 2', value: 'h2'}, {title: 'Heading 3', value: 'h3'}, {title: 'Quote', value: 'blockquote'}]}),
        defineArrayMember({type: 'image', options: {hotspot: true}, fields: [defineField({name: 'alt', type: 'string', title: 'Alternative text'})]}),
      ],
    }),
    defineField({name: 'seo', type: 'seo', group: 'seo'}),
  ],
  preview: {
    select: {title: 'title', subtitle: 'publishedAt', media: 'coverImage'},
    prepare({title, subtitle, media}) {
      return {title, subtitle: subtitle ? new Date(subtitle).toLocaleDateString() : 'No publish date', media}
    },
  },
  orderings: [
    {title: 'Newest first', name: 'publishedAtDesc', by: [{field: 'publishedAt', direction: 'desc'}]},
    {title: 'Most viewed', name: 'viewCountDesc', by: [{field: 'viewCount', direction: 'desc'}]},
  ],
})
