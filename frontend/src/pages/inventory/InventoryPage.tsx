import React, { useEffect, useState } from 'react'
import { Search, Warehouse, AlertTriangle, Sliders, X, Clock, Trash2, CheckCircle2 } from 'lucide-react'
import apiClient from '@/api/client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

interface StockItem {
  id: string
  product_id: string
  product_sku: string
  product_name: string
  main_wh_qty: number
  sub_wh_qty: number
  machine_qty: number
  total_qty: number
  reorder_point: number
  is_low_stock: boolean
  expiry_date: string | null
  is_damaged: boolean
  damage_qty: number
}

const DEFAULT_STOCKS: StockItem[] = [
  { id: '1', product_id: 'p1', product_sku: 'BEV-RB-250', product_name: 'Red Bull Energy Drink 250ml', main_wh_qty: 120, sub_wh_qty: 60, machine_qty: 24, total_qty: 204, reorder_point: 50, is_low_stock: false, expiry_date: '2027-03-15', is_damaged: true, damage_qty: 3 },
  { id: '2', product_id: 'p2', product_sku: 'BEV-CC-300', product_name: 'Coca Cola Can 300ml', main_wh_qty: 150, sub_wh_qty: 80, machine_qty: 32, total_qty: 262, reorder_point: 60, is_low_stock: false, expiry_date: '2027-06-20', is_damaged: false, damage_qty: 0 },
  { id: '3', product_id: 'p3', product_sku: 'SNK-DOR-50', product_name: 'Doritos Cheese Nachos 50g', main_wh_qty: 80, sub_wh_qty: 40, machine_qty: 18, total_qty: 138, reorder_point: 40, is_low_stock: false, expiry_date: '2026-09-15', is_damaged: false, damage_qty: 0 },
  { id: '4', product_id: 'p4', product_sku: 'CHO-SNK-50', product_name: 'Snickers Chocolate Bar 50g', main_wh_qty: 20, sub_wh_qty: 10, machine_qty: 8, total_qty: 38, reorder_point: 40, is_low_stock: true, expiry_date: '2026-11-30', is_damaged: false, damage_qty: 0 },
  { id: '5', product_id: 'p5', product_sku: 'SNK-LAY-50', product_name: 'Lays Classic Salted 50g', main_wh_qty: 10, sub_wh_qty: 5, machine_qty: 4, total_qty: 19, reorder_point: 40, is_low_stock: true, expiry_date: '2026-12-10', is_damaged: true, damage_qty: 5 },
  { id: '6', product_id: 'p6', product_sku: 'BEV-PB-250', product_name: 'Paper Boat Mango 250ml', main_wh_qty: 40, sub_wh_qty: 20, machine_qty: 14, total_qty: 74, reorder_point: 30, is_low_stock: false, expiry_date: '2026-08-30', is_damaged: false, damage_qty: 0 },
  { id: '7', product_id: 'p7', product_sku: 'CHO-KK-37', product_name: 'KitKat 37g', main_wh_qty: 60, sub_wh_qty: 30, machine_qty: 20, total_qty: 110, reorder_point: 35, is_low_stock: false, expiry_date: '2027-01-15', is_damaged: true, damage_qty: 4 },
  { id: '8', product_id: 'p8', product_sku: 'SNK-PRO-40', product_name: 'Protein Bar 40g', main_wh_qty: 15, sub_wh_qty: 8, machine_qty: 6, total_qty: 29, reorder_point: 25, is_low_stock: false, expiry_date: '2026-09-05', is_damaged: false, damage_qty: 0 },
]

export default function InventoryPage() {
  const [stocks, setStocks] = useState<StockItem[]>(DEFAULT_STOCKS)
  const [search, setSearch] = useState('')
  const [activeFilter, setActiveFilter] = useState<'all' | 'low_stock' | 'expiring' | 'damaged'>('all')
  const [isAdjustModalOpen, setIsAdjustModalOpen] = useState(false)
  const [selectedItem, setSelectedItem] = useState<StockItem | null>(null)
  const [newQty, setNewQty] = useState<number>(0)
  const [adjustWarehouse, setAdjustWarehouse] = useState('main_wh')
  const [reason, setReason] = useState('physical_count')

  useEffect(() => {
    fetchStocks()
  }, [])

  const fetchStocks = async () => {
    try {
      const res = await apiClient.get('/inventory')
      if (res.data?.data?.length) setStocks(res.data.data)
    } catch (err) {
      console.log('Using default stock levels')
    }
  }

  const openAdjust = (item: StockItem) => {
    setSelectedItem(item)
    setNewQty(item.main_wh_qty)
    setAdjustWarehouse('main_wh')
    setIsAdjustModalOpen(true)
  }

  const handleAdjustSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedItem) return

    setStocks(
      stocks.map((s) => {
        if (s.id !== selectedItem.id) return s
        const updated = { ...s }
        if (adjustWarehouse === 'main_wh') updated.main_wh_qty = newQty
        else if (adjustWarehouse === 'sub_wh') updated.sub_wh_qty = newQty
        else updated.machine_qty = newQty
        updated.total_qty = updated.main_wh_qty + updated.sub_wh_qty + updated.machine_qty
        updated.is_low_stock = updated.total_qty <= s.reorder_point
        return updated
      })
    )
    setIsAdjustModalOpen(false)
  }

  // Calculate days until expiry
  const getDaysUntilExpiry = (expiryDate: string | null): number | null => {
    if (!expiryDate) return null
    const diff = new Date(expiryDate).getTime() - Date.now()
    return Math.ceil(diff / (1000 * 60 * 60 * 24))
  }

  const filtered = stocks.filter((s) => {
    const matchesSearch =
      s.product_name.toLowerCase().includes(search.toLowerCase()) ||
      s.product_sku.toLowerCase().includes(search.toLowerCase())

    if (!matchesSearch) return false

    switch (activeFilter) {
      case 'low_stock':
        return s.is_low_stock
      case 'expiring': {
        const days = getDaysUntilExpiry(s.expiry_date)
        return days !== null && days <= 30
      }
      case 'damaged':
        return s.is_damaged
      default:
        return true
    }
  })

  const lowStockCount = stocks.filter((s) => s.is_low_stock).length
  const expiringCount = stocks.filter((s) => {
    const days = getDaysUntilExpiry(s.expiry_date)
    return days !== null && days <= 30
  }).length
  const damagedCount = stocks.filter((s) => s.is_damaged).length

  const totalMainWH = stocks.reduce((sum, s) => sum + s.main_wh_qty, 0)
  const totalSubWH = stocks.reduce((sum, s) => sum + s.sub_wh_qty, 0)
  const totalMachine = stocks.reduce((sum, s) => sum + s.machine_qty, 0)
  const totalAll = stocks.reduce((sum, s) => sum + s.total_qty, 0)

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Inventory & Stock Balances
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Stock breakdown by Main WH, Sub WH & Machine — with expiry and damage tracking
          </p>
        </div>
      </div>

      {/* ── WH Summary Cards ── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3 rounded-lg bg-indigo-500/5 border border-indigo-500/20">
          <div className="text-[10px] font-semibold text-muted-foreground uppercase">Main WH</div>
          <div className="text-xl font-bold text-indigo-600 dark:text-indigo-400 mt-1">{totalMainWH}</div>
        </div>
        <div className="p-3 rounded-lg bg-violet-500/5 border border-violet-500/20">
          <div className="text-[10px] font-semibold text-muted-foreground uppercase">Sub WH</div>
          <div className="text-xl font-bold text-violet-600 dark:text-violet-400 mt-1">{totalSubWH}</div>
        </div>
        <div className="p-3 rounded-lg bg-cyan-500/5 border border-cyan-500/20">
          <div className="text-[10px] font-semibold text-muted-foreground uppercase">In Machines</div>
          <div className="text-xl font-bold text-cyan-600 dark:text-cyan-400 mt-1">{totalMachine}</div>
        </div>
        <div className="p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/20">
          <div className="text-[10px] font-semibold text-muted-foreground uppercase">Total Stock</div>
          <div className="text-xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">{totalAll}</div>
        </div>
      </div>

      {/* ── Filter Bar ── */}
      <Card className="shadow-sm">
        <CardContent className="p-4 flex flex-col sm:flex-row gap-3 items-center justify-between">
          <div className="relative w-full sm:w-80">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Filter by SKU or Product Name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 text-xs"
            />
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <Button
              variant={activeFilter === 'all' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setActiveFilter('all')}
              className="text-xs h-8"
            >
              All ({stocks.length})
            </Button>
            <Button
              variant={activeFilter === 'low_stock' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setActiveFilter('low_stock')}
              className="text-xs gap-1.5 h-8"
            >
              <AlertTriangle className="h-3.5 w-3.5" />
              Low Stock ({lowStockCount})
            </Button>
            <Button
              variant={activeFilter === 'expiring' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setActiveFilter('expiring')}
              className="text-xs gap-1.5 h-8"
            >
              <Clock className="h-3.5 w-3.5" />
              Expiring ({expiringCount})
            </Button>
            <Button
              variant={activeFilter === 'damaged' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setActiveFilter('damaged')}
              className="text-xs gap-1.5 h-8"
            >
              <Trash2 className="h-3.5 w-3.5" />
              Damaged ({damagedCount})
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* ── Stock Table ── */}
      <Card className="shadow-sm overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>SKU</TableHead>
              <TableHead>Product Name</TableHead>
              <TableHead className="text-center">Main WH</TableHead>
              <TableHead className="text-center">Sub WH</TableHead>
              <TableHead className="text-center">Machine</TableHead>
              <TableHead className="text-center">Total</TableHead>
              <TableHead>Expiry Date</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((s) => {
              const daysLeft = getDaysUntilExpiry(s.expiry_date)
              return (
                <TableRow key={s.id} className="hover:bg-muted/40">
                  <TableCell className="font-mono font-bold text-xs text-indigo-600 dark:text-indigo-400">
                    {s.product_sku}
                  </TableCell>
                  <TableCell className="font-medium text-foreground">{s.product_name}</TableCell>
                  <TableCell className="text-center font-semibold text-foreground">{s.main_wh_qty}</TableCell>
                  <TableCell className="text-center font-semibold text-foreground">{s.sub_wh_qty}</TableCell>
                  <TableCell className="text-center font-semibold text-foreground">{s.machine_qty}</TableCell>
                  <TableCell className="text-center">
                    <span className={`font-bold ${s.is_low_stock ? 'text-amber-600 dark:text-amber-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
                      {s.total_qty}
                    </span>
                  </TableCell>
                  <TableCell>
                    {s.expiry_date ? (
                      <div className="text-xs">
                        <div className="text-muted-foreground">{s.expiry_date}</div>
                        {daysLeft !== null && daysLeft <= 30 && (
                          <div className={`text-[10px] font-semibold ${
                            daysLeft <= 14 ? 'text-rose-600 dark:text-rose-400' : 'text-amber-600 dark:text-amber-400'
                          }`}>
                            {daysLeft}d left
                          </div>
                        )}
                      </div>
                    ) : (
                      <span className="text-xs text-muted-foreground">—</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-col gap-1">
                      {s.is_low_stock && <Badge variant="warning">Low Stock</Badge>}
                      {daysLeft !== null && daysLeft <= 30 && (
                        <Badge variant="destructive">Expiring</Badge>
                      )}
                      {s.is_damaged && (
                        <Badge variant="secondary">Damaged ({s.damage_qty})</Badge>
                      )}
                      {!s.is_low_stock && (daysLeft === null || daysLeft > 30) && !s.is_damaged && (
                        <Badge variant="success">OK</Badge>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-7 text-xs gap-1"
                      onClick={() => openAdjust(s)}
                    >
                      <Sliders className="h-3 w-3" />
                      Adjust
                    </Button>
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </Card>

      {/* ── Adjust Modal ── */}
      {isAdjustModalOpen && selectedItem && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <Card className="w-full max-w-md bg-card border-border shadow-2xl animate-in fade-in zoom-in-95">
            <CardHeader className="flex flex-row items-center justify-between border-b border-border pb-4">
              <div>
                <CardTitle className="text-base font-bold">Stock Adjustment</CardTitle>
                <CardDescription className="text-xs">{selectedItem.product_name}</CardDescription>
              </div>
              <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setIsAdjustModalOpen(false)}>
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            <form onSubmit={handleAdjustSubmit}>
              <CardContent className="space-y-4 pt-5">
                {/* Current stock breakdown */}
                <div className="p-3 rounded-lg bg-muted/40 text-xs space-y-1.5">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Main WH:</span>
                    <span className="font-bold text-foreground">{selectedItem.main_wh_qty} units</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Sub WH:</span>
                    <span className="font-bold text-foreground">{selectedItem.sub_wh_qty} units</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Machine:</span>
                    <span className="font-bold text-foreground">{selectedItem.machine_qty} units</span>
                  </div>
                  <div className="flex justify-between border-t border-border pt-1.5">
                    <span className="text-muted-foreground font-semibold">Total:</span>
                    <span className="font-bold text-foreground">{selectedItem.total_qty} units</span>
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold">Adjust Which Warehouse *</label>
                  <select
                    className="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-xs"
                    value={adjustWarehouse}
                    onChange={(e) => {
                      setAdjustWarehouse(e.target.value)
                      if (e.target.value === 'main_wh') setNewQty(selectedItem.main_wh_qty)
                      else if (e.target.value === 'sub_wh') setNewQty(selectedItem.sub_wh_qty)
                      else setNewQty(selectedItem.machine_qty)
                    }}
                  >
                    <option value="main_wh">Main Warehouse</option>
                    <option value="sub_wh">Sub Warehouse</option>
                    <option value="machine">Machine Stock</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold">New Verified Count *</label>
                  <Input
                    type="number"
                    min="0"
                    required
                    value={newQty}
                    onChange={(e) => setNewQty(Number(e.target.value))}
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold">Adjustment Reason</label>
                  <select
                    className="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-xs"
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                  >
                    <option value="physical_count">Physical Stock Take / Audit</option>
                    <option value="damaged_in_warehouse">Damaged / Leakage</option>
                    <option value="system_correction">System Discrepancy Correction</option>
                    <option value="expiry">Expired Stock Disposal</option>
                    <option value="transfer">WH Transfer Adjustment</option>
                  </select>
                </div>
              </CardContent>

              <div className="p-4 border-t border-border flex justify-end gap-2 bg-muted/20">
                <Button type="button" variant="outline" size="sm" onClick={() => setIsAdjustModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" size="sm">
                  Update Stock
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  )
}
