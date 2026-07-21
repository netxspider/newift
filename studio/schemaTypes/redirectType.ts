import {LinkIcon} from '@sanity/icons/Link'
import {defineField, defineType} from 'sanity'

export const redirectType = defineType({
  name: 'redirect',
  title: 'Redirect',
  type: 'document',
  icon: LinkIcon,
  fields: [
    defineField({name: 'source', type: 'string', description: 'Starts with /', validation: (Rule) => Rule.required().custom((value) => !value || value.startsWith('/') || 'Must start with /')}),
    defineField({name: 'destination', type: 'string', validation: (Rule) => Rule.required()}),
    defineField({name: 'permanent', type: 'boolean', title: 'Permanent (301)', initialValue: true}),
    defineField({name: 'isEnabled', type: 'boolean', initialValue: true}),
  ],
})
