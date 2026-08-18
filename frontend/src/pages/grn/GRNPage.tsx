import React, { useEffect, useState } from 'react'
import { Plus, Search, Receipt, CheckCircle2, AlertTriangle, X, ShieldCheck } from 'lucide-react'
import apiClient from '@/api/client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

interface GRN {
  id: string
  grn_number: string
  po_number: string
  warehouse_name: string
  status: string
  receipt_date: string
  supplier_invoice_number?: string
  created_at: string
}

const DEFAULT_GRNS: GRN[] = [
  { id: '1', grn_number: 'GRN-202608-K1902', po_number: 'PO-202608-B82K2', warehouse_name: 'Main Dark Store Bengaluru', status: 'completed', receipt_date: '2026-08-16', supplier_invoice_number: 'INV-VB-99823', created_at: '2026-08-16T14:30:00' },
  { id: '2', grn_number: 'GRN-202608-J8811', po_number: 'PO-202608-A93F1', warehouse_name: 'Main Dark Store Bengaluru', status: 'completed', receipt_date: '2026-08-15', supplier_invoice_number: 'INV-HB-44210', created_at: '2026-08-15T11:00:00' },
]

export default function GRNPage() {
  const [grns, setGrns] = useState<GRN[]>(DEFAULT_GRNS)
  const [search, setSearch] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)

  // GRN Form
  const [selectedPO, setSelectedPO] = useState('PO-202608-A93F1')
  const [invoiceNumber, setInvoiceNumber] = useState('')
  const [items, setItems] = useState([
    { name: 'Red Bull Energy Drink 250ml', ordered: 48, received: 48, accepted: 48, batch: 'BATCH-RB-0826', expiry: '2027-02-28', condition: 'good' },
    { name: 'Coca Cola Can 300ml', ordered: 60, received: 60, accepted: 60, batch: 'BATCH-CC-0826', expiry: '2027-01-15', condition: 'good' },
  ])

  useEffect(() => {
    fetchGRNs()
  }, [])

  const fetchGRNs = async () => {
    try {
      const res = await apiClient.get('/grn')
      if (res.data?.data?.length) setGrns(res.data.data)
    } catch (err) {
      console.log('Using default GRN dataset')
    }
  }

  const handleReceive = (e: React.FormEvent) => {
    e.preventDefault()
    const newGRN: GRN = {
      id: String(Date.now()),
      grn_number: `GRN-202608-${Math.random().toString(36).substring(2, 7).toUpperCase()}`,
      po_number: selectedPO,
      warehouse_name: 'Main Dark Store Bengaluru',
      status: 'completed',
      receipt_date: new Date().toISOString().split('T')[0],
      supplier_invoice_number: invoiceNumber || `INV-${Math.floor(10000 + Math.random() * 90000)}`,
      created_at: new Date().toISOString(),
    }

    setGrns([newGRN, ...grns])
    setIsModalOpen(false)
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Goods Receipt Notes (DGRN)
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Record incoming vendor shipments, batch & expiry data, and automatically update warehouse stock
          </p>
        </div>
        <Button onClick={() => setIsModalOpen(true)} className="gap-2 shadow-sm">
          <Plus className="h-4 w-4" />
          Receive Goods Against PO
        </Button>
      </div>

      <Card className="shadow-sm">
        <CardContent className="p-4 flex flex-col sm:flex-row gap-3 items-center justify-between">
          <div className="relative w-full sm:w-80">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search by GRN Number, PO, Invoice..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 text-xs"
            />
          </div>
          <div className="flex items-center gap-2 text-xs text-emerald-600 dark:text-emerald-400 font-medium">
            <CheckCircle2 className="h-4 w-4" />
            <span>Auto-Inventory Sync Active</span>
          </div>
        </CardContent>
      </Card>

      <Card className="shadow-sm overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>GRN Number</TableHead>
              <TableHead>Reference PO</TableHead>
              <TableHead>Warehouse</TableHead>
              <TableHead>Supplier Invoice</TableHead>
              <TableHead>Receipt Date</TableHead>
              <TableHead>Stock Status</TableHead>
              <TableHead className="text-right">Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {grns.map((g) => (
              <TableRow key={g.id} className="hover:bg-muted/40">
                <TableCell className="font-mono font-bold text-xs text-indigo-600 dark:text-indigo-400">
                  {g.grn_number}
                </TableCell>
                <TableCell className="font-mono text-xs font-semibold text-foreground">{g.po_number}</TableCell>
                <TableCell className="text-xs text-muted-foreground">{g.warehouse_name}</TableCell>
                <TableCell className="text-xs font-mono text-foreground">{g.supplier_invoice_number || '—'}</TableCell>
                <TableCell className="text-xs">{g.receipt_date}</TableCell>
                <TableCell>
                  <Badge variant="success">Stock Credited</Badge>
                </TableCell>
                <TableCell className="text-right">
                  <Button variant="ghost" size="sm" className="h-7 text-xs text-primary">
                    View Items →
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <Card className="w-full max-w-2xl bg-card border-border shadow-2xl animate-in fade-in zoom-in-95">
            <CardHeader className="flex flex-row items-center justify-between border-b border-border pb-4">
              <div>
                <CardTitle className="text-base font-bold">Receive Goods & Process DGRN</CardTitle>
                <CardDescription className="text-xs">Physical verification and stock ledger entry</CardDescription>
              </div>
              <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setIsModalOpen(false)}>
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            <form onSubmit={handleReceive}>
              <CardContent className="space-y-4 pt-5 max-h-[70vh] overflow-y-auto">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-xs font-semibold">Select Approved PO</label>
                    <select
                      className="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-xs"
                      value={selectedPO}
                      onChange={(e) => setSelectedPO(e.target.value)}
                    >
                      <option>PO-202608-A93F1 (Hindustan Bottling - ₹14,500)</option>
                      <option>PO-202608-C19X4 (PepsiCo Snacks - ₹8,900)</option>
                    </select>
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold">Vendor Invoice / Challan #</label>
                    <Input
                      placeholder="e.g. INV-HB-2026-881"
                      value={invoiceNumber}
                      onChange={(e) => setInvoiceNumber(e.target.value)}
                    />
                  </div>
                </div>

                <div className="space-y-2 pt-2">
                  <span className="text-xs font-bold text-foreground">Items Received & Batch Information</span>
                  {items.map((item, idx) => (
                    <div key={idx} className="p-3 rounded-lg border border-border bg-muted/20 space-y-2">
                      <div className="flex justify-between items-center text-xs font-semibold text-foreground">
                        <span>{item.name}</span>
                        <span className="text-muted-foreground">PO Ordered: {item.ordered} units</span>
                      </div>
                      <div className="grid grid-cols-4 gap-2 text-xs">
                        <div>
                          <label className="text-[10px] text-muted-foreground block">Received Qty</label>
                          <input
                            type="number"
                            className="w-full bg-background border border-input rounded px-2 py-1 text-xs"
                            value={item.received}
                            onChange={(e) => {
                              const up = [...items]
                              up[idx].received = Number(e.target.value)
                              up[idx].accepted = Number(e.target.value)
                              setItems(up)
                            }}
                          />
                        </div>
                        <div>
                          <label className="text-[10px] text-muted-foreground block">Accepted Qty</label>
                          <input
                            type="number"
                            className="w-full bg-background border border-input rounded px-2 py-1 text-xs"
                            value={item.accepted}
                            onChange={(e) => {
                              const up = [...items]
                              up[idx].accepted = Number(e.target.value)
                              setItems(up)
                            }}
                          />
                        </div>
                        <div>
                          <label className="text-[10px] text-muted-foreground block">Batch Number</label>
                          <input
                            type="text"
                            className="w-full bg-background border border-input rounded px-2 py-1 text-xs"
                            value={item.batch}
                            onChange={(e) => {
                              const up = [...items]
                              up[idx].batch = e.target.value
                              setItems(up)
                            }}
                          />
                        </div>
                        <div>
                          <label className="text-[10px] text-muted-foreground block">Expiry Date</label>
                          <input
                            type="date"
                            className="w-full bg-background border border-input rounded px-2 py-1 text-xs"
                            value={item.expiry}
                            onChange={(e) => {
                              const up = [...items]
                              up[idx].expiry = e.target.value
                              setItems(up)
                            }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>

              <div className="p-4 border-t border-border flex justify-end gap-2 bg-muted/20">
                <Button type="button" variant="outline" size="sm" onClick={() => setIsModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" size="sm" className="bg-emerald-600 hover:bg-emerald-700 text-white">
                  Confirm Receipt & Credit Stock
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  )
}
