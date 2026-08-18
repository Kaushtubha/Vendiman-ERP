import React, { useEffect, useState } from 'react'
import { Plus, Search, Filter, Package, AlertCircle, Edit, Check, X, Barcode } from 'lucide-react'
import apiClient from '@/api/client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

interface Product {
  id: string
  sku: string
  barcode?: string
  name: string
  category_name?: string
  brand?: string
  unit: string
  mrp: number
  cost_price: number
  selling_price: number
  gst_rate: string
  status: string
  reorder_point: number
  reorder_quantity: number
}

const DEFAULT_PRODUCTS: Product[] = [
  { id: '1', sku: 'BEV-RB-250', barcode: '8901030383748', name: 'Red Bull Energy Drink 250ml', brand: 'Red Bull', unit: 'can', mrp: 125, cost_price: 75, selling_price: 125, gst_rate: '18', status: 'active', reorder_point: 10, reorder_quantity: 48 },
  { id: '2', sku: 'BEV-CC-300', barcode: '8901764012207', name: 'Coca Cola Can 300ml', brand: 'Coca-Cola', unit: 'can', mrp: 40, cost_price: 25, selling_price: 40, gst_rate: '18', status: 'active', reorder_point: 15, reorder_quantity: 60 },
  { id: '3', sku: 'SNK-DOR-50', barcode: '8901491101912', name: 'Doritos Cheese Nachos 50g', brand: 'Doritos', unit: 'packet', mrp: 50, cost_price: 30, selling_price: 50, gst_rate: '12', status: 'active', reorder_point: 10, reorder_quantity: 30 },
  { id: '4', sku: 'CHO-SNK-50', barcode: '8901233010488', name: 'Snickers Chocolate Bar 50g', brand: 'Snickers', unit: 'bar', mrp: 50, cost_price: 32, selling_price: 50, gst_rate: '18', status: 'active', reorder_point: 12, reorder_quantity: 50 },
  { id: '5', sku: 'BEV-PB-250', barcode: '8906060100010', name: 'Paper Boat Aamras Mango 250ml', brand: 'Paper Boat', unit: 'pouch', mrp: 35, cost_price: 20, selling_price: 35, gst_rate: '12', status: 'active', reorder_point: 10, reorder_quantity: 40 },
  { id: '6', sku: 'SNK-LAY-50', barcode: '8901491001014', name: 'Lays Classic Salted 50g', brand: 'Lays', unit: 'packet', mrp: 20, cost_price: 12, selling_price: 20, gst_rate: '12', status: 'active', reorder_point: 15, reorder_quantity: 60 },
]

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>(DEFAULT_PRODUCTS)
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(false)
  const [isModalOpen, setIsModalOpen] = useState(false)

  // Form state
  const [form, setForm] = useState({
    sku: '',
    name: '',
    brand: '',
    unit: 'piece',
    mrp: '',
    cost_price: '',
    selling_price: '',
    gst_rate: '18',
    reorder_point: '10',
    reorder_quantity: '50',
  })

  useEffect(() => {
    fetchProducts()
  }, [])

  const fetchProducts = async () => {
    try {
      setLoading(true)
      const res = await apiClient.get('/products')
      if (res.data?.data?.length) {
        setProducts(res.data.data)
      }
    } catch (err) {
      console.log('Using default products list')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    const newProduct: Product = {
      id: String(Date.now()),
      sku: form.sku.toUpperCase(),
      name: form.name,
      brand: form.brand,
      unit: form.unit,
      mrp: Number(form.mrp),
      cost_price: Number(form.cost_price),
      selling_price: Number(form.selling_price || form.mrp),
      gst_rate: form.gst_rate,
      status: 'active',
      reorder_point: Number(form.reorder_point),
      reorder_quantity: Number(form.reorder_quantity),
    }

    try {
      await apiClient.post('/products', {
        ...newProduct,
        mrp: newProduct.mrp,
        cost_price: newProduct.cost_price,
        selling_price: newProduct.selling_price,
      })
    } catch (err) {
      console.log('Saved to local product state')
    }

    setProducts([newProduct, ...products])
    setIsModalOpen(false)
    setForm({
      sku: '',
      name: '',
      brand: '',
      unit: 'piece',
      mrp: '',
      cost_price: '',
      selling_price: '',
      gst_rate: '18',
      reorder_point: '10',
      reorder_quantity: '50',
    })
  }

  const filtered = products.filter(
    (p) =>
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.sku.toLowerCase().includes(search.toLowerCase()) ||
      p.brand?.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Products & Vending Catalog
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Manage slots, pricing matrices, margins, and reorder thresholds
          </p>
        </div>
        <Button onClick={() => setIsModalOpen(true)} className="gap-2 shadow-sm">
          <Plus className="h-4 w-4" />
          Add New Product
        </Button>
      </div>

      {/* Controls Card */}
      <Card className="shadow-sm">
        <CardContent className="p-4 flex flex-col sm:flex-row gap-3 items-center justify-between">
          <div className="relative w-full sm:w-80">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search by SKU, Name, Brand..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 text-xs"
            />
          </div>
          <div className="text-xs text-muted-foreground font-medium">
            Showing <strong className="text-foreground">{filtered.length}</strong> of{' '}
            {products.length} catalog items
          </div>
        </CardContent>
      </Card>

      {/* Data Table */}
      <Card className="shadow-sm overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>SKU & Barcode</TableHead>
              <TableHead>Product Name</TableHead>
              <TableHead>Brand</TableHead>
              <TableHead>MRP</TableHead>
              <TableHead>Cost Price</TableHead>
              <TableHead>Selling Price</TableHead>
              <TableHead>Unit Margin</TableHead>
              <TableHead>GST</TableHead>
              <TableHead>Reorder Pt.</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((p) => {
              const profit = p.selling_price - p.cost_price
              const margin = p.selling_price > 0 ? ((profit / p.selling_price) * 100).toFixed(1) : '0'
              return (
                <TableRow key={p.id} className="hover:bg-muted/40">
                  <TableCell>
                    <div className="font-mono font-bold text-xs text-indigo-600 dark:text-indigo-400">
                      {p.sku}
                    </div>
                    {p.barcode && (
                      <div className="text-[10px] text-muted-foreground flex items-center gap-1 mt-0.5">
                        <Barcode className="h-3 w-3" />
                        {p.barcode}
                      </div>
                    )}
                  </TableCell>
                  <TableCell className="font-medium">{p.name}</TableCell>
                  <TableCell className="text-muted-foreground text-xs">{p.brand || '—'}</TableCell>
                  <TableCell className="font-semibold">₹{p.mrp}</TableCell>
                  <TableCell className="text-muted-foreground">₹{p.cost_price}</TableCell>
                  <TableCell className="font-semibold text-foreground">₹{p.selling_price}</TableCell>
                  <TableCell>
                    <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                      +₹{profit} ({margin}%)
                    </span>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">{p.gst_rate}%</TableCell>
                  <TableCell className="text-xs font-semibold">{p.reorder_point} {p.unit}s</TableCell>
                  <TableCell>
                    <Badge variant="success">Active</Badge>
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </Card>

      {/* ── Add Product Modal ── */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <Card className="w-full max-w-lg bg-card border-border shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            <CardHeader className="flex flex-row items-center justify-between border-b border-border pb-4">
              <div>
                <CardTitle className="text-base font-bold">Add Product to Catalog</CardTitle>
                <CardDescription className="text-xs">Define SKU, pricing matrix, and reorder levels</CardDescription>
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => setIsModalOpen(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            <form onSubmit={handleCreate}>
              <CardContent className="space-y-4 pt-5 max-h-[70vh] overflow-y-auto">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-foreground">SKU Code *</label>
                    <Input
                      required
                      placeholder="e.g. BEV-COKE-300"
                      value={form.sku}
                      onChange={(e) => setForm({ ...form, sku: e.target.value })}
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-foreground">Brand</label>
                    <Input
                      placeholder="e.g. Coca-Cola"
                      value={form.brand}
                      onChange={(e) => setForm({ ...form, brand: e.target.value })}
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-foreground">Product Full Name *</label>
                  <Input
                    required
                    placeholder="e.g. Coca Cola Can 300ml"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                  />
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-foreground">Cost Price (₹) *</label>
                    <Input
                      type="number"
                      required
                      placeholder="25.00"
                      value={form.cost_price}
                      onChange={(e) => setForm({ ...form, cost_price: e.target.value })}
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-foreground">Selling Price (₹) *</label>
                    <Input
                      type="number"
                      required
                      placeholder="40.00"
                      value={form.selling_price}
                      onChange={(e) => setForm({ ...form, selling_price: e.target.value })}
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-foreground">MRP (₹) *</label>
                    <Input
                      type="number"
                      required
                      placeholder="40.00"
                      value={form.mrp}
                      onChange={(e) => setForm({ ...form, mrp: e.target.value })}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-foreground">Reorder Point (Min)</label>
                    <Input
                      type="number"
                      value={form.reorder_point}
                      onChange={(e) => setForm({ ...form, reorder_point: e.target.value })}
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-foreground">Reorder Batch Qty</label>
                    <Input
                      type="number"
                      value={form.reorder_quantity}
                      onChange={(e) => setForm({ ...form, reorder_quantity: e.target.value })}
                    />
                  </div>
                </div>
              </CardContent>

              <div className="p-4 border-t border-border flex justify-end gap-2 bg-muted/20">
                <Button type="button" variant="outline" size="sm" onClick={() => setIsModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" size="sm">
                  Save Product
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  )
}
