import React from 'react'
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Package,
  Truck,
  FileSpreadsheet,
  Receipt,
  Warehouse,
  TrendingUp,
  AlertTriangle,
  Upload,
  LogOut,
  Moon,
  Sun,
  Bell,
  Search,
  CheckCircle2,
} from 'lucide-react'
import { useAuthStore } from '@/stores/auth.store'
import { useUIStore } from '@/stores/ui.store'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

const navItems = [
  { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { name: 'Products', path: '/products', icon: Package },
  { name: 'Suppliers', path: '/suppliers', icon: Truck },
  { name: 'Purchase Orders', path: '/purchase-orders', icon: FileSpreadsheet },
  { name: 'GRN', path: '/grn', icon: Receipt },
  { name: 'Delivery Challans (DC)', path: '/dc', icon: Truck },
  { name: 'Inventory', path: '/inventory', icon: Warehouse },
  { name: 'Profitability', path: '/profitability', icon: TrendingUp },
  { name: 'Alerts', path: '/alerts', icon: AlertTriangle, badge: 'Live' },
  { name: 'Upload Data', path: '/upload', icon: Upload },
]

export default function AppLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()
  const { theme, toggleTheme } = useUIStore()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen w-full bg-background text-foreground overflow-hidden">
      {/* ── Sidebar ── */}
      <aside className="w-64 bg-card border-r border-border flex flex-col shrink-0">
        {/* Brand */}
        <div className="h-16 flex items-center px-6 border-b border-border gap-3">
          <div className="h-9 w-9 rounded-lg bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center text-white font-bold shadow-md shadow-indigo-500/20">
            V
          </div>
          <div>
            <div className="font-bold text-sm tracking-tight bg-gradient-to-r from-foreground to-foreground/80 bg-clip-text">
              Vendiman ERP
            </div>
            <div className="text-[11px] text-muted-foreground font-medium">
              Vending Operations Hub
            </div>
          </div>
        </div>

        {/* Navigation items */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          <div className="px-3 pb-2 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
            Operational Modules
          </div>
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.path
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={`flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-primary text-primary-foreground font-semibold shadow-sm shadow-primary/20'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className="h-4 w-4 shrink-0" />
                  <span>{item.name}</span>
                </div>
                {item.badge && (
                  <span className="px-1.5 py-0.5 rounded-full text-[9px] font-bold bg-amber-500/20 text-amber-500 border border-amber-500/30">
                    {item.badge}
                  </span>
                )}
              </NavLink>
            )
          })}
        </nav>

        {/* User Card */}
        <div className="p-3 border-t border-border bg-muted/20">
          <div className="flex items-center justify-between p-2 rounded-lg bg-card border border-border">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="h-8 w-8 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-primary font-semibold text-xs">
                {user?.full_name?.charAt(0) || 'U'}
              </div>
              <div className="min-w-0">
                <p className="text-xs font-semibold truncate leading-tight">
                  {user?.full_name || 'Admin User'}
                </p>
                <p className="text-[10px] text-muted-foreground truncate uppercase font-medium">
                  {user?.role || 'Admin'}
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 text-muted-foreground hover:text-destructive"
              onClick={handleLogout}
              title="Logout"
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </aside>

      {/* ── Main Area ── */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Header */}
        <header className="h-16 border-b border-border bg-card/60 backdrop-blur-md px-6 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-4">
            <div className="relative w-64 md:w-80">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search products, orders, slots..."
                className="w-full bg-muted/50 border border-input rounded-md pl-9 pr-4 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-primary text-foreground"
              />
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs font-medium">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>Live API Connected</span>
            </div>

            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-muted-foreground"
              onClick={toggleTheme}
              title="Toggle theme"
            >
              {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </Button>

            <NavLink to="/alerts">
              <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground relative">
                <Bell className="h-4 w-4" />
                <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-destructive" />
              </Button>
            </NavLink>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-6 bg-background/50">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
