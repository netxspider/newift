import {TagIcon} from '@sanity/icons/Tag'
import {defineField, defineType} from 'sanity'

export const categoryType = defineType({
  name: 'category',
  title: 'Category',
  type: 'document',
  icon: TagIcon,
  fields: [
    defineField({
      name: 'title',
      type: 'string',
      options: {
        list: [
          {title: 'Global', value: 'Global'},
          {title: 'Tech', value: 'Tech'},
          {title: 'Entertainment', value: 'Entertainment'},
        ],
        layout: 'radio',
      },
      validation: (Rule) => Rule.required(),
    }),
    defineField({
      name: 'slug',
      type: 'slug',
      options: {source: 'title', maxLength: 96},
      validation: (Rule) => Rule.required(),
    }),
    defineField({name: 'description', type: 'text', rows: 3}),
  ],
  preview: {select: {title: 'title'}},
})
