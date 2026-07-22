import {DocumentTextIcon} from '@sanity/icons'
import {defineArrayMember, defineField, defineType} from 'sanity'

export const tableBlockType = defineType({
  name: 'tableBlock',
  title: 'Table',
  type: 'object',
  icon: DocumentTextIcon,
  fields: [
    defineField({
      name: 'rows',
      title: 'Rows',
      type: 'array',
      initialValue: [
        {cells: ['Column 1', 'Column 2']},
        {cells: ['Value 1', 'Value 2']},
      ],
      of: [
        defineArrayMember({
          name: 'tableRow',
          title: 'Row',
          type: 'object',
          fields: [
            defineField({
              name: 'cells',
              title: 'Cells',
              type: 'array',
              of: [defineArrayMember({type: 'string'})],
              validation: (Rule) => Rule.required().min(1),
            }),
          ],
          preview: {
            select: {firstCell: 'cells.0'},
            prepare({firstCell}) {
              return {title: firstCell || 'Empty row'}
            },
          },
        }),
      ],
      validation: (Rule) => Rule.required().min(2),
    }),
  ],
  preview: {
    select: {rows: 'rows'},
    prepare({rows}) {
      return {title: 'Table', subtitle: `${Array.isArray(rows) ? rows.length : 0} rows`}
    },
  },
})
