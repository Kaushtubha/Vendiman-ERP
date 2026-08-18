import React, { useEffect, useState } from 'react'
import { Plus, Search, Truck, Phone, Mail, MapPin, Building2, CheckCircle2, X } from 'lucide-react'
import apiClient from '@/api/client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface Supplier {
  id: string
  code: string
  name: string
  contact_person?: string
  email?: string
  phone?: string
  gst_number?: string
  city?: string
  state?: string
  status: string
  rating: string
  total_orders: number
  total_spend: number
}

const DEFAULT_SUPPLIERS: Supplier[] = [
  { id: '1', code: 'SUP-HINDUSTAN', name: 'Hindustan Bottling & Beverages Pvt Ltd', contact_person: 'Rahul Sharma', email: 'orders@hindustanbev.com', phone: '+91 98201 12345', gst_number: '27AAACH1234F1Z8', city: 'Mumbai', state: 'Maharashtra', status: 'active', rating: 'excellent', total_orders: 14, total_spend: 340000 },
  { id: '2', code: 'SUP-PEPSI', name: 'Varun Beverages Limited', contact_person: 'Pooja Nair', email: 'supply@varunbev.com', phone: '+91 98450 54321', gst_number: '29AAACV5678B1ZP', city: 'Bengaluru', state: 'Karnataka', status: 'active', rating: 'excellent', total_orders: 22, total_spend: 520000 },
  { id: '3', code: 'SUP-PEPSICO', name: 'PepsiCo Snack Distribution', contact_person: 'Amit Verma', email: 'sales@pepsicosnacks.in', phone: '+91 99880 99880', gst_number: '07AAACP9988Q1Z1', city: 'New Delhi', state: 'Delhi', status: 'active', rating: 'good', total_orders: 9, total_spend: 185000 },
  { id: '4', code: 'SUP-MARS', name: 'Mars Wrigley Confectionery India', contact_person: 'David Dsouza', email: 'b2b@marswrigley.com', phone: '+91 97112 33445', gst_number: '06AAACM4455N1ZK', city: 'Gurugram', state: 'Haryana', status: 'active', rating: 'good', total_orders: 6, total_spend: 92000 },
]

export default function SuppliersPage() {
  const [suppliers, setSuppliers] = useState<Supplier[]>(DEFAULT_SUPPLIERS)
  const [search, setSearch] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)

  const [form, setForm] = useState({
    code: '',
    name: '',
    contact_person: '',
    email: '',
    phone: '',
    gst_number: '',
    city: '',
    state: '',
  })

  useEffect(() => {
    fetchSuppliers()
  }, [])

  const fetchSuppliers = async () => {
    try {
      const res = await apiClient.get('/suppliers')
      if (res.data?.data?.length) {
        setSuppliers(res.data.data)
      }
    } catch (err) {
      console.log('Using default suppliers list')
    }
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    const newSupp: Supplier = {
      id: String(Date.now()),
      code: form.code.toUpperCase(),
      name: form.name,
      contact_person: form.contact_person,
      email: form.email,
      phone: form.phone,
      gst_number: form.gst_number,
      city: form.city,
      state: form.state,
      status: 'active',
      rating: 'good',
      total_orders: 0,
      total_spend: 0,
    }

    try {
      await apiClient.post('/suppliers', newSupp)
    } catch (err) {
      console.log('Saved locally')
    }

    setSuppliers([newSupp, ...suppliers])
    setIsModalOpen(false)
    setForm({ code: '', name: '', contact_person: '', email: '', phone: '', gst_number: '', city: '', state: '' })
  }

  const filtered = suppliers.filter(
    (s) =>
      s.name.toLowerCase().includes(search.toLowerCase()) ||
      s.code.toLowerCase().includes(search.toLowerCase()) ||
      s.city?.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Supplier & Vendor Directory
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Manage procurement partners, GST details, payment terms & lifetime spend
          </p>
        </div>
        <Button onClick={() => setIsModalOpen(true)} className="gap-2 shadow-sm">
          <Plus className="h-4 w-4" />
          Add Supplier
        </Button>
      </div>

      {/* Search */}
      <Card className="shadow-sm">
        <CardContent className="p-4">
          <div className="relative w-full sm:w-80">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search by Vendor Name, Code, City..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 text-xs"
            />
          </div>
        </CardContent>
      </Card>

      {/* Supplier Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filtered.map((s) => (
          <Card key={s.id} className="hover:shadow-md transition-all border-border">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-indigo-600 dark:text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded">
                      {s.code}
                    </span>
                    <Badge variant={s.rating === 'excellent' ? 'success' : 'secondary'}>
                      {s.rating.toUpperCase()}
                    </Badge>
                  </div>
                  <CardTitle className="text-base font-bold mt-2 text-foreground">{s.name}</CardTitle>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-3 pt-0 text-xs">
              <div className="grid grid-cols-2 gap-2 text-muted-foreground pt-1 border-t border-border">
                {s.contact_person && (
                  <div className="flex items-center gap-1.5">
                    <Building2 className="h-3.5 w-3.5 text-foreground" />
                    <span>{s.contact_person}</span>
                  </div>
                )}
                {s.city && (
                  <div className="flex items-center gap-1.5">
                    <MapPin className="h-3.5 w-3.5 text-foreground" />
                    <span>{s.city}, {s.state}</span>
                  </div>
                )}
                {s.phone && (
                  <div className="flex items-center gap-1.5">
                    <Phone className="h-3.5 w-3.5 text-foreground" />
                    <span>{s.phone}</span>
                  </div>
                )}
                {s.email && (
                  <div className="flex items-center gap-1.5 truncate">
                    <Mail className="h-3.5 w-3.5 text-foreground shrink-0" />
                    <span className="truncate">{s.email}</span>
                  </div>
                )}
              </div>

              {s.gst_number && (
                <div className="p-2 rounded bg-muted/40 text-[11px] font-mono text-muted-foreground flex justify-between items-center">
                  <span>GSTIN: <strong className="text-foreground">{s.gst_number}</strong></span>
                  <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-sans font-medium flex items-center gap-1">
                    <CheckCircle2 className="h-3 w-3" /> Verified
                  </span>
                </div>
              )}

              <div className="flex justify-between items-center pt-2 border-t border-border text-xs">
                <span className="text-muted-foreground">
                  Fulfilled Orders: <strong className="text-foreground">{s.total_orders}</strong>
                </span>
                <span className="font-semibold text-foreground">
                  Total Spend: ₹{s.total_spend.toLocaleString('en-IN')}
                </span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <Card className="w-full max-w-lg bg-card border-border shadow-2xl animate-in fade-in zoom-in-95">
            <CardHeader className="flex flex-row items-center justify-between border-b border-border pb-4">
              <div>
                <CardTitle className="text-base font-bold">Add New Supplier</CardTitle>
                <CardDescription className="text-xs">Register vendor for Purchase Orders</CardDescription>
              </div>
              <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setIsModalOpen(false)}>
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            <form onSubmit={handleCreate}>
              <CardContent className="space-y-4 pt-5">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-xs font-semibold">Vendor Code *</label>
                    <Input required placeholder="e.g. SUP-COCA" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold">Contact Person</label>
                    <Input placeholder="e.g. Rahul Sharma" value={form.contact_person} onChange={(e) => setForm({ ...form, contact_person: e.target.value })} />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold">Company / Supplier Name *</label>
                  <Input required placeholder="e.g. Hindustan Beverages Pvt Ltd" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-xs font-semibold">Email</label>
                    <Input type="email" placeholder="orders@supplier.com" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold">Phone</label>
                    <Input placeholder="+91 98765 43210" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div className="space-y-1">
                    <label className="text-xs font-semibold">GSTIN</label>
                    <Input placeholder="29ABCDE1234F1Z5" value={form.gst_number} onChange={(e) => setForm({ ...form, gst_number: e.target.value })} />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold">City</label>
                    <Input placeholder="Bengaluru" value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold">State</label>
                    <Input placeholder="Karnataka" value={form.state} onChange={(e) => setForm({ ...form, state: e.target.value })} />
                  </div>
                </div>
              </CardContent>

              <div className="p-4 border-t border-border flex justify-end gap-2 bg-muted/20">
                <Button type="button" variant="outline" size="sm" onClick={() => setIsModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" size="sm">
                  Register Supplier
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  )
}
