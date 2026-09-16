<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'

const apiBase = 'http://localhost:8000/api/v1'
const token = ref(localStorage.getItem('token'))
const currentUser = ref(null)
const selectedRole = ref(null)
const credentialEmail = ref('')
const password = ref('')
const showPassword = ref(false)
const showNewUserPassword = ref(false)
const isLoading = ref(false)
const toast = ref({ show: false, msg: '', type: 'success' })

const activeTab = ref('inicio')
const patients = ref([])
const practitioners = ref([])
const appointments = ref([])
const users = ref([])
const auditLogs = ref([])
const auditFilters = ref({ entity_type: '', changed_by: '', operation: '', date_from: '', date_to: '' })
const auditPage = ref(1)
const auditTotal = ref(0)
const auditMeta = ref({ pages: 0 })

const showModal = ref(false)
const modalType = ref('patient')
const searchQuery = ref('')

const newPatient = ref({ identifier: '', name: '' })
const newPractitioner = ref({ identifier: '', name: '', specialty: '', telecom: '', generate_credentials: true })
const newAppointment = ref({ patient_id: '', practitioner_id: '', start_time: '', end_time: '', status: 'agendada' })
const newUser = ref({ email: '', full_name: '', role: 'recepcionista', password: '' })
const visiblePasswords = ref({})
const practitionerCredentials = ref({})
const expandedUserPerms = ref(null)

const scopeLabel = (s) => {
  const map = {
    'admin:all': 'Acceso total',
    'patients:read': 'Ver pacientes',
    'patients:write': 'Registrar y editar pacientes',
    'practitioners:read': 'Ver personal medico',
    'practitioners:write': 'Registrar y editar medicos',
    'appointments:read': 'Ver citas',
    'appointments:write': 'Agendar y modificar citas',
    'audit:read': 'Consultar auditoria',
    'audit:delete': 'Eliminar registros de auditoria',
  }
  return map[s] || s
}

const roles = [
  { id: 'admin', label: 'Administrador', email: 'admin@clinic.com', pwd: 'admin123', icon: 'admin_panel_settings', color: 'emerald', desc: 'Acceso total al sistema. Gestiona pacientes, profesionales, citas y usuarios.' },
  { id: 'medico', label: 'Médico', email: 'medico@clinic.com', pwd: 'admin123', icon: 'stethoscope', color: 'blue', desc: 'Ve sus citas del día, consulta fichas de pacientes y agenda nuevas consultas.' },
  { id: 'recepcionista', label: 'Recepcionista', email: 'recepcionista@clinic.com', pwd: 'admin123', icon: 'person_add', color: 'violet', desc: 'Registra pacientes, agenda citas y gestiona la agenda diaria del consultorio.' }
]

const roleLabel = computed(() => {
  if (!currentUser.value) return ''
  const map = { admin: 'Administrador', medico: 'Médico', recepcionista: 'Recepcionista' }
  return map[currentUser.value.role] || ''
})
const canWritePatients = computed(() => currentUser.value?.scopes?.includes('patients:write') || currentUser.value?.scopes?.includes('admin:all'))
const canWriteAppointments = computed(() => currentUser.value?.scopes?.includes('appointments:write') || currentUser.value?.scopes?.includes('admin:all'))
const canWritePractitioners = computed(() => currentUser.value?.scopes?.includes('practitioners:write') || currentUser.value?.scopes?.includes('admin:all'))

const formatRut = (raw) => { const clean = raw.replace(/[^0-9kK]/g, '').toUpperCase(); if (clean.length <= 1) return clean; return clean.slice(0, -1) + '-' + clean.slice(-1) }
const handleRutInput = (e, model, field) => { model[field] = formatRut(e.target.value); const input = e.target; const len = input.value.length; setTimeout(() => input.setSelectionRange(len, len), 0) }
const showToast = (msg, type = 'success') => { toast.value = { show: true, msg, type }; setTimeout(() => toast.value.show = false, 4000) }
const decodeJwt = (t) => { try { return JSON.parse(atob(t.split('.')[1])) } catch { return null } }

const selectRole = (role) => { selectedRole.value = role.id; credentialEmail.value = role.email; password.value = role.pwd }

const login = async () => {
  if (!credentialEmail.value || !password.value) { showToast('Selecciona un rol e ingresa la contraseña', 'error'); return }
  isLoading.value = true
  try {
    const params = new URLSearchParams(); params.append('username', credentialEmail.value); params.append('password', password.value)
    const response = await axios.post('http://localhost:8000/token', params)
    token.value = response.data.access_token; localStorage.setItem('token', token.value)
    const payload = decodeJwt(token.value)
    if (payload) currentUser.value = { email: payload.sub, fullName: payload.full_name || payload.sub, role: payload.role || 'admin', scopes: payload.scopes || [] }
    showToast('Sesión iniciada'); fetchData(); if (payload.role === 'admin') fetchUsers()
  } catch { showToast('Credenciales inválidas', 'error') }
  finally { isLoading.value = false }
}

const logout = () => { token.value = null; currentUser.value = null; selectedRole.value = null; credentialEmail.value = ''; password.value = ''; localStorage.removeItem('token'); activeTab.value = 'inicio' }
const authHeaders = () => ({ headers: { Authorization: `Bearer ${token.value}` } })

const fetchData = async () => {
  if (!token.value) return; isLoading.value = true
  try {
    const reqs = []
    reqs.push((currentUser.value?.scopes?.includes('patients:read') || currentUser.value?.scopes?.includes('admin:all')) ? axios.get(`${apiBase}/patients/`, authHeaders()) : Promise.resolve({ data: [] }))
    reqs.push((currentUser.value?.scopes?.includes('practitioners:read') || currentUser.value?.scopes?.includes('admin:all')) ? axios.get(`${apiBase}/practitioners/`, authHeaders()) : Promise.resolve({ data: [] }))
    reqs.push((currentUser.value?.scopes?.includes('appointments:read') || currentUser.value?.scopes?.includes('admin:all')) ? axios.get(`${apiBase}/appointments/`, authHeaders()) : Promise.resolve({ data: [] }))
    const [pRes, prRes, aRes] = await Promise.all(reqs)
    patients.value = pRes.data; practitioners.value = prRes.data; appointments.value = aRes.data
  } catch (err) { if (err.response?.status === 401) logout(); else showToast('Error al sincronizar datos', 'error') }
  finally { isLoading.value = false }
}

const fetchUsers = async () => { if (!currentUser.value?.scopes?.includes('admin:all')) return; try { const res = await axios.get(`${apiBase}/users`, authHeaders()); users.value = res.data } catch {} }

const fetchAuditLogs = async () => {
  if (!currentUser.value?.scopes?.includes('audit:read')) return
  isLoading.value = true
  try {
    const params = { page: auditPage.value, limit: 20 }
    if (auditFilters.value.entity_type) params.entity_type = auditFilters.value.entity_type
    if (auditFilters.value.changed_by) params.changed_by = auditFilters.value.changed_by
    if (auditFilters.value.operation) params.operation = auditFilters.value.operation
    if (auditFilters.value.date_from) params.date_from = auditFilters.value.date_from
    if (auditFilters.value.date_to) params.date_to = auditFilters.value.date_to
    const res = await axios.get(`${apiBase}/audit`, { ...authHeaders(), params })
    auditLogs.value = res.data.data || []
    auditTotal.value = res.data.meta?.total || 0
    auditMeta.value = res.data.meta || { pages: 0 }
  } catch { showToast('Error al cargar auditoría', 'error') }
  finally { isLoading.value = false }
}

const deleteAuditLogs = async () => {
  try {
    const res = await axios.delete(`${apiBase}/audit`, { ...authHeaders(), data: { confirm: 'delete' } })
    showToast(res.data?.message || 'Logs eliminados')
    fetchAuditLogs()
  } catch (err) { showToast(err.response?.data?.detail || 'Error al eliminar logs', 'error') }
}

const groupedAuditLogs = computed(() => {
  const groups = {}
  for (const log of auditLogs.value) {
    const key = `${log.entity_type}|${log.entity_id}|${log.operation}|${log.changed_by}|${log.changed_at}`
    if (!groups[key]) {
      groups[key] = {
        entity_type: log.entity_type,
        entity_id: log.entity_id,
        operation: log.operation,
        changed_by: log.changed_by,
        changed_at: log.changed_at,
        changes: []
      }
    }
    if (log.field_name !== '*') {
      groups[key].changes.push({ field: log.field_name, old: log.old_value, new: log.new_value })
    } else {
      groups[key].changes.push({ field: 'snapshot', old: log.old_value, new: null })
    }
  }
  return Object.values(groups).sort((a, b) => new Date(b.changed_at) - new Date(a.changed_at))
})

const entityLabel = (t) => ({ patients: 'Paciente', practitioners: 'Médico', appointments: 'Cita' }[t] || t)
const opIcon = (op) => ({ CREATE: 'add_circle', UPDATE: 'edit', DELETE: 'delete' }[op] || 'info')
const opColor = (op) => ({ CREATE: 'text-emerald-600 bg-emerald-50', UPDATE: 'text-amber-600 bg-amber-50', DELETE: 'text-red-600 bg-red-50' }[op] || '')
const fieldLabel = (f) => {
  const map = { name: 'Nombre', identifier: 'RUT', specialty: 'Especialidad', telecom: 'Contacto',
    status: 'Estado', start_time: 'Inicio', end_time: 'Fin', patient_id: 'Paciente', practitioner_id: 'Médico',
    email: 'Email', full_name: 'Nombre', role: 'Rol', is_deleted: 'Eliminado', deleted_at: 'Fecha eliminación',
    snapshot: 'Registro completo' }
  return map[f] || f
}
const prettyVal = (field, val) => {
  if (!val) return '—'
  if (field === 'start_time' || field === 'end_time') {
    try { return new Date(val).toLocaleString('es-CL', { day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit' }) } catch { return val }
  }
  if (val.length > 40) return val.slice(0, 40) + '...'
  return val
}

const createPatient = async () => {
  if (!newPatient.value.name || !newPatient.value.identifier) { showToast('Nombre e identificador requeridos', 'error'); return }
  isLoading.value = true
  try { await axios.post(`${apiBase}/patients/`, { id: `pat-${Date.now()}`, identifier: newPatient.value.identifier.trim(), name: newPatient.value.name.trim(), birth_date: null }, authHeaders()); showToast('Paciente registrado'); showModal.value = false; newPatient.value = { identifier: '', name: '' }; fetchData() }
  catch (err) { showToast(err.response?.data?.detail || 'Error al registrar paciente', 'error') }
  finally { isLoading.value = false }
}

const createPractitioner = async () => {
  if (!newPractitioner.value.name || !newPractitioner.value.identifier) { showToast('Nombre e identificador requeridos', 'error'); return }
  isLoading.value = true
  try { const res = await axios.post(`${apiBase}/practitioners/`, { id: `prac-${Date.now()}`, identifier: newPractitioner.value.identifier.trim(), name: newPractitioner.value.name.trim(), specialty: newPractitioner.value.specialty || null, telecom: newPractitioner.value.telecom || null, generate_credentials: newPractitioner.value.generate_credentials }, authHeaders()); if (res.data?.generated_password) { showToast(`Medico creado. Email: ${res.data.email || 'N/A'}`, 'success'); setTimeout(() => alert(`Credenciales generadas:\n\nEmail: ${res.data.email}\nPassword: ${res.data.generated_password}\n\nGuardalas. No se mostraran de nuevo.`), 500) } else { showToast('Profesional registrado') }; showModal.value = false; newPractitioner.value = { identifier: '', name: '', specialty: '', telecom: '', generate_credentials: true }; fetchData() }
  catch (err) { showToast(err.response?.data?.detail || 'Error al registrar profesional', 'error') }
  finally { isLoading.value = false }
}

const createAppointment = async () => {
  if (!newAppointment.value.patient_id || !newAppointment.value.practitioner_id || !newAppointment.value.start_time) { showToast('Todos los campos son requeridos', 'error'); return }
  isLoading.value = true
  const start = new Date(newAppointment.value.start_time)
  const end = new Date(start.getTime() + 30 * 60000)
  try { await axios.post(`${apiBase}/appointments/`, { id: `apt-${Date.now()}`, status: newAppointment.value.status, start_time: start.toISOString(), end_time: end.toISOString(), patient_id: newAppointment.value.patient_id, practitioner_id: newAppointment.value.practitioner_id }, authHeaders()); showToast('Cita registrada'); showModal.value = false; newAppointment.value = { patient_id: '', practitioner_id: '', start_time: '', end_time: '', status: 'agendada' }; fetchData() }
  catch (err) { showToast(err.response?.data?.detail || 'Error al registrar cita', 'error') }
  finally { isLoading.value = false }
}

const deleteRecord = async (id, type) => { if (!confirm('¿Eliminar este registro?')) return; try { await axios.delete(`${apiBase}/${type}/${id}/`, authHeaders()); showToast('Registro eliminado'); fetchData() } catch (err) { showToast(err.response?.data?.detail || 'Error al eliminar', 'error') } }

const createUser = async () => {
  if (!newUser.value.email || !newUser.value.full_name || !newUser.value.password) { showToast('Todos los campos son requeridos', 'error'); return }
  isLoading.value = true
  try { await axios.post(`${apiBase}/users`, newUser.value, authHeaders()); showToast('Usuario creado'); showModal.value = false; newUser.value = { email: '', full_name: '', role: 'recepcionista', password: '' }; fetchUsers() }
  catch (err) { showToast(err.response?.data?.detail || 'Error al crear usuario', 'error') }
  finally { isLoading.value = false }
}

const deleteUser = async (email) => { if (!confirm(`¿Eliminar usuario ${email}?`)) return; try { await axios.delete(`${apiBase}/users/${email}`, authHeaders()); showToast('Usuario eliminado'); fetchUsers() } catch (err) { showToast(err.response?.data?.detail || 'Error al eliminar usuario', 'error') } }

const resetPractitionerPassword = async (email) => {
  try {
    const res = await axios.post(`${apiBase}/users/${email}/reset-password`, {}, authHeaders())
    practitionerCredentials.value[email] = res.data.new_password
    visiblePasswords.value[email] = false
    showToast('Contrasena regenerada')
  } catch (err) { showToast(err.response?.data?.detail || 'Error al regenerar', 'error') }
}
const togglePasswordVisibility = (email) => {
  visiblePasswords.value[email] = !visiblePasswords.value[email]
}

const statusLabel = (s) => { const map = { agendada:'Agendada', confirmada:'Confirmada', en_curso:'En curso', completada:'Completada', cancelada:'Cancelada', no_asiste:'No asiste', booked:'Agendada', pending:'Pendiente', cancelled:'Cancelada' }; return map[s]||s }
const statusColor = (s) => { const map = { agendada:'bg-blue-50 text-blue-700 border-blue-200', booked:'bg-blue-50 text-blue-700 border-blue-200', confirmada:'bg-emerald-50 text-emerald-700 border-emerald-200', en_curso:'bg-amber-50 text-amber-700 border-amber-200', completada:'bg-green-50 text-green-700 border-green-200', cancelada:'bg-red-50 text-red-700 border-red-200', cancelled:'bg-red-50 text-red-700 border-red-200', no_asiste:'bg-gray-50 text-gray-700 border-gray-200', pending:'bg-purple-50 text-purple-700 border-purple-200' }; return map[s]||'bg-gray-50 text-gray-700 border-gray-200' }

const filteredPatients = computed(() => { if (!searchQuery.value) return patients.value; const q = searchQuery.value.toLowerCase(); return patients.value.filter(p => p.name?.toLowerCase().includes(q) || p.identifier?.toLowerCase().includes(q)) })
const filteredPractitioners = computed(() => { if (!searchQuery.value) return practitioners.value; const q = searchQuery.value.toLowerCase(); return practitioners.value.filter(p => p.name?.toLowerCase().includes(q) || p.specialty?.toLowerCase().includes(q)) })
const filteredAppointments = computed(() => { if (!searchQuery.value) return appointments.value; const q = searchQuery.value.toLowerCase(); return appointments.value.filter(a => a.patient_id?.toLowerCase().includes(q) || a.status?.toLowerCase().includes(q)) })
const todayAppointments = computed(() => appointments.value.filter(a => { const d = new Date(a.start_time); const today = new Date(); return d.toDateString() === today.toDateString() }))

const patientName = (id) => { const p = patients.value.find(x => x.id === id); return p ? p.name : id }
const practitionerName = (id) => { const p = practitioners.value.find(x => x.id === id); return p ? p.name : id }

onMounted(() => {
  if (token.value) { const payload = decodeJwt(token.value); if (payload) { currentUser.value = { email: payload.sub, fullName: payload.full_name || payload.sub, role: payload.role || 'admin', scopes: payload.scopes || [] }; fetchData(); if (payload.role === 'admin') fetchUsers() } }
})
</script>

<template>
<div class="min-h-screen bg-gray-50 text-gray-800 flex flex-col font-sans antialiased">

<!-- ===== LOGIN ===== -->
<div v-if="!token" class="flex-1 flex items-center justify-center p-6">
  <div class="w-full max-w-2xl">
    <div class="text-center mb-8">
      <div class="w-14 h-14 bg-emerald-100 rounded-xl flex items-center justify-center mx-auto mb-3 overflow-hidden"><img src="/logo.webp" alt="Logo" class="w-10 h-10 object-contain" /></div>
      <h1 class="text-2xl font-semibold text-gray-900">Consultorio Central</h1>
      <p class="text-sm text-gray-500 mt-1">Sistema de gestión clínica</p>
    </div>
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-4">
      <div class="text-center"><span class="text-xs font-medium text-gray-400 uppercase tracking-wide">Iniciar sesión</span></div>
      <div class="flex gap-3">
        <div class="flex-1 space-y-1.5"><label class="text-[11px] text-gray-400 font-medium">Correo electrónico</label><input v-model="credentialEmail" placeholder="correo@clinica.com" class="w-full border border-gray-200 p-2.5 rounded-lg text-sm focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none font-mono" /></div>
        <div class="w-40 space-y-1.5"><label class="text-[11px] text-gray-400 font-medium">Contraseña</label><div class="relative"><input v-model="password" :type="showPassword ? 'text' : 'password'" placeholder="••••••••" class="w-full border border-gray-200 p-2.5 rounded-lg text-sm focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none pr-10" @keyup.enter="login" /><button type="button" @click="showPassword = !showPassword" class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"><span class="material-symbols-outlined text-[18px]">{{ showPassword ? 'visibility_off' : 'visibility' }}</span></button></div></div>
        <div class="flex items-end pb-0.5"><button @click="login" :disabled="isLoading || !credentialEmail || !password" class="px-6 py-2.5 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 transition-colors flex items-center gap-2 disabled:opacity-50 shrink-0"><span v-if="isLoading" class="material-symbols-outlined animate-spin text-[18px]">refresh</span><span v-else>Ingresar</span></button></div>
      </div>
      <div class="flex items-center gap-2 pt-1 border-t border-gray-50">
        <span class="text-[10px] text-gray-300 font-medium tracking-wide">DEMO</span>
        <button v-for="role in roles" :key="role.id" @click="selectRole(role)" class="text-[11px] px-3 py-1 rounded-full border transition-colors" :class="selectedRole === role.id ? 'border-emerald-400 bg-emerald-50 text-emerald-700 font-medium' : 'border-gray-200 text-gray-400 hover:border-gray-300 hover:text-gray-600'">{{ role.label }}</button>
      </div>
    </div>
  </div>
</div>

<!-- ===== APP SHELL ===== -->
<div v-else class="flex flex-1 overflow-hidden">

  <!-- SIDEBAR -->
  <aside class="w-60 bg-white border-r border-gray-200 flex flex-col shrink-0">
    <div class="p-5 border-b border-gray-100">
      <div class="flex items-center gap-2.5">
        <div class="w-8 h-8 rounded-lg bg-emerald-100 flex items-center justify-center overflow-hidden"><img src="/logo.webp" alt="Logo" class="w-6 h-6 object-contain" /></div>
        <h1 class="text-sm font-semibold text-gray-900 leading-tight">Consultorio</h1>
      </div>
    </div>
    <nav class="flex-1 p-3 space-y-0.5">
      <a @click.prevent="activeTab = 'inicio'" href="#" class="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors" :class="activeTab === 'inicio' ? 'bg-emerald-50 text-emerald-700 font-medium' : 'text-gray-600 hover:bg-gray-50'"><span class="material-symbols-outlined text-[20px]">dashboard</span>Inicio</a>
      <a v-if="currentUser?.scopes?.includes('patients:read') || currentUser?.scopes?.includes('admin:all')" @click.prevent="activeTab = 'patients'" href="#" class="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors" :class="activeTab === 'patients' ? 'bg-emerald-50 text-emerald-700 font-medium' : 'text-gray-600 hover:bg-gray-50'"><span class="material-symbols-outlined text-[20px]">person</span>Pacientes</a>
      <a v-if="currentUser?.scopes?.includes('appointments:read') || currentUser?.scopes?.includes('admin:all')" @click.prevent="activeTab = 'appointments'" href="#" class="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors" :class="activeTab === 'appointments' ? 'bg-emerald-50 text-emerald-700 font-medium' : 'text-gray-600 hover:bg-gray-50'"><span class="material-symbols-outlined text-[20px]">calendar_today</span>Citas</a>
      <a v-if="currentUser?.scopes?.includes('practitioners:read') || currentUser?.scopes?.includes('admin:all')" @click.prevent="activeTab = 'practitioners'" href="#" class="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors" :class="activeTab === 'practitioners' ? 'bg-emerald-50 text-emerald-700 font-medium' : 'text-gray-600 hover:bg-gray-50'"><span class="material-symbols-outlined text-[20px]">stethoscope</span>Personal médico</a>
      <div v-if="currentUser?.scopes?.includes('admin:all')" class="pt-2 mt-2 border-t border-gray-100"></div>
      <a v-if="currentUser?.scopes?.includes('admin:all')" @click.prevent="activeTab = 'users'; fetchUsers()" href="#" class="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors" :class="activeTab === 'users' ? 'bg-emerald-50 text-emerald-700 font-medium' : 'text-gray-600 hover:bg-gray-50'"><span class="material-symbols-outlined text-[20px]">manage_accounts</span>Gestión de usuarios</a>
      <a v-if="currentUser?.scopes?.includes('audit:read')" @click.prevent="activeTab = 'audit'; fetchAuditLogs()" href="#" class="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors" :class="activeTab === 'audit' ? 'bg-emerald-50 text-emerald-700 font-medium' : 'text-gray-600 hover:bg-gray-50'"><span class="material-symbols-outlined text-[20px]">receipt_long</span>Auditoría</a>
    </nav>
    <div class="p-3 border-t border-gray-100">
      <div class="flex items-center gap-3 px-3 py-2 mb-2">
        <div class="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center text-xs font-bold text-emerald-700">{{ currentUser?.fullName?.charAt(0) || 'U' }}</div>
        <div class="min-w-0"><p class="text-sm font-medium text-gray-900 truncate">{{ currentUser?.fullName }}</p><p class="text-[11px] text-gray-400">{{ roleLabel }}</p></div>
      </div>
      <a @click.prevent="logout" class="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-red-600 hover:bg-red-50 cursor-pointer transition-colors"><span class="material-symbols-outlined text-[20px]">logout</span>Cerrar sesión</a>
    </div>
  </aside>

  <!-- MAIN CONTENT -->
  <main class="flex-1 flex flex-col min-w-0 bg-gray-50 overflow-hidden">
    <header class="flex justify-between items-center h-14 px-6 bg-white border-b border-gray-200 shrink-0">
      <h2 class="text-base font-semibold text-gray-800">{{ activeTab === 'inicio' ? 'Panel principal' : activeTab === 'patients' ? 'Pacientes' : activeTab === 'appointments' ? 'Citas' : activeTab === 'practitioners' ? 'Personal médico' : activeTab === 'audit' ? 'Auditoría' : 'Gestión de usuarios' }}</h2>
      <button @click="fetchData" class="p-2 rounded-lg hover:bg-gray-100 text-gray-500 transition-colors" title="Actualizar"><span class="material-symbols-outlined text-[20px]" :class="{ 'animate-spin': isLoading }">sync</span></button>
    </header>

    <div class="flex-1 overflow-y-auto p-6 space-y-6">

      <!-- INICIO -->
      <template v-if="activeTab === 'inicio'">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div class="bg-white rounded-xl border border-gray-200 p-5"><div class="flex items-center justify-between mb-3"><span class="text-xs font-medium text-gray-400 uppercase tracking-wide">Pacientes</span><span class="material-symbols-outlined text-emerald-500 text-[20px]">person</span></div><p class="text-2xl font-semibold text-gray-900">{{ patients.length }}</p><p class="text-xs text-gray-400 mt-1">Total registrados</p></div>
          <div class="bg-white rounded-xl border border-gray-200 p-5"><div class="flex items-center justify-between mb-3"><span class="text-xs font-medium text-gray-400 uppercase tracking-wide">Citas hoy</span><span class="material-symbols-outlined text-emerald-500 text-[20px]">today</span></div><p class="text-2xl font-semibold text-gray-900">{{ todayAppointments.length }}</p><p class="text-xs text-gray-400 mt-1">{{ new Date().toLocaleDateString('es-CL', { weekday:'long', day:'numeric', month:'long' }) }}</p></div>
          <div class="bg-white rounded-xl border border-gray-200 p-5"><div class="flex items-center justify-between mb-3"><span class="text-xs font-medium text-gray-400 uppercase tracking-wide">Personal</span><span class="material-symbols-outlined text-emerald-500 text-[20px]">stethoscope</span></div><p class="text-2xl font-semibold text-gray-900">{{ practitioners.length }}</p><p class="text-xs text-gray-400 mt-1">Médicos y especialistas</p></div>
        </div>
        <div v-if="currentUser?.scopes?.includes('appointments:read') || currentUser?.scopes?.includes('admin:all')" class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="text-sm font-semibold text-gray-800 mb-4">Citas del día</h3>
          <div v-if="todayAppointments.length === 0" class="text-center py-8 text-sm text-gray-400"><span class="material-symbols-outlined text-[40px] mb-2 block text-gray-300">event_busy</span>No hay citas programadas para hoy</div>
          <table v-else class="w-full text-sm"><thead><tr class="text-left text-xs text-gray-400 uppercase tracking-wide border-b border-gray-100"><th class="pb-2 font-medium">Hora</th><th class="pb-2 font-medium">Paciente</th><th class="pb-2 font-medium">Profesional</th><th class="pb-2 font-medium">Estado</th></tr></thead><tbody><tr v-for="a in todayAppointments" :key="a.id" class="border-b border-gray-50"><td class="py-2.5 text-gray-700">{{ new Date(a.start_time).toLocaleTimeString('es-CL', { hour:'2-digit', minute:'2-digit' }) }}</td><td class="py-2.5 text-gray-700 font-medium">{{ patientName(a.patient_id) }}</td><td class="py-2.5 text-gray-500">{{ practitionerName(a.practitioner_id) }}</td><td class="py-2.5"><span class="inline-flex px-2 py-0.5 rounded-full text-[11px] font-medium border" :class="statusColor(a.status)">{{ statusLabel(a.status) }}</span></td></tr></tbody></table>
        </div>
      </template>

      <!-- PACIENTES -->
      <template v-if="activeTab === 'patients'">
        <div class="flex items-center justify-between">
          <div class="relative"><span class="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-gray-400 text-[18px]">search</span><input v-model="searchQuery" placeholder="Buscar paciente..." class="pl-9 pr-4 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none w-64" /></div>
          <button v-if="canWritePatients" @click="modalType = 'patient'; showModal = true" class="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 transition-colors"><span class="material-symbols-outlined text-[18px]">add</span>Nuevo paciente</button>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table class="w-full text-sm"><thead><tr class="text-left text-xs text-gray-400 uppercase tracking-wide border-b border-gray-100 bg-gray-50/50"><th class="px-5 py-3 font-medium">Paciente</th><th class="px-5 py-3 font-medium">Identificador</th><th class="px-5 py-3 font-medium text-right w-20">Acciones</th></tr></thead>
            <tbody class="divide-y divide-gray-50">
              <tr v-for="p in filteredPatients" :key="p.id" class="hover:bg-gray-50/50 transition-colors"><td class="px-5 py-3"><div class="flex items-center gap-3"><div class="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center text-xs font-semibold text-emerald-700">{{ p.name?.charAt(0) || '?' }}</div><span class="font-medium text-gray-800">{{ p.name }}</span></div></td><td class="px-5 py-3 text-gray-500 font-mono text-xs">{{ p.identifier }}</td><td class="px-5 py-3 text-right"><button v-if="canWritePatients" @click="deleteRecord(p.id, 'patients')" class="p-1.5 rounded hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors" title="Eliminar"><span class="material-symbols-outlined text-[18px]">delete</span></button></td></tr>
              <tr v-if="filteredPatients.length === 0 && !isLoading"><td colspan="3" class="px-5 py-12 text-center text-sm text-gray-400"><span class="material-symbols-outlined text-[40px] mb-2 block text-gray-300">folder_open</span>No hay pacientes {{ searchQuery ? 'para esta búsqueda' : 'registrados' }}</td></tr>
            </tbody>
          </table>
        </div>
      </template>

      <!-- CITAS -->
      <template v-if="activeTab === 'appointments'">
        <div class="flex items-center justify-between">
          <div class="relative"><span class="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-gray-400 text-[18px]">search</span><input v-model="searchQuery" placeholder="Buscar cita..." class="pl-9 pr-4 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none w-64" /></div>
          <button v-if="canWriteAppointments" @click="modalType = 'appointment'; showModal = true" class="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 transition-colors"><span class="material-symbols-outlined text-[18px]">add</span>Nueva cita</button>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table class="w-full text-sm"><thead><tr class="text-left text-xs text-gray-400 uppercase tracking-wide border-b border-gray-100 bg-gray-50/50"><th class="px-5 py-3 font-medium">Fecha / Hora</th><th class="px-5 py-3 font-medium">Paciente</th><th class="px-5 py-3 font-medium">Profesional</th><th class="px-5 py-3 font-medium">Estado</th><th class="px-5 py-3 font-medium text-right w-20">Acciones</th></tr></thead>
            <tbody class="divide-y divide-gray-50">
              <tr v-for="a in filteredAppointments" :key="a.id" class="hover:bg-gray-50/50 transition-colors"><td class="px-5 py-3 text-gray-700">{{ new Date(a.start_time).toLocaleString('es-CL', { day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit' }) }}</td><td class="px-5 py-3 text-gray-700 font-medium">{{ patientName(a.patient_id) }}</td><td class="px-5 py-3 text-gray-500">{{ practitionerName(a.practitioner_id) }}</td><td class="px-5 py-3"><span class="inline-flex px-2 py-0.5 rounded-full text-[11px] font-medium border" :class="statusColor(a.status)">{{ statusLabel(a.status) }}</span></td><td class="px-5 py-3 text-right"><button v-if="canWriteAppointments" @click="deleteRecord(a.id, 'appointments')" class="p-1.5 rounded hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors" title="Eliminar"><span class="material-symbols-outlined text-[18px]">delete</span></button></td></tr>
              <tr v-if="filteredAppointments.length === 0 && !isLoading"><td colspan="5" class="px-5 py-12 text-center text-sm text-gray-400"><span class="material-symbols-outlined text-[40px] mb-2 block text-gray-300">event_busy</span>No hay citas {{ searchQuery ? 'para esta búsqueda' : 'registradas' }}</td></tr>
            </tbody>
          </table>
        </div>
      </template>

      <!-- PERSONAL MÉDICO -->
      <template v-if="activeTab === 'practitioners'">
        <div class="flex items-center justify-between">
          <div class="relative"><span class="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-gray-400 text-[18px]">search</span><input v-model="searchQuery" placeholder="Buscar profesional..." class="pl-9 pr-4 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none w-64" /></div>
          <button v-if="canWritePractitioners" @click="modalType = 'practitioner'; showModal = true" class="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 transition-colors"><span class="material-symbols-outlined text-[18px]">add</span>Nuevo profesional</button>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table class="w-full text-sm"><thead><tr class="text-left text-xs text-gray-400 uppercase tracking-wide border-b border-gray-100 bg-gray-50/50"><th class="px-5 py-3 font-medium">Profesional</th><th class="px-5 py-3 font-medium">Especialidad</th><th class="px-5 py-3 font-medium">Contacto</th><th class="px-5 py-3 font-medium text-right w-20">Acciones</th></tr></thead>
            <tbody class="divide-y divide-gray-50">
              <tr v-for="pr in filteredPractitioners" :key="pr.id" class="hover:bg-gray-50/50 transition-colors"><td class="px-5 py-3"><div class="flex items-center gap-3"><div class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-xs font-semibold text-blue-700">{{ pr.name?.charAt(0) || '?' }}</div><span class="font-medium text-gray-800">{{ pr.name }}</span></div></td><td class="px-5 py-3 text-gray-500">{{ pr.specialty || 'Medicina general' }}</td><td class="px-5 py-3 text-gray-500 text-xs font-mono">{{ pr.telecom || '—' }}</td><td class="px-5 py-3 text-right"><button v-if="canWritePractitioners" @click="deleteRecord(pr.id, 'practitioners')" class="p-1.5 rounded hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors" title="Eliminar"><span class="material-symbols-outlined text-[18px]">delete</span></button></td></tr>
              <tr v-if="filteredPractitioners.length === 0 && !isLoading"><td colspan="4" class="px-5 py-12 text-center text-sm text-gray-400"><span class="material-symbols-outlined text-[40px] mb-2 block text-gray-300">folder_open</span>No hay profesionales registrados</td></tr>
            </tbody>
          </table>
        </div>
      </template>

      <!-- GESTIÓN DE USUARIOS -->
      <template v-if="activeTab === 'users'">
        <div class="flex items-center justify-between">
          <h3 class="text-sm font-semibold text-gray-700">Usuarios del sistema</h3>
          <button @click="modalType = 'user'; showModal = true" class="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 transition-colors"><span class="material-symbols-outlined text-[18px]">person_add</span>Nuevo usuario</button>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table class="w-full text-sm"><thead><tr class="text-left text-xs text-gray-400 uppercase tracking-wide border-b border-gray-100 bg-gray-50/50"><th class="px-5 py-3 font-medium">Usuario</th><th class="px-5 py-3 font-medium">Rol</th><th class="px-5 py-3 font-medium">Permisos</th><th class="px-5 py-3 font-medium">Contrasena</th><th class="px-5 py-3 font-medium text-right w-20">Acciones</th></tr></thead>
            <tbody class="divide-y divide-gray-50">
              <tr v-for="u in users" :key="u.email" class="hover:bg-gray-50/50 transition-colors">
                <td class="px-5 py-3"><div class="flex items-center gap-3"><div class="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center text-xs font-semibold text-emerald-700">{{ u.full_name?.charAt(0) || '?' }}</div><div><p class="font-medium text-gray-800">{{ u.full_name }}</p><p class="text-[11px] text-gray-400 font-mono">{{ u.email }}</p></div></div></td>
                <td class="px-5 py-3"><span class="inline-flex px-2 py-0.5 rounded-full text-[11px] font-medium border" :class="u.role === 'admin' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : u.role === 'medico' ? 'bg-blue-50 text-blue-700 border-blue-200' : 'bg-violet-50 text-violet-700 border-violet-200'">{{ u.role === 'admin' ? 'Administrador' : u.role === 'medico' ? 'Medico' : 'Recepcionista' }}</span></td>
                <td class="px-5 py-3">
                  <button @click="expandedUserPerms = expandedUserPerms === u.email ? null : u.email" class="text-left group">
                    <span class="text-xs font-medium text-gray-600 group-hover:text-emerald-600 transition-colors">{{ u.scopes?.length || 0 }} {{ u.scopes?.length === 1 ? 'permiso' : 'permisos' }}</span>
                    <span class="material-symbols-outlined text-[14px] text-gray-300 group-hover:text-emerald-500 align-middle ml-0.5 transition-colors">{{ expandedUserPerms === u.email ? 'expand_less' : 'expand_more' }}</span>
                  </button>
                  <div v-if="expandedUserPerms === u.email" class="mt-2 pl-1 space-y-0.5 border-l-2 border-emerald-200">
                    <div v-for="s in u.scopes" :key="s" class="text-[11px] text-gray-500">{{ scopeLabel(s) }}</div>
                  </div>
                </td>
                <td class="px-5 py-3">
                  <div class="flex items-center gap-1.5">
                    <input :type="visiblePasswords[u.email] ? 'text' : 'password'" :value="practitionerCredentials[u.email] || ''" readonly class="w-28 border border-gray-200 rounded px-2 py-1 text-xs font-mono bg-gray-50" placeholder="••••••••" />
                    <button @click="togglePasswordVisibility(u.email)" class="p-1 rounded hover:bg-gray-100 text-gray-400" :title="visiblePasswords[u.email] ? 'Ocultar' : 'Mostrar'">
                      <span class="material-symbols-outlined text-[16px]">{{ visiblePasswords[u.email] ? 'visibility_off' : 'visibility' }}</span>
                    </button>
                    <button @click="resetPractitionerPassword(u.email)" class="p-1 rounded hover:bg-emerald-50 text-gray-400 hover:text-emerald-600" title="Regenerar contrasena">
                      <span class="material-symbols-outlined text-[16px]">refresh</span>
                    </button>
                  </div>
                </td>
                <td class="px-5 py-3 text-right"><button @click="deleteUser(u.email)" :disabled="u.email === currentUser?.email" class="p-1.5 rounded hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors disabled:opacity-30 disabled:cursor-not-allowed" :title="u.email === currentUser?.email ? 'No puedes eliminarte a ti mismo' : 'Eliminar'"><span class="material-symbols-outlined text-[18px]">delete</span></button></td>
              </tr>
              <tr v-if="users.length === 0 && !isLoading"><td colspan="5" class="px-5 py-12 text-center text-sm text-gray-400"><span class="material-symbols-outlined text-[40px] mb-2 block text-gray-300">group_off</span>No hay usuarios registrados</td></tr>
            </tbody>
          </table>
        </div>
      </template>

      <!-- AUDITORÍA -->
      <template v-if="activeTab === 'audit'">
        <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
          <div class="flex flex-wrap gap-2">
            <select v-model="auditFilters.entity_type" @change="auditPage=1; fetchAuditLogs()" class="border border-gray-200 p-2 rounded-lg text-sm bg-white focus:border-emerald-500 outline-none"><option value="">Todas las entidades</option><option value="patients">Pacientes</option><option value="practitioners">Personal médico</option><option value="appointments">Citas</option></select>
            <select v-model="auditFilters.operation" @change="auditPage=1; fetchAuditLogs()" class="border border-gray-200 p-2 rounded-lg text-sm bg-white focus:border-emerald-500 outline-none"><option value="">Todas las operaciones</option><option value="CREATE">Creación</option><option value="UPDATE">Modificación</option><option value="DELETE">Eliminación</option></select>
            <input v-model="auditFilters.changed_by" @keyup.enter="auditPage=1; fetchAuditLogs()" placeholder="Usuario..." class="w-36 border border-gray-200 p-2 rounded-lg text-sm focus:border-emerald-500 outline-none" />
          </div>
          <div class="flex items-center gap-2">
            <span class="text-xs text-gray-400">{{ auditTotal }} registros</span>
            <button v-if="currentUser?.scopes?.includes('audit:delete')" @click="deleteAuditLogs()" class="px-3 py-1.5 border border-red-200 text-red-600 rounded-lg text-xs font-medium hover:bg-red-50 transition-colors">Eliminar logs</button>
            <button @click="fetchAuditLogs" class="p-1.5 rounded hover:bg-gray-100 text-gray-400"><span class="material-symbols-outlined text-[18px]">refresh</span></button>
          </div>
        </div>

        <!-- Loading -->
        <div v-if="isLoading" class="p-8 text-center text-sm text-gray-400"><span class="material-symbols-outlined animate-spin text-[32px] mb-2 block">refresh</span>Cargando auditoría...</div>

        <!-- Empty -->
        <div v-else-if="groupedAuditLogs.length === 0" class="p-8 text-center text-sm text-gray-400"><span class="material-symbols-outlined text-[40px] mb-2 block text-gray-300">receipt_long</span>No hay registros de auditoría</div>

        <!-- Changelog -->
        <div v-else class="space-y-2">
          <div v-for="group in groupedAuditLogs" :key="group.changed_at + group.entity_id" class="bg-white rounded-lg border border-gray-200 hover:border-gray-300 transition-colors">
            <div class="flex items-start gap-3 p-4">
              <div class="w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-0.5" :class="opColor(group.operation)">
                <span class="material-symbols-outlined text-[18px]">{{ opIcon(group.operation) }}</span>
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 flex-wrap mb-1">
                  <span class="text-sm font-medium text-gray-900">{{ group.changed_by }}</span>
                  <span class="text-xs px-1.5 py-0.5 rounded-full font-medium" :class="opColor(group.operation)">
                    {{ group.operation === 'CREATE' ? 'creó' : group.operation === 'UPDATE' ? 'modificó' : 'eliminó' }}
                  </span>
                  <span class="text-sm text-gray-700">{{ entityLabel(group.entity_type) }}</span>
                  <span class="text-xs text-gray-400 font-mono">{{ group.entity_id?.slice(0,8) }}</span>
                  <span class="text-xs text-gray-400">·</span>
                  <span class="text-xs text-gray-400">{{ new Date(group.changed_at).toLocaleString('es-CL', { day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit' }) }}</span>
                </div>
                <div v-if="group.changes.length > 0 && group.changes[0].field !== 'snapshot'" class="mt-2 space-y-0.5">
                  <div v-for="c in group.changes" :key="c.field" class="flex items-center gap-2 text-xs pl-1">
                    <span class="text-gray-500 w-28 shrink-0">{{ fieldLabel(c.field) }}</span>
                    <template v-if="group.operation === 'CREATE'">
                      <span class="text-gray-700 font-mono truncate">{{ prettyVal(c.field, c.new) }}</span>
                    </template>
                    <template v-else>
                      <span class="text-gray-400 font-mono line-through truncate max-w-[140px]">{{ prettyVal(c.field, c.old) }}</span>
                      <span class="text-gray-400">→</span>
                      <span class="text-gray-700 font-mono truncate max-w-[140px]">{{ prettyVal(c.field, c.new) }}</span>
                    </template>
                  </div>
                </div>
                <div v-else-if="group.changes.length > 0" class="mt-2">
                  <span class="text-xs text-gray-400">Registro completo eliminado (soft-delete)</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="auditMeta.pages > 1" class="flex justify-center gap-2 mt-4">
          <button @click="auditPage--; fetchAuditLogs()" :disabled="auditPage <= 1" class="px-3 py-1.5 border border-gray-200 rounded-lg text-xs hover:bg-gray-50 disabled:opacity-30">Anterior</button>
          <span class="px-3 py-1.5 text-xs text-gray-400">Pág {{ auditPage }} de {{ auditMeta.pages }}</span>
          <button @click="auditPage++; fetchAuditLogs()" :disabled="auditPage >= auditMeta.pages" class="px-3 py-1.5 border border-gray-200 rounded-lg text-xs hover:bg-gray-50 disabled:opacity-30">Siguiente</button>
        </div>
      </template>

    </div>
  </main>

</div>

<!-- ===== MODAL ===== -->
<div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/20 backdrop-blur-sm">
  <div class="bg-white rounded-xl shadow-lg border border-gray-200 w-full max-w-md overflow-hidden">
    <div class="px-5 py-4 border-b border-gray-100 flex justify-between items-center">
      <h3 class="text-base font-semibold text-gray-800">{{ modalType === 'practitioner' ? 'Nuevo profesional' : modalType === 'appointment' ? 'Nueva cita' : modalType === 'user' ? 'Nuevo usuario' : 'Nuevo paciente' }}</h3>
      <button @click="showModal = false" class="text-gray-400 hover:text-gray-600 transition-colors material-symbols-outlined">close</button>
    </div>

    <!-- Patient form -->
    <div v-if="modalType === 'patient'" class="p-5 space-y-4">
      <div><label class="block text-xs font-medium text-gray-500 mb-1">Nombre completo</label><input v-model="newPatient.name" placeholder="Ej: Juan Pérez" class="w-full border border-gray-200 p-2.5 rounded-lg text-sm focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none" /></div>
      <div><label class="block text-xs font-medium text-gray-500 mb-1">Identificador (RUT)</label><input :value="newPatient.identifier" @input="handleRutInput($event, newPatient, 'identifier')" placeholder="12345678-9" maxlength="11" class="w-full border border-gray-200 p-2.5 rounded-lg text-sm font-mono focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none" /></div>
    </div>

    <!-- Practitioner form -->
    <div v-if="modalType === 'practitioner'" class="p-5 space-y-4">
      <div><label class="block text-xs font-medium text-gray-500 mb-1">Nombre completo</label><input v-model="newPractitioner.name" placeholder="Ej: Dra. Maria Gonzalez" class="w-full border border-gray-200 p-2.5 rounded-lg text-sm focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none" /></div>
      <div><label class="block text-xs font-medium text-gray-500 mb-1">Identificador (RUT)</label><input :value="newPractitioner.identifier" @input="handleRutInput($event, newPractitioner, 'identifier')" placeholder="12345678-9" maxlength="11" class="w-full border border-gray-200 p-2.5 rounded-lg text-sm font-mono focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none" /></div>
      <div><label class="block text-xs font-medium text-gray-500 mb-1">Especialidad</label><input v-model="newPractitioner.specialty" placeholder="Medicina general" class="w-full border border-gray-200 p-2.5 rounded-lg text-sm focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none" /></div>
      <div><label class="block text-xs font-medium text-gray-500 mb-1">Telefono</label><input v-model="newPractitioner.telecom" placeholder="+56 9 1234 5678" type="tel" class="w-full border border-gray-200 p-2.5 rounded-lg text-sm focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none" /></div>
      <div class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
        <input type="checkbox" v-model="newPractitioner.generate_credentials" id="genCreds" class="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500" />
        <div><label for="genCreds" class="text-sm font-medium text-gray-700">Generar credenciales de acceso</label><p class="text-[11px] text-gray-400">Crea un usuario automaticamente. Email basado en el nombre, password aleatoria segura.</p></div>
      </div>
    </div>

    <!-- Appointment form -->
    <div v-if="modalType === 'appointment'" class="p-5 space-y-4">
      <div><label class="block text-xs font-medium text-gray-500 mb-1">Paciente</label><select v-model="newAppointment.patient_id" class="w-full border border-gray-200 p-2.5 rounded-lg text-sm bg-white focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none"><option value="" disabled>Seleccionar paciente...</option><option v-for="p in patients" :key="p.id" :value="p.id">{{ p.name }} ({{ p.identifier }})</option></select></div>
      <div><label class="block text-xs font-medium text-gray-500 mb-1">Profesional</label><select v-model="newAppointment.practitioner_id" class="w-full border border-gray-200 p-2.5 rounded-lg text-sm bg-white focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none"><option value="" disabled>Seleccionar profesional...</option><option v-for="pr in practitioners" :key="pr.id" :value="pr.id">{{ pr.name }} – {{ pr.specialty || 'Medicina general' }}</option></select></div>
      <div><label class="block text-xs font-medium text-gray-500 mb-1">Fecha y hora</label><input v-model="newAppointment.start_time" type="datetime-local" class="w-full border border-gray-200 p-2.5 rounded-lg text-sm focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none" /></div>
      <div><label class="block text-xs font-medium text-gray-500 mb-1">Estado</label><select v-model="newAppointment.status" class="w-full border border-gray-200 p-2.5 rounded-lg text-sm bg-white focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none"><option value="agendada">Agendada</option><option value="confirmada">Confirmada</option><option value="cancelada">Cancelada</option></select></div>
    </div>

    <!-- User form -->
    <div v-if="modalType === 'user'" class="p-5 space-y-4">
      <div><label class="block text-xs font-medium text-gray-500 mb-1">Nombre completo</label><input v-model="newUser.full_name" placeholder="Ej: Dra. María González" class="w-full border border-gray-200 p-2.5 rounded-lg text-sm focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none" /></div>
      <div><label class="block text-xs font-medium text-gray-500 mb-1">Correo electrónico</label><input v-model="newUser.email" type="email" placeholder="usuario@clinica.com" class="w-full border border-gray-200 p-2.5 rounded-lg text-sm focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none font-mono" /></div>
      <div><label class="block text-xs font-medium text-gray-500 mb-1">Rol</label><select v-model="newUser.role" class="w-full border border-gray-200 p-2.5 rounded-lg text-sm bg-white focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none"><option value="medico">Médico</option><option value="recepcionista">Recepcionista</option><option value="admin">Administrador</option></select></div>
      <div><label class="block text-xs font-medium text-gray-500 mb-1">Contraseña</label><div class="relative"><input v-model="newUser.password" :type="showNewUserPassword ? 'text' : 'password'" placeholder="Mínimo 6 caracteres" class="w-full border border-gray-200 p-2.5 rounded-lg text-sm focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none pr-10" /><button type="button" @click="showNewUserPassword = !showNewUserPassword" class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"><span class="material-symbols-outlined text-[18px]">{{ showNewUserPassword ? 'visibility_off' : 'visibility' }}</span></button></div></div>
    </div>

    <div class="px-5 py-4 border-t border-gray-100 bg-gray-50 flex gap-3 justify-end">
      <button @click="showModal = false" class="px-4 py-2 border border-gray-200 bg-white rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100 transition-colors">Cancelar</button>
      <button @click="modalType === 'practitioner' ? createPractitioner() : modalType === 'appointment' ? createAppointment() : modalType === 'user' ? createUser() : createPatient()" :disabled="isLoading" class="px-4 py-2 bg-emerald-600 rounded-lg text-sm font-medium text-white hover:bg-emerald-700 transition-colors flex items-center gap-2 disabled:opacity-50"><span v-if="isLoading" class="material-symbols-outlined animate-spin text-[18px]">refresh</span><span v-else>Guardar</span></button>
    </div>
  </div>
</div>

<!-- ===== TOAST ===== -->
<Transition name="toast">
  <div v-if="toast.show" class="fixed bottom-6 right-6 flex items-center gap-2.5 px-4 py-3 rounded-lg shadow-lg border z-50 text-sm font-medium" :class="toast.type === 'error' ? 'bg-red-50 border-red-200 text-red-700' : 'bg-white border-gray-200 text-gray-800'">
    <span class="material-symbols-outlined text-[18px]">{{ toast.type === 'error' ? 'error' : 'check_circle' }}</span>{{ toast.msg }}
  </div>
</Transition>

</div>
</template>

<style>
.toast-enter-active, .toast-leave-active { transition: all 0.25s ease; }
.toast-enter-from { opacity: 0; transform: translateY(0.5rem); }
.toast-leave-to { opacity: 0; transform: translateY(0.5rem); }
</style>
