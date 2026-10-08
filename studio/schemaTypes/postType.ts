import {DocumentTextIcon} from '@sanity/icons/DocumentText'
import {defineArrayMember, defineField, defineType} from 'sanity'

export const postType = defineType({
  name: 'post',
  title: 'Post',
  type: 'document',
  icon: DocumentTextIcon,
  groups: [
    {name: 'content', title: 'Content', default: true},
    {name: 'editorial', title: 'Editorial & Sources'},
    {name: 'seo', title: 'SEO & Schema'},
    {name: 'intelligence', title: 'Trend & Verification'},
    {name: 'publishing', title: 'Publishing'},
  ],
  fields: [
    defineField({name: 'title', type: 'string', group: 'content', validation: (Rule) => Rule.required().max(140)}),
    defineField({
      name: 'slug',
      type: 'slug',
      group: 'publishing',
      options: {source: 'title', maxLength: 96},
      validation: (Rule) => Rule.required(),
    }),
    defineField({name: 'excerpt', type: 'text', rows: 3, group: 'content', validation: (Rule) => Rule.required().max(260)}),
    defineField({
      name: 'coverImage',
      type: 'image',
      title: 'Cover image',
      group: 'content',
      options: {hotspot: true},
      fields: [
        defineField({name: 'alt', type: 'string', title: 'Alternative text', validation: (Rule) => Rule.required()}),
        defineField({name: 'caption', type: 'string', title: 'Caption'}),
        defineField({name: 'attribution', type: 'string', title: 'Image Attribution / Credit'}),
        defineField({name: 'sourceUrl', type: 'url', title: 'Source URL'}),
      ],
    }),
    defineField({name: 'author', type: 'reference', to: [{type: 'author'}], group: 'content'}),
    defineField({name: 'category', type: 'reference', to: [{type: 'category'}], group: 'content', validation: (Rule) => Rule.required()}),
    defineField({name: 'publishedAt', type: 'datetime', group: 'publishing', validation: (Rule) => Rule.required()}),
    defineField({name: 'updatedAt', type: 'datetime', group: 'publishing'}),
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

    // Key points & Takeaways
    defineField({
      name: 'keyPoints',
      title: 'Key Points / What Happened',
      description: 'Bullet points highlighting core verified takeaways for fast reading',
      type: 'array',
      group: 'editorial',
      of: [defineArrayMember({type: 'string'})],
    }),

    // Structured Timeline
    defineField({
      name: 'timeline',
      title: 'Story Timeline',
      description: 'Chronological timeline of events leading up to this story',
      type: 'array',
      group: 'editorial',
      of: [
        defineArrayMember({
          type: 'object',
          fields: [
            defineField({name: 'time', title: 'Time / Date', type: 'string'}),
            defineField({name: 'event', title: 'Event Description', type: 'text', rows: 2}),
          ],
          preview: {
            select: {title: 'time', subtitle: 'event'},
          },
        }),
      ],
    }),

    // FAQ Section
    defineField({
      name: 'faq',
      title: 'Frequently Asked Questions (FAQ)',
      description: 'Common reader questions and verified answers (rendered as FAQPage schema)',
      type: 'array',
      group: 'editorial',
      of: [
        defineArrayMember({
          type: 'object',
          fields: [
            defineField({name: 'question', title: 'Question', type: 'string'}),
            defineField({name: 'answer', title: 'Answer', type: 'text', rows: 3}),
          ],
          preview: {
            select: {title: 'question', subtitle: 'answer'},
          },
        }),
      ],
    }),

    // Sources & Citations
    defineField({
      name: 'sources',
      title: 'Corroborating Sources',
      description: 'Original reporting sources, primary releases, and secondary references',
      type: 'array',
      group: 'editorial',
      of: [
        defineArrayMember({
          type: 'object',
          fields: [
            defineField({name: 'publisher', title: 'Publisher / Outlet', type: 'string'}),
            defineField({name: 'title', title: 'Article Title', type: 'string'}),
            defineField({name: 'url', title: 'URL', type: 'url'}),
            defineField({name: 'publishedAt', title: 'Source Published Date', type: 'string'}),
            defineField({name: 'isPrimary', title: 'Primary Source', type: 'boolean', initialValue: false}),
          ],
          preview: {
            select: {title: 'publisher', subtitle: 'title'},
          },
        }),
      ],
    }),

    // Story Intelligence & Cluster Tracking
    defineField({
      name: 'story',
      title: 'Trend Intelligence Metadata',
      type: 'object',
      group: 'intelligence',
      fields: [
        defineField({name: 'storyClusterId', title: 'Story Cluster ID', type: 'string'}),
        defineField({name: 'trendScore', title: 'Trend Score (0-100)', type: 'number'}),
        defineField({name: 'trendVelocity', title: 'Search / Trend Velocity', type: 'number'}),
        defineField({name: 'firstDetectedAt', title: 'First Detected At', type: 'datetime'}),
        defineField({name: 'contentHash', title: 'Content Hash', type: 'string'}),
      ],
    }),

    // Fact Verification & Quality Gate Record
    defineField({
      name: 'verification',
      title: 'Verification & Quality Gate',
      type: 'object',
      group: 'intelligence',
      fields: [
        defineField({
          name: 'status',
          title: 'Verification Status',
          type: 'string',
          initialValue: 'verified',
          options: {
            list: [
              {title: 'Verified', value: 'verified'},
              {title: 'Needs Review', value: 'needs_review'},
              {title: 'Flagged / Speculative', value: 'flagged'},
            ],
          },
        }),
        defineField({name: 'confidence', title: 'Fact Confidence Score (0-100)', type: 'number'}),
        defineField({name: 'factCheckedAt', title: 'Fact Checked At', type: 'datetime'}),
        defineField({name: 'corroboratingSourcesCount', title: 'Corroborating Sources Count', type: 'number'}),
        defineField({name: 'notes', title: 'Verification Notes / Evidence', type: 'text', rows: 3}),
      ],
    }),

    // AI Disclosure & Editorial Transparency
    defineField({
      name: 'aiDisclosure',
      title: 'AI Disclosure & Editorial Transparency',
      type: 'object',
      group: 'intelligence',
      fields: [
        defineField({name: 'isAiAssisted', title: 'AI-Assisted Drafting', type: 'boolean', initialValue: true}),
        defineField({name: 'model', title: 'Model Name / Version', type: 'string'}),
        defineField({name: 'editorialRole', title: 'Editorial Role', type: 'string', initialValue: 'Research synthesis and initial draft under Newift quality gate'}),
        defineField({name: 'humanReviewed', title: 'Human Reviewed', type: 'boolean', initialValue: false}),
      ],
    }),

    // Related Articles references
    defineField({
      name: 'relatedArticles',
      title: 'Related Stories',
      type: 'array',
      group: 'editorial',
      of: [defineArrayMember({type: 'reference', to: [{type: 'post'}]})],
    }),

    // Portable Text Body
    defineField({
      name: 'body',
      type: 'array',
      group: 'content',
      of: [
        defineArrayMember({
          type: 'block',
          styles: [
            {title: 'Normal', value: 'normal'},
            {title: 'Heading 2', value: 'h2'},
            {title: 'Heading 3', value: 'h3'},
            {title: 'Quote', value: 'blockquote'},
          ],
        }),
        defineArrayMember({
          type: 'image',
          options: {hotspot: true},
          fields: [
            defineField({name: 'alt', type: 'string', title: 'Alternative text'}),
            defineField({name: 'caption', type: 'string', title: 'Caption'}),
          ],
        }),
        defineArrayMember({type: 'tableBlock'}),
      ],
    }),

    // SEO Object
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
    {title: 'Highest Trend Score', name: 'trendScoreDesc', by: [{field: 'story.trendScore', direction: 'desc'}]},
    {title: 'Most viewed', name: 'viewCountDesc', by: [{field: 'viewCount', direction: 'desc'}]},
  ],
})
