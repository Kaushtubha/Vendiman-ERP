import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  AlertTriangle,
  Clock,
  CheckCircle2,
  ShieldAlert,
  Bell,
  RefreshCw,
  Trash2,
  Mail,
  FileSpreadsheet,
  RotateCcw,
  XCircle,
  Cpu,
} from 'lucide-react'
import apiClient from '@/api/client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

export default function AlertsPage() {
  // ── Low Availability (≤50%) Alerts ──
  const [availabilityAlerts, setAvailabilityAlerts] = useState([
    { name: 'Lays Classic Salted 50g', sku: 'SNK-LAY-50', machine: 'VM-04', availability: 25, slot: 'B3', on_hand: 4, capacity: 16 },
    { name: 'Snickers Bar 50g', sku: 'CHO-SNK-50', machine: 'VM-07', availability: 38, slot: 'A2', on_hand: 6, capacity: 16 },
    { name: 'Coca Cola 300ml', sku: 'BEV-CC-300', machine: 'VM-02', availability: 45, slot: 'C1', on_hand: 9, capacity: 20 },
    { name: 'Paper Boat Mango 250ml', sku: 'BEV-PB-250', machine: 'VM-09', availability: 30, slot: 'D2', on_hand: 3, capacity: 10 },
  ])

  // ── PO Mismatch Alerts ──
  const [poMismatch, setPoMismatch] = useState([
    { po_number: 'PO-202608-A93F1', supplier: 'Hindustan Bottling', generated_date: '2026-08-10', status: 'generated_not_ordered', amount: 14500 },
    { po_number: 'PO-202608-D47R2', supplier: 'PepsiCo Distribution', generated_date: '2026-08-12', status: 'generated_not_ordered', amount: 8900 },
    { po_number: 'PO-202608-E51K8', supplier: 'Mars Wrigley India', generated_date: '2026-08-15', status: 'generated_not_ordered', amount: 6200 },
  ])

  // ── Expiring Stock ──
  const [expiring, setExpiring] = useState([
    { name: 'Paper Boat Aamras Mango 250ml', sku: 'BEV-PB-250', batch: 'BATCH-PB-0426', expiry: '2026-08-30', days_left: 11, qty: 14 },
    { name: 'Doritos Cheese Nachos 50g', sku: 'SNK-DOR-50', batch: 'BATCH-DOR-0326', expiry: '2026-09-15', days_left: 27, qty: 18 },
    { name: 'Protein Bar 40g', sku: 'SNK-PRO-40', batch: 'BATCH-PRO-0726', expiry: '2026-09-05', days_left: 17, qty: 8 },
  ])

  // ── Damage Stock ──
  const [damageStock, setDamageStock] = useState([
    { name: 'Red Bull 250ml', sku: 'BEV-RB-250', qty: 3, reason: 'Dented cans', date_reported: '2026-08-12' },
    { name: 'Lays Classic 50g', sku: 'SNK-LAY-50', qty: 5, reason: 'Packet torn', date_reported: '2026-08-14' },
    { name: 'KitKat 37g', sku: 'CHO-KK-37', qty: 4, reason: 'Melted/Deformed', date_reported: '2026-08-16' },
    { name: 'Snickers 50g', sku: 'CHO-SNK-50', qty: 2, reason: 'Wrapper damage', date_reported: '2026-08-18' },
  ])

  useEffect(() => {
    async function fetchAlerts() {
      try {
        const [lowRes, expRes] = await Promise.all([
          apiClient.get('/alerts/low-stock'),
          apiClient.get('/alerts/expiring'),
        ])
        if (lowRes.data?.data?.length) setAvailabilityAlerts(lowRes.data.data)
        if (expRes.data?.data?.length) setExpiring(expRes.data.data)
      } catch (err) {
        console.log('Using default alerts dataset')
      }
    }
    fetchAlerts()
  }, [])

  const totalDamaged = damageStock.reduce((acc, d) => acc + d.qty, 0)

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <ShieldAlert className="h-6 w-6 text-amber-500" />
            Alerts Center
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Availability alerts, PO mismatches, expiry tracking & damage stock
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" className="gap-1.5 text-xs">
            <Mail className="h-3.5 w-3.5" />
            Email Report to Sahil
          </Button>
          <Button variant="outline" size="sm" className="gap-1.5 text-xs">
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </Button>
        </div>
      </div>

      {/* ── Summary Stats ── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3 rounded-lg bg-amber-500/5 border border-amber-500/20">
          <div className="text-xl font-bold text-amber-600 dark:text-amber-400">{availabilityAlerts.length}</div>
          <div className="text-[10px] font-semibold text-muted-foreground uppercase">Slots ≤ 50%</div>
        </div>
        <div className="p-3 rounded-lg bg-rose-500/5 border border-rose-500/20">
          <div className="text-xl font-bold text-rose-600 dark:text-rose-400">{poMismatch.length}</div>
          <div className="text-[10px] font-semibold text-muted-foreground uppercase">PO Mismatches</div>
        </div>
        <div className="p-3 rounded-lg bg-orange-500/5 border border-orange-500/20">
          <div className="text-xl font-bold text-orange-600 dark:text-orange-400">{expiring.length}</div>
          <div className="text-[10px] font-semibold text-muted-foreground uppercase">Expiring Batches</div>
        </div>
        <div className="p-3 rounded-lg bg-slate-500/5 border border-slate-500/20">
          <div className="text-xl font-bold text-slate-600 dark:text-slate-400">{totalDamaged}</div>
          <div className="text-[10px] font-semibold text-muted-foreground uppercase">Damaged Units</div>
        </div>
      </div>

      {/* ── Alert Sections ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* 1. Availability ≤ 50% Alerts */}
        <Card className="border-amber-500/30 bg-amber-500/5 shadow-sm">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-bold text-amber-600 dark:text-amber-400 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                Low Availability (≤ 50%)
              </CardTitle>
              <Badge variant="warning">{availabilityAlerts.length} Active</Badge>
            </div>
            <CardDescription className="text-xs">
              Machine slots below 50% capacity — trigger refill immediately
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2.5 pt-2">
            {availabilityAlerts.map((item, idx) => (
              <div key={idx} className="p-3 rounded-lg bg-card border border-border space-y-2">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="text-xs font-semibold text-foreground">{item.name}</div>
                    <div className="text-[10px] text-muted-foreground mt-0.5">
                      {item.machine} • Slot {item.slot} • <span className="font-mono">{item.sku}</span>
                    </div>
                  </div>
                  <span className={`text-sm font-bold ${
                    item.availability <= 30
                      ? 'text-rose-600 dark:text-rose-400'
                      : 'text-amber-600 dark:text-amber-400'
                  }`}>
                    {item.availability}%
                  </span>
                </div>
                <div className="h-2 rounded-full bg-muted overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      item.availability <= 30 ? 'bg-rose-500' : 'bg-amber-500'
                    }`}
                    style={{ width: `${item.availability}%` }}
                  />
                </div>
                <div className="flex justify-between text-[10px] text-muted-foreground">
                  <span>{item.on_hand} of {item.capacity} units remaining</span>
                  <span>Refill needed: +{item.capacity - item.on_hand}</span>
                </div>
              </div>
            ))}
            <Button size="sm" className="w-full h-8 text-xs gap-1.5 mt-2">
              <RotateCcw className="h-3.5 w-3.5" />
              Trigger Refill for All {availabilityAlerts.length} Slots
            </Button>
          </CardContent>
        </Card>

        {/* 2. PO Mismatch Alerts */}
        <Card className="border-rose-500/30 bg-rose-500/5 shadow-sm">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-bold text-rose-600 dark:text-rose-400 flex items-center gap-2">
                <FileSpreadsheet className="h-4 w-4" />
                PO Generated ≠ Ordered
              </CardTitle>
              <Badge variant="destructive">{poMismatch.length} Pending</Badge>
            </div>
            <CardDescription className="text-xs">
              POs generated but not yet ordered from supplier — action required
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2.5 pt-2">
            {poMismatch.map((po, idx) => (
              <div key={idx} className="p-3 rounded-lg bg-card border border-border space-y-1.5">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-mono font-bold text-indigo-600 dark:text-indigo-400">
                    {po.po_number}
                  </span>
                  <Badge variant="destructive" className="text-[9px]">Not Ordered</Badge>
                </div>
                <div className="flex justify-between text-[11px] text-muted-foreground">
                  <span>{po.supplier}</span>
                  <span className="font-semibold text-foreground">₹{po.amount.toLocaleString('en-IN')}</span>
                </div>
                <div className="text-[10px] text-muted-foreground">
                  Generated: {po.generated_date}
                </div>
                <div className="flex gap-2 pt-1">
                  <Link to="/purchase-orders" className="flex-1">
                    <Button variant="outline" size="sm" className="w-full h-7 text-[10px]">
                      Order Now →
                    </Button>
                  </Link>
                </div>
              </div>
            ))}
            <Button variant="outline" size="sm" className="w-full h-8 text-xs gap-1.5 text-rose-600 dark:text-rose-400 border-rose-500/30 mt-2">
              <Mail className="h-3.5 w-3.5" />
              Auto Report & Mail to Sahil
            </Button>
          </CardContent>
        </Card>

        {/* 3. Expiring Batches */}
        <Card className="border-orange-500/30 bg-orange-500/5 shadow-sm">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-bold text-orange-600 dark:text-orange-400 flex items-center gap-2">
                <Clock className="h-4 w-4" />
                Near-Expiry Stock (30 Days)
              </CardTitle>
              <Badge variant="warning">{expiring.length} Batches</Badge>
            </div>
            <CardDescription className="text-xs">
              Products expiring soon — email Sahil for return to vendor
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2.5 pt-2">
            {expiring.map((batch, idx) => (
              <div key={idx} className="p-3 rounded-lg bg-card border border-border space-y-1.5">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-semibold text-foreground truncate">{batch.name}</span>
                  <span className={`text-xs font-bold shrink-0 ${
                    batch.days_left <= 14
                      ? 'text-rose-600 dark:text-rose-400'
                      : 'text-amber-600 dark:text-amber-400'
                  }`}>
                    {batch.days_left} days left
                  </span>
                </div>
                <div className="text-[11px] text-muted-foreground flex justify-between">
                  <span className="font-mono">{batch.batch}</span>
                  <span>{batch.qty} units on hand</span>
                </div>
                <div className="text-[10px] text-muted-foreground pt-1 border-t border-border">
                  Expiry Date: <strong className="text-foreground">{batch.expiry}</strong>
                </div>
              </div>
            ))}
            <div className="flex gap-2 mt-2">
              <Button variant="outline" size="sm" className="flex-1 h-8 text-xs gap-1.5 text-orange-600 dark:text-orange-400 border-orange-500/30">
                <Mail className="h-3.5 w-3.5" />
                Email Sahil — Return to Vendor
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* 4. Damage Stock */}
        <Card className="border-slate-500/30 bg-slate-500/5 shadow-sm">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-bold text-slate-400 flex items-center gap-2">
                <Trash2 className="h-4 w-4" />
                Damage Stock
              </CardTitle>
              <Badge variant="secondary">{totalDamaged} Units</Badge>
            </div>
            <CardDescription className="text-xs">
              Vendor pre-agreed: up to 5% damage accepted. Track damaged items here.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2.5 pt-2">
            {damageStock.map((d, idx) => (
              <div key={idx} className="p-3 rounded-lg bg-card border border-border space-y-1.5">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-semibold text-foreground">{d.name}</span>
                  <span className="text-xs font-bold text-slate-500">{d.qty} units</span>
                </div>
                <div className="flex justify-between text-[11px] text-muted-foreground">
                  <span className="font-mono">{d.sku}</span>
                  <span>{d.reason}</span>
                </div>
                <div className="text-[10px] text-muted-foreground">
                  Reported: {d.date_reported}
                </div>
              </div>
            ))}
            <div className="p-2.5 rounded-lg bg-muted/30 border border-border text-xs text-muted-foreground mt-2">
              <div className="flex justify-between">
                <span>Total Damaged:</span>
                <span className="font-bold text-foreground">{totalDamaged} units</span>
              </div>
              <div className="text-[10px] mt-1">
                Vendor damage agreement: 5% of total stock (≈{Math.round(856 * 0.05)} units) — 
                <span className={totalDamaged <= 43 ? 'text-emerald-600 dark:text-emerald-400 font-semibold' : 'text-rose-600 dark:text-rose-400 font-semibold'}>
                  {totalDamaged <= 43 ? ' Within limit ✓' : ' Exceeds limit ✗'}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
