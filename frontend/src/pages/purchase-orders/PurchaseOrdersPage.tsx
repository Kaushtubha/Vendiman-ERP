import React, { useEffect, useState } from 'react'
import { Plus, Search, FileSpreadsheet, CheckCircle2, Clock, X, ArrowRight, Layers } from 'lucide-react'
import apiClient from '@/api/client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

interface PurchaseOrder {
  id: string
  po_number: string
  supplier_name: string
  warehouse_name: string
  status: string
  order_date: string
  expected_delivery_date?: string
  total_amount: number
}

const DEFAULT_POS: PurchaseOrder[] = [
  { id: '1', po_number: 'PO-202608-A93F1', supplier_name: 'Hindustan Bottling & Beverages', warehouse_name: 'Main Dark Store Bengaluru', status: 'approved', order_date: '2026-08-16', expected_delivery_date: '2026-08-18', total_amount: 14500 },
  { id: '2', po_number: 'PO-202608-B82K2', supplier_name: 'Varun Beverages Limited', warehouse_name: 'Main Dark Store Bengaluru', status: 'fully_received', order_date: '2026-08-14', expected_delivery_date: '2026-08-16', total_amount: 22800 },
  { id: '3', po_number: 'PO-202608-C19X4', supplier_name: 'PepsiCo Snack Distribution', warehouse_name: 'Dark Store Whitefield', status: 'draft', order_date: '2026-08-17', expected_delivery_date: '2026-08-20', total_amount: 8900 },
]

export default function PurchaseOrdersPage() {
  const [pos, setPos] = useState<PurchaseOrder[]>(DEFAULT_POS)
  const [search, setSearch] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)

  // PO form state
  const [supplierName, setSupplierName] = useState('Hindustan Bottling & Beverages')
  const [lines, setLines] = useState([
    { product: 'Red Bull Energy Drink 250ml', qty: 48, unit_price: 75 },
    { product: 'Coca Cola Can 300ml', qty: 60, unit_price: 25 },
  ])

  useEffect(() => {
    fetchPOs()
  }, [])

  const fetchPOs = async () => {
    try {
      const res = await apiClient.get('/purchase-orders')
      if (res.data?.data?.length) setPos(res.data.data)
    } catch (err) {
      console.log('Using default PO dataset')
    }
  }

  const addLine = () => {
    setLines([...lines, { product: 'Doritos Cheese Nachos 50g', qty: 30, unit_price: 30 }])
  }

  const removeLine = (idx: number) => {
    setLines(lines.filter((_, i) => i !== idx))
  }

  const totalAmount = lines.reduce((acc, curr) => acc + curr.qty * curr.unit_price, 0)
  const totalTax = totalAmount * 0.18

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    const newPO: PurchaseOrder = {
      id: String(Date.now()),
      po_number: `PO-202608-${Math.random().toString(36).substring(2, 7).toUpperCase()}`,
      supplier_name: supplierName,
      warehouse_name: 'Main Dark Store Bengaluru',
      status: 'approved',
      order_date: new Date().toISOString().split('T')[0],
      expected_delivery_date: new Date(Date.now() + 86400000 * 2).toISOString().split('T')[0],
      total_amount: Math.round(totalAmount + totalTax),
    }

    setPos([newPO, ...pos])
    setIsModalOpen(false)
  }

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'approved':
        return <Badge variant="info">Approved</Badge>
      case 'fully_received':
        return <Badge variant="success">Fully Received</Badge>
      case 'draft':
        return <Badge variant="secondary">Draft</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Purchase Orders (Procurement)
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Create, approve, and track vendor replenishment purchase orders
          </p>
        </div>
        <Button onClick={() => setIsModalOpen(true)} className="gap-2 shadow-sm">
          <Plus className="h-4 w-4" />
          Create Purchase Order
        </Button>
      </div>

      {/* Filter and summary card */}
      <Card className="shadow-sm">
        <CardContent className="p-4 flex flex-col sm:flex-row gap-3 items-center justify-between">
          <div className="relative w-full sm:w-80">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search by PO Number, Supplier..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 text-xs"
            />
          </div>
          <div className="text-xs text-muted-foreground font-medium">
            Open POs: <strong className="text-foreground">{pos.filter((p) => p.status === 'approved').length}</strong> pending receipt
          </div>
        </CardContent>
      </Card>

      {/* PO Table */}
      <Card className="shadow-sm overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>PO Number</TableHead>
              <TableHead>Supplier Name</TableHead>
              <TableHead>Destination Warehouse</TableHead>
              <TableHead>Order Date</TableHead>
              <TableHead>Expected Delivery</TableHead>
              <TableHead>Total PO Amount</TableHead>
              <TableHead>Lifecycle Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {pos.map((p) => (
              <TableRow key={p.id} className="hover:bg-muted/40">
                <TableCell className="font-mono font-bold text-xs text-indigo-600 dark:text-indigo-400">
                  {p.po_number}
                </TableCell>
                <TableCell className="font-medium text-foreground">{p.supplier_name}</TableCell>
                <TableCell className="text-xs text-muted-foreground">{p.warehouse_name}</TableCell>
                <TableCell className="text-xs">{p.order_date}</TableCell>
                <TableCell className="text-xs text-muted-foreground">{p.expected_delivery_date || '—'}</TableCell>
                <TableCell className="font-bold text-foreground">₹{p.total_amount.toLocaleString('en-IN')}</TableCell>
                <TableCell>{getStatusBadge(p.status)}</TableCell>
                <TableCell className="text-right">
                  <Button variant="ghost" size="sm" className="h-7 text-xs text-primary">
                    View Details →
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>

      {/* Create PO Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <Card className="w-full max-w-2xl bg-card border-border shadow-2xl animate-in fade-in zoom-in-95">
            <CardHeader className="flex flex-row items-center justify-between border-b border-border pb-4">
              <div>
                <CardTitle className="text-base font-bold">New Purchase Order</CardTitle>
                <CardDescription className="text-xs">Raise replenishment order to supplier</CardDescription>
              </div>
              <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setIsModalOpen(false)}>
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            <form onSubmit={handleCreate}>
              <CardContent className="space-y-4 pt-5 max-h-[70vh] overflow-y-auto">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-xs font-semibold">Select Supplier</label>
                    <select
                      className="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-xs"
                      value={supplierName}
                      onChange={(e) => setSupplierName(e.target.value)}
                    >
                      <option>Hindustan Bottling & Beverages</option>
                      <option>Varun Beverages Limited</option>
                      <option>PepsiCo Snack Distribution</option>
                      <option>Mars Wrigley Confectionery India</option>
                    </select>
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold">Target Warehouse</label>
                    <select className="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-xs">
                      <option>Main Dark Store Bengaluru</option>
                      <option>Dark Store Whitefield</option>
                      <option>Dark Store Indiranagar</option>
                    </select>
                  </div>
                </div>

                {/* Line Items List */}
                <div className="space-y-2 pt-2">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-bold text-foreground">PO Line Items</span>
                    <Button type="button" variant="outline" size="sm" onClick={addLine} className="h-7 text-xs">
                      + Add Item
                    </Button>
                  </div>

                  <div className="space-y-2">
                    {lines.map((line, idx) => (
                      <div key={idx} className="flex items-center gap-2 p-2.5 rounded-lg border border-border bg-muted/20">
                        <div className="flex-1 text-xs font-medium">{line.product}</div>
                        <div className="w-20 text-xs">
                          <label className="text-[10px] text-muted-foreground block">Qty</label>
                          <input
                            type="number"
                            className="w-full bg-background border border-input rounded px-2 py-0.5 text-xs"
                            value={line.qty}
                            onChange={(e) => {
                              const updated = [...lines]
                              updated[idx].qty = Number(e.target.value)
                              setLines(updated)
                            }}
                          />
                        </div>
                        <div className="w-24 text-xs">
                          <label className="text-[10px] text-muted-foreground block">Cost (₹)</label>
                          <input
                            type="number"
                            className="w-full bg-background border border-input rounded px-2 py-0.5 text-xs"
                            value={line.unit_price}
                            onChange={(e) => {
                              const updated = [...lines]
                              updated[idx].unit_price = Number(e.target.value)
                              setLines(updated)
                            }}
                          />
                        </div>
                        <div className="w-24 text-right font-semibold text-xs pt-3">
                          ₹{(line.qty * line.unit_price).toLocaleString('en-IN')}
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 text-destructive"
                          onClick={() => removeLine(idx)}
                        >
                          <X className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    ))}
                  </div>

                  {/* Summary */}
                  <div className="p-3 rounded-lg bg-muted/40 text-xs space-y-1.5 font-medium">
                    <div className="flex justify-between text-muted-foreground">
                      <span>Subtotal</span>
                      <span>₹{totalAmount.toLocaleString('en-IN')}</span>
                    </div>
                    <div className="flex justify-between text-muted-foreground">
                      <span>Estimated GST (18%)</span>
                      <span>₹{totalTax.toLocaleString('en-IN')}</span>
                    </div>
                    <div className="flex justify-between text-sm font-bold text-foreground border-t border-border pt-1.5">
                      <span>Grand Total</span>
                      <span className="text-primary">₹{(totalAmount + totalTax).toLocaleString('en-IN')}</span>
                    </div>
                  </div>
                </div>
              </CardContent>

              <div className="p-4 border-t border-border flex justify-end gap-2 bg-muted/20">
                <Button type="button" variant="outline" size="sm" onClick={() => setIsModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" size="sm">
                  Issue & Approve PO
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  )
}
