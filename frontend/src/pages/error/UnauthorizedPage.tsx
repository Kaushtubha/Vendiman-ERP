export default function UnauthorizedPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="text-center">
        <div className="text-6xl font-bold text-danger">403</div>
        <h1 className="mt-4 text-2xl font-bold text-foreground">Access Denied</h1>
        <p className="mt-2 text-muted-foreground">You don't have permission to view this page.</p>
        <a href="/dashboard" className="mt-6 inline-block text-primary hover:underline">Return to Dashboard</a>
      </div>
    </div>
  )
}
