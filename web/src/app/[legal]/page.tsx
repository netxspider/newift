import type {Metadata} from 'next'
import Link from 'next/link'
import {notFound} from 'next/navigation'
import {Footer} from '@/components/SiteShell'

const pages = {
  about: {title: 'About Newift', intro: 'A clear, quick read on the moments that move the internet.', content: ['Newift is your modern pulse on what’s happening right now. We sift through the noise to bring you fast, easy-to-read updates on the internet’s biggest trending events, viral topics, and breaking stories.', 'We believe a fast update should still feel considered. Our job is to give you the context, clarity, and source-aware reporting that helps you decide what matters.']},
  privacy: {title: 'Privacy Policy', intro: 'How Newift handles the information you share with us.', content: ['Newift collects only the information needed to operate our newsletter and improve the site experience. If you subscribe, we use your email address to deliver the newsletter you requested.', 'We do not sell personal information. You can unsubscribe at any time using the link in every email. For privacy questions, contact hello@newift.com.']},
  terms: {title: 'Terms of Service', intro: 'The straightforward rules for using Newift.', content: ['Newift content is provided for general information and personal use. You may share links to our work, but may not reproduce it in full without permission.', 'We may update the site, its content, and these terms as the publication evolves. Continued use of Newift means you accept the most current version.']},
  'editorial-guidelines': {title: 'Editorial Guidelines', intro: 'Our commitment to speed, accuracy, and clarity.', content: ['We aim to be fast without being careless. Before publishing, we seek reliable sources, distinguish reporting from commentary, and update stories when meaningful new information emerges.', 'Our coverage is chosen for relevance and explained in plain language. When we make a mistake, we correct it openly and promptly.']},
} as const

export async function generateMetadata({params}: {params: Promise<{legal: string}>}): Promise<Metadata> { const page = pages[(await params).legal as keyof typeof pages]; return page ? {title: page.title, description: page.intro} : {} }

export default async function LegalPage({params}: {params: Promise<{legal: string}>}) {
  const page = pages[(await params).legal as keyof typeof pages]
  if (!page) notFound()
  return <div className="legal-page"><header className="site-header"><Link className="brand" href="/">newift<span>•</span></Link><Link className="back-link" href="/">← Home</Link></header><main className="legal-main"><p className="eyebrow">NEWIFT / INFORMATION</p><h1>{page.title}</h1><p className="legal-intro">{page.intro}</p>{page.content.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}</main><Footer /></div>
}
