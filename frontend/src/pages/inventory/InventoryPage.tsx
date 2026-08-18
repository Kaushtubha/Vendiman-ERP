import React, { useEffect, useState } from 'react'
import { Search, Warehouse, AlertTriangle, ArrowUpDown, History, Plus, CheckCircle2, Sliders, X } from 'lucide-react'
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
  warehouse_name: string
  quantity_on_hand: number
  quantity_reserved: number
  available_quantity: number
  reorder_point: number
  is_low_stock: boolean
}

const DEFAULT_STOCKS: StockItem[] = [
  { id: '1', product_id: 'p1', product_sku: 'BEV-RB-250', product_name: 'Red Bull Energy Drink 250ml', warehouse_name: 'Main Dark Store Bengaluru', quantity_on_hand: 24, quantity_reserved: 2, available_quantity: 22, reorder_point: 10, is_low_stock: false },
  { id: '2', product_id: 'p2', product_sku: 'BEV-CC-300', product_name: 'Coca Cola Can 300ml', warehouse_name: 'Main Dark Store Bengaluru', quantity_on_hand: 32, quantity_reserved: 0, available_quantity: 32, reorder_point: 15, is_low_stock: false },
  { id: '3', product_id: 'p3', product_sku: 'SNK-DOR-50', product_name: 'Doritos Cheese Nachos 50g', warehouse_name: 'Main Dark Store Bengaluru', quantity_on_hand: 18, quantity_reserved: 0, available_quantity: 18, reorder_point: 10, is_low_stock: false },
  { id: '4', product_id: 'p4', product_sku: 'CHO-SNK-50', product_name: 'Snickers Chocolate Bar 50g', warehouse_name: 'Main Dark Store Bengaluru', quantity_on_hand: 8, quantity_reserved: 1, available_quantity: 7, reorder_point: 12, is_low_stock: true },
  { id: '5', product_id: 'p5', product_sku: 'SNK-LAY-50', product_name: 'Lays Classic Salted 50g', warehouse_name: 'Main Dark Store Bengaluru', quantity_on_hand: 4, quantity_reserved: 0, available_quantity: 4, reorder_point: 15, is_low_stock: true },
]

export default function InventoryPage() {
  const [stocks, setStocks] = useState<StockItem[]>(DEFAULT_STOCKS)
  const [search, setSearch] = useState('')
  const [lowStockFilter, setLowStockFilter] = useState(false)
  const [isAdjustModalOpen, setIsAdjustModalOpen] = useState(false)
  const [selectedItem, setSelectedItem] = useState<StockItem | null>(null)
  const [newQty, setNewQty] = useState<number>(0)
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
    setNewQty(item.quantity_on_hand)
    setIsAdjustModalOpen(true)
  }

  const handleAdjustSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedItem) return

    setStocks(
      stocks.map((s) =>
        s.id === selectedItem.id
          ? {
              ...s,
              quantity_on_hand: newQty,
              available_quantity: newQty - s.quantity_reserved,
              is_low_stock: newQty <= s.reorder_point,
            }
          : s
      )
    )
    setIsAdjustModalOpen(false)
  }

  const filtered = stocks.filter((s) => {
    const matchesSearch =
      s.product_name.toLowerCase().includes(search.toLowerCase()) ||
      s.product_sku.toLowerCase().includes(search.toLowerCase())
    if (lowStockFilter) return matchesSearch && s.is_low_stock
    return matchesSearch
  })

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Inventory & Stock Balances
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Physical stock on hand, reserved quantities for active orders, and ledger adjustments
          </p>
        </div>
      </div>

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
          <div className="flex items-center gap-2">
            <Button
              variant={lowStockFilter ? 'default' : 'outline'}
              size="sm"
              onClick={() => setLowStockFilter(!lowStockFilter)}
              className="text-xs gap-1.5"
            >
              <AlertTriangle className="h-3.5 w-3.5" />
              Low Stock Only ({stocks.filter((s) => s.is_low_stock).length})
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card className="shadow-sm overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>SKU</TableHead>
              <TableHead>Product Name</TableHead>
              <TableHead>Warehouse</TableHead>
              <TableHead>On Hand</TableHead>
              <TableHead>Reserved</TableHead>
              <TableHead>Available</TableHead>
              <TableHead>Reorder Threshold</TableHead>
              <TableHead>Health Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((s) => (
              <TableRow key={s.id} className="hover:bg-muted/40">
                <TableCell className="font-mono font-bold text-xs text-indigo-600 dark:text-indigo-400">
                  {s.product_sku}
                </TableCell>
                <TableCell className="font-medium text-foreground">{s.product_name}</TableCell>
                <TableCell className="text-xs text-muted-foreground">{s.warehouse_name}</TableCell>
                <TableCell className="font-bold text-foreground">{s.quantity_on_hand} units</TableCell>
                <TableCell className="text-muted-foreground">{s.quantity_reserved} units</TableCell>
                <TableCell className="font-bold text-emerald-600 dark:text-emerald-400">
                  {s.available_quantity} units
                </TableCell>
                <TableCell className="text-xs text-muted-foreground">{s.reorder_point} units</TableCell>
                <TableCell>
                  {s.is_low_stock ? (
                    <Badge variant="warning">Low Stock</Badge>
                  ) : (
                    <Badge variant="success">Optimal</Badge>
                  )}
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
            ))}
          </TableBody>
        </Table>
      </Card>

      {/* Adjust Modal */}
      {isAdjustModalOpen && selectedItem && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <Card className="w-full max-w-md bg-card border-border shadow-2xl animate-in fade-in zoom-in-95">
            <CardHeader className="flex flex-row items-center justify-between border-b border-border pb-4">
              <div>
                <CardTitle className="text-base font-bold">Manual Stock Adjustment</CardTitle>
                <CardDescription className="text-xs">{selectedItem.product_name}</CardDescription>
              </div>
              <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setIsAdjustModalOpen(false)}>
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            <form onSubmit={handleAdjustSubmit}>
              <CardContent className="space-y-4 pt-5">
                <div className="p-3 rounded-lg bg-muted/40 text-xs flex justify-between">
                  <span className="text-muted-foreground">Current Count on Hand:</span>
                  <span className="font-bold text-foreground">{selectedItem.quantity_on_hand} units</span>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold">New Verified Physical Count *</label>
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
                  </select>
                </div>
              </CardContent>

              <div className="p-4 border-t border-border flex justify-end gap-2 bg-muted/20">
                <Button type="button" variant="outline" size="sm" onClick={() => setIsAdjustModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" size="sm">
                  Write to Ledger
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  )
}
