import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Warehouse,
  TrendingUp,
  AlertTriangle,
  ArrowUpRight,
  ArrowDownRight,
  Package,
  Clock,
  PlusCircle,
  Activity,
  Cpu,
  ShieldAlert,
  FileSpreadsheet,
  RotateCcw,
  Trash2,
  Mail,
  Bell,
  CheckCircle2,
  XCircle,
  Truck,
  MessageSquare,
  Sparkles,
  Barcode,
  Send,
} from 'lucide-react'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import apiClient from '@/api/client'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

// ── Simulated Data (replaced by API when available) ──────────────────────────

const DEFAULT_STOCK_BREAKDOWN = {
  main_wh: 420,
  sub_wh: 280,
  machine: 156,
  total: 856,
}

const DEFAULT_SALES_30D = {
  total_sales: 2340,
  payment_success: 2185,
  avg_daily_run_rate: 72.8,
  run_rate_trend: 'up' as 'up' | 'down',
  trend_percent: 8.5,
}

const DEFAULT_MACHINE_FLEET = {
  total_machines: 12,
  refilled: 9,
  not_refilled: 3,
  refilled_percent: 75,
  not_refilled_percent: 25,
}

const DEFAULT_AVAILABILITY_ALERTS = [
  { name: 'Lays Classic Salted 50g', sku: 'SNK-LAY-50', machine: 'VM-04', availability: 25, slot: 'B3' },
  { name: 'Snickers Bar 50g', sku: 'CHO-SNK-50', machine: 'VM-07', availability: 38, slot: 'A2' },
  { name: 'Coca Cola 300ml', sku: 'BEV-CC-300', machine: 'VM-02', availability: 45, slot: 'C1' },
]

const DEFAULT_PO_TRACKER = {
  generated: 14,
  ordered: 11,
  mismatch: 3,
  pending_approval: 2,
  last_po_date: '2026-08-17',
}

const DEFAULT_EXPIRING_STOCK = [
  { name: 'Paper Boat Mango 250ml', sku: 'BEV-PB-250', batch: 'BATCH-PB-0426', expiry: '2026-08-30', days_left: 11, qty: 14 },
  { name: 'Doritos Cheese 50g', sku: 'SNK-DOR-50', batch: 'BATCH-DOR-0326', expiry: '2026-09-15', days_left: 27, qty: 18 },
  { name: 'Protein Bar 40g', sku: 'SNK-PRO-40', batch: 'BATCH-PRO-0726', expiry: '2026-09-05', days_left: 17, qty: 8 },
]

const DEFAULT_DAMAGE_STOCK = {
  total_damaged: 12,
  total_stock: 856,
  damage_percent: 1.4,
  vendor_agreed_percent: 5,
  items: [
    { name: 'Red Bull 250ml', sku: 'BEV-RB-250', qty: 3, reason: 'Dented cans' },
    { name: 'Lays Classic 50g', sku: 'SNK-LAY-50', qty: 5, reason: 'Packet torn' },
    { name: 'KitKat 37g', sku: 'CHO-KK-37', qty: 4, reason: 'Melted/Deformed' },
  ],
}

// Photos 6 & 7: In-Transit & Sub-WH Out of stock auto DC
const DEFAULT_IN_TRANSIT = {
  active_transits: 3,
  lost_in_transit_pct: 0,
  sync_mismatches_today: 1, // 4-times daily sync
  auto_dc_suggestions: [
    { item: 'Lays Classic 50g', target: 'Sub-WH Whitefield (0 left)', source: 'Sub-WH Koramangala (45 surplus)', qty: 40 },
    { item: 'Snickers 50g', target: 'Sub-WH Indiranagar (0 left)', source: 'Main Dark Store (120 surplus)', qty: 30 },
  ],
}

const DEFAULT_DAILY_RUN_RATE = [
  { date: 'Aug 01', sales: 58, run_rate: 58 },
  { date: 'Aug 03', sales: 65, run_rate: 61 },
  { date: 'Aug 05', sales: 72, run_rate: 65 },
  { date: 'Aug 07', sales: 55, run_rate: 62 },
  { date: 'Aug 09', sales: 80, run_rate: 66 },
  { date: 'Aug 11', sales: 78, run_rate: 68 },
  { date: 'Aug 13', sales: 82, run_rate: 70 },
  { date: 'Aug 15', sales: 68, run_rate: 70 },
  { date: 'Aug 17', sales: 90, run_rate: 73 },
  { date: 'Aug 19', sales: 85, run_rate: 75 },
]

export default function DashboardPage() {
  const [stockBreakdown, setStockBreakdown] = useState(DEFAULT_STOCK_BREAKDOWN)
  const [sales30d, setSales30d] = useState(DEFAULT_SALES_30D)
  const [machineFleet, setMachineFleet] = useState(DEFAULT_MACHINE_FLEET)
  const [availabilityAlerts, setAvailabilityAlerts] = useState(DEFAULT_AVAILABILITY_ALERTS)
  const [poTracker, setPoTracker] = useState(DEFAULT_PO_TRACKER)
  const [expiringStock, setExpiringStock] = useState(DEFAULT_EXPIRING_STOCK)
  const [damageStock, setDamageStock] = useState(DEFAULT_DAMAGE_STOCK)
  const [inTransit, setInTransit] = useState(DEFAULT_IN_TRANSIT)
  const [dailyRunRate, setDailyRunRate] = useState(DEFAULT_DAILY_RUN_RATE)
  const [whatsappSent, setWhatsappSent] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      try {
        const [stockRes, salesRes] = await Promise.all([
          apiClient.get('/analytics/stock-breakdown'),
          apiClient.get('/analytics/sales-30d'),
        ])
        if (stockRes.data?.data) setStockBreakdown(stockRes.data.data)
        if (salesRes.data?.data) setSales30d(salesRes.data.data)
      } catch (err) {
        console.log('Using simulated dashboard data')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const triggerWhatsApp = () => {
    setWhatsappSent(true)
    setTimeout(() => setWhatsappSent(false), 3500)
  }

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            Operations Dashboard
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-500 border border-indigo-500/20 font-medium">
              Live
            </span>
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Stock levels, sales run rate, automated DC transfers & alerts at a glance
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link to="/dc">
            <Button variant="outline" size="sm" className="gap-1.5 text-xs text-indigo-600 dark:text-indigo-400 border-indigo-500/30">
              <Truck className="h-4 w-4" />
              Delivery Challans (DC)
            </Button>
          </Link>
          <Link to="/purchase-orders">
            <Button size="sm" className="gap-1.5 shadow-sm text-xs">
              <PlusCircle className="h-4 w-4" />
              New PO
            </Button>
          </Link>
          <Link to="/alerts">
            <Button variant="outline" size="sm" className="gap-1.5 text-xs">
              <Bell className="h-4 w-4" />
              Alerts
            </Button>
          </Link>
        </div>
      </div>

      {/* ── Row 1: Stock Breakdown + Sales + Machine Fleet + Availability Alert ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">

        {/* 1. Total Stock Overview (Main WH + Sub WH + Machine) */}
        <Card className="bg-card border-border shadow-sm hover:shadow transition-all">
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Total Stock
              </span>
              <div className="h-8 w-8 rounded-lg bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
                <Warehouse className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-bold tracking-tight">
                {stockBreakdown.total.toLocaleString('en-IN')} units
              </div>
              <div className="mt-2 space-y-1">
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Main WH</span>
                  <span className="font-semibold text-foreground">{stockBreakdown.main_wh}</span>
                </div>
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Sub WH</span>
                  <span className="font-semibold text-foreground">{stockBreakdown.sub_wh}</span>
                </div>
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>In Machines</span>
                  <span className="font-semibold text-foreground">{stockBreakdown.machine}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 2. Last 30 Days Sales & Run Rate */}
        <Card className="bg-card border-border shadow-sm hover:shadow transition-all">
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                30-Day Sales
              </span>
              <div className="h-8 w-8 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
                <TrendingUp className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-bold tracking-tight">
                {sales30d.payment_success.toLocaleString('en-IN')}
              </div>
              <div className="text-[10px] text-muted-foreground mt-0.5">
                Payment success only (of {sales30d.total_sales} total)
              </div>
              <div className="flex items-center gap-1.5 mt-2 text-xs font-medium">
                {sales30d.run_rate_trend === 'up' ? (
                  <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
                    <ArrowUpRight className="h-3.5 w-3.5" />
                    +{sales30d.trend_percent}%
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-rose-600 dark:text-rose-400">
                    <ArrowDownRight className="h-3.5 w-3.5" />
                    -{sales30d.trend_percent}%
                  </span>
                )}
                <span className="text-muted-foreground">
                  Avg Run Rate: <strong className="text-foreground">{sales30d.avg_daily_run_rate}/day</strong>
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 3. Machine Fleet Status */}
        <Card className="bg-card border-border shadow-sm hover:shadow transition-all">
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Machine Fleet
              </span>
              <div className="h-8 w-8 rounded-lg bg-violet-500/10 text-violet-600 dark:text-violet-400 flex items-center justify-center">
                <Cpu className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-bold tracking-tight">
                {machineFleet.total_machines} Machines
              </div>
              <div className="mt-2 space-y-1.5">
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden">
                    <div
                      className="h-full rounded-full bg-emerald-500 transition-all"
                      style={{ width: `${machineFleet.refilled_percent}%` }}
                    />
                  </div>
                  <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 w-12 text-right">
                    {machineFleet.refilled_percent}%
                  </span>
                </div>
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <CheckCircle2 className="h-3 w-3 text-emerald-500" />
                    Refilled: {machineFleet.refilled}
                  </span>
                  <span className="flex items-center gap-1">
                    <XCircle className="h-3 w-3 text-rose-500" />
                    Pending: {machineFleet.not_refilled}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 4. Availability Alert (≤50%) */}
        <Card className={`bg-card border-border shadow-sm hover:shadow transition-all ${
          availabilityAlerts.length > 0 
            ? 'border-amber-500/30 bg-amber-500/5' 
            : ''
        }`}>
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <span className={`text-xs font-semibold uppercase tracking-wider ${
                availabilityAlerts.length > 0
                  ? 'text-amber-600 dark:text-amber-400'
                  : 'text-muted-foreground'
              }`}>
                Low Availability
              </span>
              <div className={`h-8 w-8 rounded-lg flex items-center justify-center ${
                availabilityAlerts.length > 0
                  ? 'bg-amber-500/20 text-amber-600 dark:text-amber-400'
                  : 'bg-muted text-muted-foreground'
              }`}>
                <AlertTriangle className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3">
              <div className={`text-2xl font-bold tracking-tight ${
                availabilityAlerts.length > 0 ? 'text-amber-600 dark:text-amber-400' : ''
              }`}>
                {availabilityAlerts.length} Slots ≤ 50%
              </div>
              <Link
                to="/alerts"
                className="flex items-center gap-1 mt-2 text-xs font-semibold text-amber-600 dark:text-amber-400 hover:underline"
              >
                <span>View & trigger refill →</span>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ── Photos 6 & 7: In-Transit Mismatch WhatsApp Banner + Automated DC Recommendation ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* In Transit Status & 4x Daily Mismatch */}
        <Card className="shadow-sm border-indigo-500/30 bg-indigo-500/5">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-bold text-indigo-600 dark:text-indigo-400 flex items-center gap-2">
                <Truck className="h-4 w-4" />
                In-Transit DC Monitoring
              </CardTitle>
              <Badge variant="info">4x Sync Active</Badge>
            </div>
            <CardDescription className="text-xs">
              Transit tracking & 0% lost-in-transit policy
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2.5">
            <div className="grid grid-cols-2 gap-2 text-center">
              <div className="p-2.5 rounded-lg bg-card border border-border">
                <div className="text-lg font-bold text-foreground">{inTransit.active_transits}</div>
                <div className="text-[10px] text-muted-foreground uppercase">Dispatches En Route</div>
              </div>
              <div className="p-2.5 rounded-lg bg-card border border-emerald-500/30">
                <div className="text-lg font-bold text-emerald-600 dark:text-emerald-400">{inTransit.lost_in_transit_pct}%</div>
                <div className="text-[10px] text-emerald-600/90 dark:text-emerald-400/90 font-semibold uppercase">Lost Target: 0%</div>
              </div>
            </div>

            {inTransit.sync_mismatches_today > 0 && (
              <div className="p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/30 flex items-center justify-between text-xs">
                <span className="text-rose-600 dark:text-rose-400 font-semibold">
                  {inTransit.sync_mismatches_today} sync mismatch detected
                </span>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={triggerWhatsApp}
                  className="h-6 text-[10px] gap-1 text-emerald-600 dark:text-emerald-400 border-emerald-500/40 hover:bg-emerald-500/10"
                >
                  <MessageSquare className="h-3 w-3" />
                  {whatsappSent ? 'Sent to WhatsApp!' : 'WhatsApp Alert'}
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Subwarehouse Stock-Out Automated DC Generation (Photo 7) */}
        <Card className="lg:col-span-2 shadow-sm border-amber-500/30 bg-amber-500/5">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-sm font-bold text-amber-600 dark:text-amber-400 flex items-center gap-2">
                  <Sparkles className="h-4 w-4" />
                  Sub-Warehouse Out of Stock → Auto DC Creation
                </CardTitle>
                <CardDescription className="text-xs">
                  Automated routing from nearest warehouse with surplus stock
                </CardDescription>
              </div>
              <Link to="/dc">
                <Button size="sm" variant="outline" className="h-7 text-xs">
                  Open DC Hub →
                </Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            {inTransit.auto_dc_suggestions.map((s, idx) => (
              <div key={idx} className="p-2.5 rounded-lg bg-card border border-border flex items-center justify-between text-xs">
                <div>
                  <div className="font-semibold text-foreground">{s.item}</div>
                  <div className="text-[10px] text-muted-foreground">
                    Target: <strong className="text-rose-500">{s.target}</strong> • Auto-from: <strong>{s.source}</strong>
                  </div>
                </div>
                <Link to="/dc">
                  <Button size="sm" className="h-7 text-xs gap-1 bg-indigo-600 hover:bg-indigo-700 text-white">
                    <Send className="h-3 w-3" />
                    Auto-DC ({s.qty}u)
                  </Button>
                </Link>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* ── Row 3: PO Tracker + Near-Expiry Stock + Damage Stock ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        {/* 5. PO Tracker (Generated vs Ordered) */}
        <Card className="shadow-sm">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-bold flex items-center gap-2">
                <FileSpreadsheet className="h-4 w-4 text-indigo-500" />
                PO Tracker
              </CardTitle>
              {poTracker.mismatch > 0 && (
                <Badge variant="destructive" className="text-[10px]">
                  {poTracker.mismatch} Mismatch
                </Badge>
              )}
            </div>
            <CardDescription className="text-xs">
              Purchase Orders generated vs actually ordered
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 rounded-lg bg-indigo-500/5 border border-indigo-500/20 text-center">
                <div className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
                  {poTracker.generated}
                </div>
                <div className="text-[10px] font-semibold text-muted-foreground uppercase mt-1">
                  Generated
                </div>
              </div>
              <div className="p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/20 text-center">
                <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
                  {poTracker.ordered}
                </div>
                <div className="text-[10px] font-semibold text-muted-foreground uppercase mt-1">
                  Ordered
                </div>
              </div>
            </div>

            {poTracker.mismatch > 0 && (
              <div className="p-2.5 rounded-lg bg-rose-500/5 border border-rose-500/20 text-xs flex items-center gap-2">
                <ShieldAlert className="h-4 w-4 text-rose-500 shrink-0" />
                <span className="text-rose-600 dark:text-rose-400 font-medium">
                  {poTracker.mismatch} POs generated but not ordered — notify Sahil
                </span>
              </div>
            )}

            <div className="flex items-center justify-between pt-1 border-t border-border text-xs text-muted-foreground">
              <span>Pending approval: {poTracker.pending_approval}</span>
              <span>Last PO: {poTracker.last_po_date}</span>
            </div>

            <Link to="/purchase-orders" className="block">
              <Button variant="outline" size="sm" className="w-full text-xs h-8 gap-1.5">
                <PlusCircle className="h-3.5 w-3.5" />
                Create New PO
              </Button>
            </Link>
          </CardContent>
        </Card>

        {/* 6. Near-Expiry Stock (30 Days) */}
        <Card className="shadow-sm">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-bold flex items-center gap-2">
                <Clock className="h-4 w-4 text-rose-500" />
                Expiring Stock (30 Days)
              </CardTitle>
              <Badge variant="destructive" className="text-[10px]">
                {expiringStock.length} Batches
              </Badge>
            </div>
            <CardDescription className="text-xs">
              Products expiring within 30 days — return to vendor or push sales
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2.5">
            {expiringStock.map((item, idx) => (
              <div key={idx} className="p-2.5 rounded-lg border border-border bg-card hover:bg-muted/20 transition-colors">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-foreground truncate flex-1">
                    {item.name}
                  </span>
                  <span className={`text-xs font-bold shrink-0 ml-2 ${
                    item.days_left <= 14
                      ? 'text-rose-600 dark:text-rose-400'
                      : 'text-amber-600 dark:text-amber-400'
                  }`}>
                    {item.days_left}d left
                  </span>
                </div>
                <div className="flex items-center justify-between mt-1 text-[10px] text-muted-foreground">
                  <span className="font-mono">{item.batch}</span>
                  <span>{item.qty} units • Exp: {item.expiry}</span>
                </div>
              </div>
            ))}
            <Button variant="outline" size="sm" className="w-full text-xs h-8 gap-1.5 text-rose-600 dark:text-rose-400 border-rose-500/30 hover:bg-rose-500/5">
              <Mail className="h-3.5 w-3.5" />
              Email Sahil — Return to Vendor
            </Button>
          </CardContent>
        </Card>

        {/* 7. Damage Stock */}
        <Card className="shadow-sm">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-bold flex items-center gap-2">
                <Trash2 className="h-4 w-4 text-slate-500" />
                Damage Stock
              </CardTitle>
              <Badge variant={damageStock.damage_percent <= damageStock.vendor_agreed_percent ? 'secondary' : 'destructive'} className="text-[10px]">
                {damageStock.damage_percent}% of Total
              </Badge>
            </div>
            <CardDescription className="text-xs">
              Vendor agreement: up to {damageStock.vendor_agreed_percent}% damage accepted
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2.5">
            {/* Damage gauge */}
            <div className="p-3 rounded-lg bg-muted/30 border border-border">
              <div className="flex justify-between text-xs text-muted-foreground mb-2">
                <span>Damage Rate</span>
                <span className="font-bold text-foreground">
                  {damageStock.total_damaged} / {damageStock.total_stock} units
                </span>
              </div>
              <div className="h-3 rounded-full bg-muted overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${
                    damageStock.damage_percent <= damageStock.vendor_agreed_percent
                      ? 'bg-emerald-500'
                      : 'bg-rose-500'
                  }`}
                  style={{ width: `${Math.min((damageStock.damage_percent / damageStock.vendor_agreed_percent) * 100, 100)}%` }}
                />
              </div>
              <div className="flex justify-between text-[10px] text-muted-foreground mt-1.5">
                <span>0%</span>
                <span className="font-semibold">Vendor Limit: {damageStock.vendor_agreed_percent}%</span>
              </div>
            </div>

            {damageStock.items.map((item, idx) => (
              <div key={idx} className="flex items-center justify-between p-2 rounded border border-border text-xs hover:bg-muted/20 transition-colors">
                <div>
                  <span className="font-medium text-foreground">{item.name}</span>
                  <span className="text-muted-foreground ml-2">×{item.qty}</span>
                </div>
                <span className="text-[10px] text-muted-foreground">{item.reason}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* ── Row 4: Daily Run Rate Chart + Availability Alerts Table ── */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">

        {/* 8. Daily Run Rate Chart (30 Days) */}
        <Card className="lg:col-span-3 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div>
              <CardTitle className="text-sm font-bold flex items-center gap-2">
                <Activity className="h-4 w-4 text-indigo-500" />
                Daily Run Rate — Last 30 Days
              </CardTitle>
              <CardDescription className="text-xs">
                Sales velocity & avg run rate trend for auto PO generation
              </CardDescription>
            </div>
            <div className="text-right">
              <div className="text-lg font-bold text-foreground">
                {sales30d.avg_daily_run_rate}
              </div>
              <div className="text-[10px] text-muted-foreground font-medium">units/day avg</div>
            </div>
          </CardHeader>
          <CardContent className="pt-2">
            <div className="h-[220px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={dailyRunRate} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="salesGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#6366F1" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="#6366F1" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="rateGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#10B981" stopOpacity={0.2} />
                      <stop offset="100%" stopColor="#10B981" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                  <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      borderColor: 'hsl(var(--border))',
                      borderRadius: '8px',
                      fontSize: '11px',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="sales"
                    name="Daily Sales"
                    stroke="#6366F1"
                    fill="url(#salesGradient)"
                    strokeWidth={2}
                  />
                  <Area
                    type="monotone"
                    dataKey="run_rate"
                    name="Avg Run Rate"
                    stroke="#10B981"
                    fill="url(#rateGradient)"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Availability Alerts Detail (≤50%) */}
        <Card className="lg:col-span-2 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-bold flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              Slots Below 50% Availability
            </CardTitle>
            <CardDescription className="text-xs">
              Immediate refill required — notifications triggered
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {availabilityAlerts.length === 0 ? (
              <div className="p-6 text-center text-xs text-muted-foreground">
                <CheckCircle2 className="h-8 w-8 text-emerald-500 mx-auto mb-2" />
                All slots above 50% — no alerts
              </div>
            ) : (
              availabilityAlerts.map((item, idx) => (
                <div key={idx} className="p-3 rounded-lg border border-amber-500/20 bg-amber-500/5 hover:bg-amber-500/10 transition-colors">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-foreground">{item.name}</span>
                    <span className="text-xs font-bold text-amber-600 dark:text-amber-400">
                      {item.availability}%
                    </span>
                  </div>
                  <div className="mt-1.5 h-1.5 rounded-full bg-muted overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        item.availability <= 30 ? 'bg-rose-500' : 'bg-amber-500'
                      }`}
                      style={{ width: `${item.availability}%` }}
                    />
                  </div>
                  <div className="flex justify-between mt-1.5 text-[10px] text-muted-foreground">
                    <span>{item.machine} • Slot {item.slot}</span>
                    <span className="font-mono">{item.sku}</span>
                  </div>
                </div>
              ))
            )}

            {availabilityAlerts.length > 0 && (
              <Link to="/alerts" className="block pt-1">
                <Button variant="outline" size="sm" className="w-full text-xs h-8 gap-1.5 text-amber-600 dark:text-amber-400 border-amber-500/30">
                  <RotateCcw className="h-3.5 w-3.5" />
                  Trigger Refill for All
                </Button>
              </Link>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
