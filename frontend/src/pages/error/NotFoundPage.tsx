export default function NotFoundPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="text-center">
        <div className="text-6xl font-bold text-muted-foreground">404</div>
        <h1 className="mt-4 text-2xl font-bold text-foreground">Page Not Found</h1>
        <p className="mt-2 text-muted-foreground">The page you are looking for does not exist.</p>
        <a href="/dashboard" className="mt-6 inline-block text-primary hover:underline">Return to Dashboard</a>
      </div>
    </div>
  )
}
