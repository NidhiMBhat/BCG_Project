import { User, ChevronRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

export default function PatientCard({ patient }) {
  const navigate = useNavigate()
  return (
    <div
      className="glass-card-hover p-5 cursor-pointer animate-fade-in"
      onClick={() => navigate(`/patients/${patient.id}`)}
    >
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-brand-600 to-accent-violet flex items-center justify-center flex-shrink-0 shadow-lg">
          <User className="w-6 h-6 text-brand-900" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-brand-900 truncate">{patient.name}</p>
          <p className="text-xs text-brand-700/80 mt-0.5">{patient.patient_code}</p>
          <div className="flex gap-3 mt-1.5 flex-wrap">
            {patient.age && <span className="text-xs text-brand-700/60">{patient.age}y</span>}
            {patient.gender && <span className="text-xs text-brand-700/60">{patient.gender}</span>}
            {patient.blood_group && (
              <span className="text-xs text-brand-400 font-mono">{patient.blood_group}</span>
            )}
          </div>
        </div>
        <ChevronRight className="w-4 h-4 text-slate-600 flex-shrink-0" />
      </div>
    </div>
  )
}
