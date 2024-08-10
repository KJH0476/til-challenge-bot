// This is the root layout component for your Next.js app.
// Learn more: https://nextjs.org/docs/app/building-your-application/routing/pages-and-layouts#root-layout-required
import { cn } from './lib/utils'
import './global.css'

export default function Layout({ children }) {
    return (
        <html lang="en">
        <body
            className={cn(
                'antialiased',
            )}
        >
        {children}
        </body>
        </html>
    )
}