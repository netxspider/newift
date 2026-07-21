import Link from 'next/link'

export function Footer() {
  return (
    <footer className="footer-shell">
      <div className="footer-grid">
        <div>
          <Link className="brand brand-footer" href="/">newift<span>•</span></Link>
          <p>Welcome to Newift—your modern pulse on what’s happening right now. We sift through the noise to bring you fast, easy-to-read updates on the internet&apos;s biggest trending events, viral topics, and breaking stories.</p>
        </div>
        <div className="footer-links"><p className="eyebrow">Explore</p><Link href="/">Home</Link><Link href="/#latest">Trending posts</Link><Link href="mailto:hello@newift.com">Contact us</Link></div>
        <div className="footer-links"><p className="eyebrow">Company</p><Link href="/about">About us</Link><Link href="/privacy">Privacy policy</Link><Link href="/terms">Terms of service</Link><Link href="/editorial-guidelines">Editorial guidelines</Link></div>
        <div className="footer-links"><p className="eyebrow">Follow</p><a href="https://x.com" aria-label="Follow Newift on X">𝕏&nbsp; X / Twitter</a><a href="https://www.reddit.com" aria-label="Follow Newift on Reddit">●&nbsp; Reddit</a></div>
      </div>
      <div className="footer-base"><span>© 2026 Newift. All rights reserved.</span><span>Made for the moment.</span></div>
    </footer>
  )
}
