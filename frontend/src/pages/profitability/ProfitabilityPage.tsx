import React, { useEffect, useState } from 'react'
import {
  TrendingUp,
  DollarSign,
  Layers,
  ArrowUpRight,
  ArrowDownRight,
  Zap,
  Percent,
  Sparkles,
} from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  ZAxis,
} from 'recharts'
import apiClient from '@/api/client'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

interface SlotProfit {
  product_id: string
  sku: string
  name: string
  brand?: string
  mrp: number
  cost_price: number
  selling_price: number
  unit_profit: number
  margin_percent: number
  stock_on_hand: number
  potential_total_profit: number
}

const DEFAULT_SLOTS: SlotProfit[] = [
  { product_id: '1', sku: 'BEV-RB-250', name: 'Red Bull Energy Drink 250ml', brand: 'Red Bull', mrp: 125, cost_price: 75, selling_price: 125, unit_profit: 50, margin_percent: 40.0, stock_on_hand: 24, potential_total_profit: 1200 },
  { product_id: '2', sku: 'BEV-PB-250', name: 'Paper Boat Aamras Mango', brand: 'Paper Boat', mrp: 35, cost_price: 20, selling_price: 35, unit_profit: 15, margin_percent: 42.8, stock_on_hand: 14, potential_total_profit: 210 },
  { product_id: '3', sku: 'SNK-DOR-50', name: 'Doritos Cheese Nachos 50g', brand: 'Doritos', mrp: 50, cost_price: 30, selling_price: 50, unit_profit: 20, margin_percent: 40.0, stock_on_hand: 18, potential_total_profit: 360 },
  { product_id: '4', sku: 'BEV-CC-300', name: 'Coca Cola Can 300ml', brand: 'Coca-Cola', mrp: 40, cost_price: 25, selling_price: 40, unit_profit: 15, margin_percent: 37.5, stock_on_hand: 32, potential_total_profit: 480 },
  { product_id: '5', sku: 'CHO-SNK-50', name: 'Snickers Chocolate Bar 50g', brand: 'Snickers', mrp: 50, cost_price: 32, selling_price: 50, unit_profit: 18, margin_percent: 36.0, stock_on_hand: 8, potential_total_profit: 144 },
  { product_id: '6', sku: 'SNK-LAY-50', name: 'Lays Classic Salted 50g', brand: 'Lays', unit_profit: 8, cost_price: 12, selling_price: 20, mrp: 20, margin_percent: 40.0, stock_on_hand: 4, potential_total_profit: 32 },
]

export default function ProfitabilityPage() {
  const [slots, setSlots] = useState<SlotProfit[]>(DEFAULT_SLOTS)

  useEffect(() => {
    async function fetchProfit() {
      try {
        const res = await apiClient.get('/analytics/profit-per-slot')
        if (res.data?.data?.length) setSlots(res.data.data)
      } catch (err) {
        console.log('Using default profitability slots dataset')
      }
    }
    fetchProfit()
  }, [])

  const totalPotentialProfit = slots.reduce((acc, s) => acc + s.potential_total_profit, 0)
  const avgMargin = (
    slots.reduce((acc, s) => acc + s.margin_percent, 0) / (slots.length || 1)
  ).toFixed(1)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">
          Profitability & Slot Space Efficiency
        </h1>
        <p className="text-xs text-muted-foreground mt-0.5">
          Unit economics, gross margin percentages, and profit contribution per machine spiral
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="shadow-sm">
          <CardContent className="p-5">
            <div className="flex justify-between items-center text-xs font-semibold text-muted-foreground">
              <span>Average Slot Margin</span>
              <Percent className="h-4 w-4 text-emerald-500" />
            </div>
            <div className="text-2xl font-bold mt-2 text-emerald-600 dark:text-emerald-400">
              {avgMargin}%
            </div>
            <p className="text-xs text-muted-foreground mt-1">Healthy industry benchmark &gt; 35%</p>
          </CardContent>
        </Card>

        <Card className="shadow-sm">
          <CardContent className="p-5">
            <div className="flex justify-between items-center text-xs font-semibold text-muted-foreground">
              <span>Total Fleet Potential Profit</span>
              <DollarSign className="h-4 w-4 text-indigo-500" />
            </div>
            <div className="text-2xl font-bold mt-2 text-foreground">
              ₹{totalPotentialProfit.toLocaleString('en-IN')}
            </div>
            <p className="text-xs text-muted-foreground mt-1">From inventory on hand</p>
          </CardContent>
        </Card>

        <Card className="shadow-sm">
          <CardContent className="p-5">
            <div className="flex justify-between items-center text-xs font-semibold text-muted-foreground">
              <span>Top Contributor SKU</span>
              <Zap className="h-4 w-4 text-amber-500" />
            </div>
            <div className="text-xl font-bold mt-2 text-foreground truncate">
              {slots[0]?.name || 'Red Bull 250ml'}
            </div>
            <p className="text-xs text-emerald-600 dark:text-emerald-400 mt-1 font-semibold">
              +₹{slots[0]?.unit_profit} per item ({slots[0]?.margin_percent}%)
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Visual Chart */}
      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle className="text-sm font-bold">Gross Margin % Comparison</CardTitle>
          <CardDescription className="text-xs">
            Percentage profit realized on each item sale across vending slots
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[280px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={slots} margin={{ top: 10, right: 10, left: -10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} angle={-15} textAnchor="end" height={40} />
                <YAxis tick={{ fontSize: 11 }} domain={[0, 60]} unit="%" />
                <Tooltip
                  formatter={(val: any) => [`${val}%`, 'Gross Margin']}
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    borderColor: 'hsl(var(--border))',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="margin_percent" fill="#6366F1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Breakdown Table */}
      <Card className="shadow-sm overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>SKU & Product Name</TableHead>
              <TableHead>Cost Price</TableHead>
              <TableHead>Selling Price (MRP)</TableHead>
              <TableHead>Profit / Unit</TableHead>
              <TableHead>Margin %</TableHead>
              <TableHead>Stock on Hand</TableHead>
              <TableHead className="text-right">Potential Slot Value</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {slots.map((s, idx) => (
              <TableRow key={idx} className="hover:bg-muted/40">
                <TableCell>
                  <div className="font-semibold text-foreground">{s.name}</div>
                  <div className="font-mono text-xs text-muted-foreground">{s.sku}</div>
                </TableCell>
                <TableCell className="text-muted-foreground">₹{s.cost_price}</TableCell>
                <TableCell className="font-semibold text-foreground">₹{s.selling_price}</TableCell>
                <TableCell className="font-bold text-emerald-600 dark:text-emerald-400">
                  +₹{s.unit_profit}
                </TableCell>
                <TableCell>
                  <Badge variant={s.margin_percent >= 40 ? 'success' : 'secondary'}>
                    {s.margin_percent}%
                  </Badge>
                </TableCell>
                <TableCell className="text-foreground">{s.stock_on_hand} units</TableCell>
                <TableCell className="text-right font-bold text-foreground">
                  ₹{s.potential_total_profit.toLocaleString('en-IN')}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  )
}
