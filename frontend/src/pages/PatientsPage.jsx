import { useState } from 'react'
import { Plus, Search } from 'lucide-react'
import { usePatients } from '../hooks/usePatients'
import PatientCard from '../components/PatientCard'
import api from '../utils/api'
import { BLOOD_GROUPS, GENDERS } from '../utils/constants'

export default function PatientsPage() {
  const { patients, loading, refetch } = usePatients()
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ patient_code: '', name: '', age: '', gender: '', height: '', weight: '', blood_group: '' })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const filtered = patients.filter(p =>
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    p.patient_code.toLowerCase().includes(search.toLowerCase())
  )

  const handleCreate = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await api.patients.create({
        ...form,
        age: form.age ? parseInt(form.age) : null,
        height: form.height ? parseFloat(form.height) : null,
        weight: form.weight ? parseFloat(form.weight) : null,
      })
      setShowForm(false)
      setForm({ patient_code: '', name: '', age: '', gender: '', height: '', weight: '', blood_group: '' })
      refetch()
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-brand-900">Patients</h1>
          <p className="text-brand-700/80 text-sm">{patients.length} registered patients</p>
        </div>
        <button onClick={() => setShowForm(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> New Patient
        </button>
      </div>

      {/* Search */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-brand-700/60" />
        <input
          type="text"
          className="input-field pl-10"
          placeholder="Search by name or code…"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      {/* Patient grid */}
      {loading ? (
        <div className="text-brand-700/80 text-sm">Loading…</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map(p => <PatientCard key={p.id} patient={p} />)}
          {filtered.length === 0 && (
            <p className="text-brand-700/60 text-sm col-span-full text-center py-8">No patients found.</p>
          )}
        </div>
      )}

      {/* Create form modal */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="absolute inset-0 bg-black/70" onClick={() => setShowForm(false)} />
          <div className="relative glass-card w-full max-w-lg p-6 animate-slide-in">
            <h2 className="text-lg font-bold text-brand-900 mb-4">New Patient</h2>
            <form onSubmit={handleCreate} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-brand-700/80 mb-1">Patient Code *</label>
                  <input className="input-field" placeholder="BCG-006" value={form.patient_code} onChange={e => setForm(f => ({ ...f, patient_code: e.target.value }))} required />
                </div>
                <div>
                  <label className="block text-xs text-brand-700/80 mb-1">Full Name *</label>
                  <input className="input-field" placeholder="Full name" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} required />
                </div>
                <div>
                  <label className="block text-xs text-brand-700/80 mb-1">Age</label>
                  <input type="number" className="input-field" placeholder="Age" value={form.age} onChange={e => setForm(f => ({ ...f, age: e.target.value }))} />
                </div>
                <div>
                  <label className="block text-xs text-brand-700/80 mb-1">Gender</label>
                  <select className="input-field" value={form.gender} onChange={e => setForm(f => ({ ...f, gender: e.target.value }))}>
                    <option value="">Select</option>
                    {GENDERS.map(g => <option key={g}>{g}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-brand-700/80 mb-1">Height (cm)</label>
                  <input type="number" step="0.1" className="input-field" placeholder="170" value={form.height} onChange={e => setForm(f => ({ ...f, height: e.target.value }))} />
                </div>
                <div>
                  <label className="block text-xs text-brand-700/80 mb-1">Weight (kg)</label>
                  <input type="number" step="0.1" className="input-field" placeholder="70" value={form.weight} onChange={e => setForm(f => ({ ...f, weight: e.target.value }))} />
                </div>
                <div>
                  <label className="block text-xs text-brand-700/80 mb-1">Blood Group</label>
                  <select className="input-field" value={form.blood_group} onChange={e => setForm(f => ({ ...f, blood_group: e.target.value }))}>
                    <option value="">Select</option>
                    {BLOOD_GROUPS.map(g => <option key={g}>{g}</option>)}
                  </select>
                </div>
              </div>
              {error && <p className="text-rose-400 text-sm">{error}</p>}
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancel</button>
                <button type="submit" disabled={saving} className="btn-primary">{saving ? 'Creating…' : 'Create Patient'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
