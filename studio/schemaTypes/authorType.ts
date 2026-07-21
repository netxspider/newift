import {UserIcon} from '@sanity/icons/User'
import {defineField, defineType} from 'sanity'

export const authorType = defineType({
  name: 'author',
  title: 'Author',
  type: 'document',
  icon: UserIcon,
  fields: [
    defineField({name: 'name', type: 'string', validation: (Rule) => Rule.required()}),
    defineField({name: 'role', type: 'string', title: 'Role'}),
    defineField({name: 'image', type: 'image', options: {hotspot: true}}),
    defineField({name: 'bio', type: 'array', of: [{type: 'block'}]}),
  ],
  preview: {select: {title: 'name', subtitle: 'role', media: 'image'}},
})
