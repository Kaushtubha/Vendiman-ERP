import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Package,
  DollarSign,
  TrendingUp,
  AlertTriangle,
  FileSpreadsheet,
  Receipt,
  ArrowUpRight,
  ArrowDownRight,
  Sparkles,
  Layers,
  Clock,
  PlusCircle,
  Upload,
} from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
  AreaChart,
  Area,
} from 'recharts'
import apiClient from '@/api/client'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

const COLORS = ['#6366F1', '#10B981', '#F59E0B', '#EC4899', '#8B5CF6', '#06B6D4']

export default function DashboardPage() {
  const [kpis, setKpis] = useState({
    total_products: 18,
    total_suppliers: 6,
    total_stock_value: 48500.0,
    total_retail_value: 72800.0,
    potential_profit: 24300.0,
    low_stock_count: 4,
    total_purchase_orders: 8,
  })

  const [slotProfits, setSlotProfits] = useState([
    { name: 'Red Bull 250ml', slot: 'A1', cost: 75, selling: 125, profit: 50, margin: 40.0, stock: 24 },
    { name: 'Coca Cola 300ml', slot: 'A2', cost: 25, selling: 40, profit: 15, margin: 37.5, stock: 32 },
    { name: 'Doritos Nacho 50g', slot: 'B1', cost: 30, selling: 50, profit: 20, margin: 40.0, stock: 18 },
    { name: 'Snickers Bar 50g', slot: 'B2', cost: 32, selling: 50, profit: 18, margin: 36.0, stock: 8 },
    { name: 'Paper Boat Mango', slot: 'C1', cost: 20, selling: 35, profit: 15, margin: 42.8, stock: 14 },
    { name: 'Lays Classic 50g', slot: 'C2', cost: 12, selling: 20, profit: 8, margin: 40.0, stock: 4 },
  ])

  const [categoryData, setCategoryData] = useState([
    { name: 'Beverages', value: 45 },
    { name: 'Chips & Snacks', value: 30 },
    { name: 'Chocolates & Bars', value: 15 },
    { name: 'Healthy & Nuts', value: 10 },
  ])

  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      try {
        const [kpiRes, profitRes] = await Promise.all([
          apiClient.get('/analytics/kpis'),
          apiClient.get('/analytics/profit-per-slot'),
        ])
        if (kpiRes.data?.data) setKpis(kpiRes.data.data)
        if (profitRes.data?.data?.length) {
          setSlotProfits(
            profitRes.data.data.map((p: any) => ({
              name: p.name,
              slot: p.sku.slice(-2),
              cost: p.cost_price,
              selling: p.selling_price,
              profit: p.unit_profit,
              margin: p.margin_percent,
              stock: p.stock_on_hand,
            }))
          )
        }
      } catch (err) {
        console.log('Using simulated dashboard datasets')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  return (
    <div className="space-y-6">
      {/* ── Top Bar / Welcome ── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            Vending Operations Dashboard
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-500 border border-indigo-500/20 font-medium">
              Vending Fleet #1
            </span>
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Real-time stock valuation, slot profitability & replenishment alerts
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link to="/purchase-orders">
            <Button size="sm" className="gap-1.5 shadow-sm">
              <PlusCircle className="h-4 w-4" />
              New Purchase Order
            </Button>
          </Link>
          <Link to="/upload">
            <Button variant="outline" size="sm" className="gap-1.5">
              <Upload className="h-4 w-4" />
              Excel Sync
            </Button>
          </Link>
        </div>
      </div>

      {/* ── KPI Stat Cards ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Stock Asset Value */}
        <Card className="bg-card border-border shadow-sm hover:shadow transition-all">
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Total Stock Valuation
              </span>
              <div className="h-8 w-8 rounded-lg bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
                <DollarSign className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-bold tracking-tight">
                ₹{kpis.total_stock_value.toLocaleString('en-IN')}
              </div>
              <div className="flex items-center gap-1.5 mt-1 text-xs text-emerald-600 dark:text-emerald-400 font-medium">
                <ArrowUpRight className="h-3.5 w-3.5" />
                <span>Retail Value: ₹{kpis.total_retail_value.toLocaleString('en-IN')}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Estimated Profit Margin */}
        <Card className="bg-card border-border shadow-sm hover:shadow transition-all">
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Potential Slot Profit
              </span>
              <div className="h-8 w-8 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
                <TrendingUp className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-bold tracking-tight text-emerald-600 dark:text-emerald-400">
                ₹{kpis.potential_profit.toLocaleString('en-IN')}
              </div>
              <div className="flex items-center gap-1.5 mt-1 text-xs text-muted-foreground font-medium">
                <span>Avg. Gross Margin: 38.5%</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Active Products / Slots */}
        <Card className="bg-card border-border shadow-sm hover:shadow transition-all">
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Active Catalog SKUs
              </span>
              <div className="h-8 w-8 rounded-lg bg-violet-500/10 text-violet-600 dark:text-violet-400 flex items-center justify-center">
                <Package className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-bold tracking-tight">
                {kpis.total_products} Products
              </div>
              <div className="flex items-center gap-1.5 mt-1 text-xs text-muted-foreground font-medium">
                <span>From {kpis.total_suppliers} Verified Suppliers</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Critical Alerts */}
        <Card className="bg-card border-border shadow-sm hover:shadow transition-all border-amber-500/20 bg-amber-500/5">
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-amber-600 dark:text-amber-400 uppercase tracking-wider">
                Low Stock Thresholds
              </span>
              <div className="h-8 w-8 rounded-lg bg-amber-500/20 text-amber-600 dark:text-amber-400 flex items-center justify-center">
                <AlertTriangle className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-bold tracking-tight text-amber-600 dark:text-amber-400">
                {kpis.low_stock_count} Slots Low
              </div>
              <Link
                to="/alerts"
                className="flex items-center gap-1 mt-1 text-xs text-amber-600 dark:text-amber-400 font-semibold hover:underline"
              >
                <span>Trigger PO Replenishment →</span>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ── Charts Grid ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Slot Profitability Analysis Chart */}
        <Card className="lg:col-span-2 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div>
              <CardTitle className="text-sm font-bold">Slot Profitability & Unit Margins</CardTitle>
              <CardDescription className="text-xs">
                Selling Price vs Purchase Cost (₹ per unit) across high-velocity slots
              </CardDescription>
            </div>
            <Link to="/profitability">
              <Button variant="ghost" size="sm" className="text-xs h-7">
                Detailed Analysis
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="pt-4">
            <div className="h-[280px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={slotProfits} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} angle={-15} textAnchor="end" height={45} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      borderColor: 'hsl(var(--border))',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                  />
                  <Bar dataKey="cost" name="Cost Price (₹)" fill="#64748B" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="profit" name="Profit Margin (₹)" fill="#10B981" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Category Share Donut */}
        <Card className="shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-bold">Category Distribution</CardTitle>
            <CardDescription className="text-xs">Inventory volume by category slab</CardDescription>
          </CardHeader>
          <CardContent className="pt-2">
            <div className="h-[230px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={categoryData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {categoryData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      borderColor: 'hsl(var(--border))',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                  />
                  <Legend verticalAlign="bottom" height={36} wrapperStyle={{ fontSize: '11px' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ── Low Stock Action Table ── */}
      <Card className="shadow-sm">
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <div>
            <CardTitle className="text-sm font-bold flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              Critical Replenishment Watchlist
            </CardTitle>
            <CardDescription className="text-xs">
              Vending slots running below threshold that require immediate PO generation
            </CardDescription>
          </div>
          <Link to="/purchase-orders">
            <Button size="sm" variant="outline" className="text-xs h-8">
              Auto-Generate PO
            </Button>
          </Link>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border border-border overflow-hidden">
            <table className="w-full text-xs">
              <thead className="bg-muted/40 border-b border-border text-muted-foreground text-left">
                <tr>
                  <th className="p-3 font-semibold">SKU & Product</th>
                  <th className="p-3 font-semibold">Slot</th>
                  <th className="p-3 font-semibold">On-Hand</th>
                  <th className="p-3 font-semibold">Reorder Point</th>
                  <th className="p-3 font-semibold">Suggested Reorder</th>
                  <th className="p-3 font-semibold">Status</th>
                  <th className="p-3 font-semibold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {slotProfits.filter((s) => s.stock <= 10).map((item, idx) => (
                  <tr key={idx} className="hover:bg-muted/20">
                    <td className="p-3 font-medium text-foreground">{item.name}</td>
                    <td className="p-3 font-mono font-bold text-indigo-500">{item.slot}</td>
                    <td className="p-3 font-bold text-amber-600 dark:text-amber-400">
                      {item.stock} units
                    </td>
                    <td className="p-3 text-muted-foreground">10 units</td>
                    <td className="p-3 font-semibold text-foreground">+50 units</td>
                    <td className="p-3">
                      <Badge variant="warning">Low Stock</Badge>
                    </td>
                    <td className="p-3 text-right">
                      <Link to="/purchase-orders">
                        <Button size="sm" variant="ghost" className="h-7 text-xs text-primary">
                          Order Now →
                        </Button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
