import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  AlertTriangle,
  Clock,
  Archive,
  CheckCircle2,
  ArrowRight,
  ShieldAlert,
  Bell,
  RefreshCw,
} from 'lucide-react'
import apiClient from '@/api/client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

export default function AlertsPage() {
  const [lowStock, setLowStock] = useState([
    { name: 'Snickers Chocolate Bar 50g', sku: 'CHO-SNK-50', warehouse: 'Main Dark Store', on_hand: 8, threshold: 12, suggested: 50 },
    { name: 'Lays Classic Salted 50g', sku: 'SNK-LAY-50', warehouse: 'Main Dark Store', on_hand: 4, threshold: 15, suggested: 60 },
  ])

  const [expiring, setExpiring] = useState([
    { name: 'Paper Boat Aamras Mango 250ml', sku: 'BEV-PB-250', batch: 'BATCH-PB-0426', expiry: '2026-08-30', days_left: 13, qty: 14 },
    { name: 'Doritos Cheese Nachos 50g', sku: 'SNK-DOR-50', batch: 'BATCH-DOR-0326', expiry: '2026-09-15', days_left: 29, qty: 18 },
  ])

  const [deadStock, setDeadStock] = useState([
    { name: 'Diet Green Tea 250ml', sku: 'BEV-TEA-250', on_hand: 12, cost: 35, tied_capital: 420, days_inactive: 65 },
  ])

  useEffect(() => {
    async function fetchAlerts() {
      try {
        const [lowRes, expRes, deadRes] = await Promise.all([
          apiClient.get('/alerts/low-stock'),
          apiClient.get('/alerts/expiring'),
          apiClient.get('/alerts/dead-stock'),
        ])
        if (lowRes.data?.data?.length) setLowStock(lowRes.data.data)
        if (expRes.data?.data?.length) setExpiring(expRes.data.data)
        if (deadRes.data?.data?.length) setDeadStock(deadRes.data.data)
      } catch (err) {
        console.log('Using default alerts dataset')
      }
    }
    fetchAlerts()
  }, [])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
          <ShieldAlert className="h-6 w-6 text-amber-500" />
          Fleet Alert & Operational Health Center
        </h1>
        <p className="text-xs text-muted-foreground mt-0.5">
          Real-time tracking of low stock replenishment, perishable expiry thresholds, and dead inventory
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Low Stock Card */}
        <Card className="border-amber-500/30 bg-amber-500/5">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-bold text-amber-600 dark:text-amber-400 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                Low Stock Thresholds
              </CardTitle>
              <Badge variant="warning">{lowStock.length} Items</Badge>
            </div>
            <CardDescription className="text-xs">Immediate PO action recommended</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 pt-2">
            {lowStock.map((item, idx) => (
              <div key={idx} className="p-3 rounded-lg bg-card border border-border space-y-1.5 text-xs">
                <div className="flex justify-between font-semibold text-foreground">
                  <span>{item.name}</span>
                  <span className="text-amber-600 dark:text-amber-400 font-bold">{item.on_hand} left</span>
                </div>
                <div className="text-[11px] text-muted-foreground flex justify-between">
                  <span>Reorder threshold: {item.threshold} units</span>
                  <span>Suggested PO: +{item.suggested}</span>
                </div>
                <Link to="/purchase-orders" className="block pt-1">
                  <Button size="sm" variant="outline" className="w-full h-7 text-xs text-amber-600 dark:text-amber-400 border-amber-500/30">
                    Order Replenishment →
                  </Button>
                </Link>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Expiring Soon Card */}
        <Card className="border-rose-500/30 bg-rose-500/5">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-bold text-rose-600 dark:text-rose-400 flex items-center gap-2">
                <Clock className="h-4 w-4" />
                Expiring Batches (FIFO)
              </CardTitle>
              <Badge variant="destructive">{expiring.length} Batches</Badge>
            </div>
            <CardDescription className="text-xs">Prioritize sales before expiration date</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 pt-2">
            {expiring.map((batch, idx) => (
              <div key={idx} className="p-3 rounded-lg bg-card border border-border space-y-1.5 text-xs">
                <div className="flex justify-between font-semibold text-foreground">
                  <span className="truncate">{batch.name}</span>
                  <span className="text-rose-600 dark:text-rose-400 font-bold shrink-0">
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
          </CardContent>
        </Card>

        {/* Dead Stock Card */}
        <Card className="border-slate-500/30 bg-slate-500/5">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-bold text-slate-400 flex items-center gap-2">
                <Archive className="h-4 w-4" />
                Dead Stock / Slow Movers
              </CardTitle>
              <Badge variant="secondary">{deadStock.length} SKUs</Badge>
            </div>
            <CardDescription className="text-xs">No customer sales or transfers in 60+ days</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 pt-2">
            {deadStock.map((d, idx) => (
              <div key={idx} className="p-3 rounded-lg bg-card border border-border space-y-1.5 text-xs">
                <div className="flex justify-between font-semibold text-foreground">
                  <span>{d.name}</span>
                  <span className="text-muted-foreground font-mono">{d.sku}</span>
                </div>
                <div className="text-[11px] text-muted-foreground flex justify-between">
                  <span>Stock: {d.on_hand} units</span>
                  <span>Tied Capital: ₹{d.tied_capital}</span>
                </div>
                <div className="p-1.5 rounded bg-muted/40 text-[10px] text-muted-foreground">
                  Inactive for {d.days_inactive} days. Recommend discount promo.
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
