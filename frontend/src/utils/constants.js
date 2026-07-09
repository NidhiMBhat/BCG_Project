export const APP_NAME = 'BCG Healthcare Platform'
export const APP_VERSION = '1.0.0'
export const BACKEND_URL = 'http://localhost:8001'
export const SSE_URL = '/api/live'

export const SIDEBAR_LINKS = [
  { path: '/',          label: 'Dashboard',       icon: 'LayoutDashboard' },
  { path: '/patients',  label: 'Patients',        icon: 'Users' },
  { path: '/live',      label: 'Live Monitoring', icon: 'Activity' },
  { path: '/analytics', label: 'Analytics',       icon: 'BarChart3' },
  { path: '/history',   label: 'Scan History',    icon: 'ClipboardList' },
  { path: '/exports',   label: 'Exports',         icon: 'Download' },
  { path: '/settings',  label: 'Settings',        icon: 'Settings' },
]

export const SIGNAL_QUALITY_ORDER = ['Excellent', 'Good', 'Moderate', 'Poor']
export const RISK_LEVELS = ['Low', 'Medium', 'High']
export const BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
export const GENDERS = ['Male', 'Female', 'Other', 'Prefer not to say']
export const ROLES = ['admin', 'doctor', 'patient']
