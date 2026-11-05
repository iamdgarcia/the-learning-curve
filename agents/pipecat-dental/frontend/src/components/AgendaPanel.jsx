import { useEffect } from 'react'

const DAYS   = ['Dom','Lun','Mar','Mié','Jue','Vie','Sáb']
const MONTHS = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic']

function parseDate(fecha) {
  const p = (fecha||'').split('/')
  return p.length === 3 ? new Date(p[2], p[1]-1, p[0]) : null
}

// ── Shared card wrapper ───────────────────────────────────
function Card({ children, glow }) {
  return (
    <div className={`rounded-xl border bg-white/4 overflow-hidden transition-shadow duration-300 ${
      glow === 'blue'  ? 'border-blue-500/40 shadow-[0_0_0_1px_rgba(96,165,250,.4),0_4px_20px_rgba(37,99,235,.2)]' :
      glow === 'green' ? 'border-green-500/40 shadow-[0_0_0_1px_rgba(74,222,128,.4),0_4px_20px_rgba(22,163,74,.2)]' :
      'border-white/8'
    }`}>
      {children}
    </div>
  )
}

function CardHead({ icon, title, badge, badgeColor }) {
  const colors = {
    amber: 'bg-amber-400/15 text-amber-300',
    green: 'bg-green-400/15 text-green-400',
    red:   'bg-red-400/15 text-red-400',
  }
  return (
    <div className="flex items-center gap-2 px-4 py-3 border-b border-white/6">
      <div className="w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0 bg-blue-500/20">
        {icon}
      </div>
      <span className="text-[10px] font-semibold uppercase tracking-widest text-white/40">{title}</span>
      <span className={`ml-auto text-[10px] font-bold px-2 py-0.5 rounded-full ${colors[badgeColor]}`}>{badge}</span>
    </div>
  )
}

function Spinner() {
  return <div className="w-4 h-4 rounded-full border-2 border-white/10 border-t-blue-400 animate-spin flex-shrink-0" />
}

function Loading({ text }) {
  return <div className="flex items-center gap-3 px-4 py-5 text-white/40 text-sm"><Spinner />{text}</div>
}

// ── Patient card ──────────────────────────────────────────
function PatientCard({ result, isLoading }) {
  if (isLoading && !result) return (
    <Card>
      <CardHead icon={<PersonIcon />} title="Ficha del paciente" badge="Buscando…" badgeColor="amber" />
      <Loading text="Consultando base de datos…" />
    </Card>
  )
  if (!result) return null

  const initials = (result.nombre||'?').split(' ').map(w=>w[0]).slice(0,2).join('')
  const hasFuture = result.citas_futuras?.length > 0

  return (
    <Card glow="blue">
      <CardHead icon={<PersonIcon />} title="Ficha del paciente" badge="Encontrado" badgeColor="green" />
      <div className="p-4 space-y-4">
        {/* Hero */}
        <div className="flex gap-3 items-start">
          <div className="w-11 h-11 rounded-xl bg-blue-500/25 text-blue-300 text-sm font-bold flex items-center justify-center flex-shrink-0">
            {initials}
          </div>
          <div>
            <div className="font-bold text-base">{result.nombre}</div>
            <div className="font-mono text-[11px] text-white/35 mt-0.5">DNI · {result.dni}</div>
            <span className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full mt-1.5 ${
              result.revision_pendiente ? 'bg-amber-400/15 text-amber-300' : 'bg-green-400/15 text-green-400'
            }`}>
              {result.revision_pendiente ? '⚠ Revisión pendiente' : '✓ Al día'}
            </span>
          </div>
        </div>

        {/* Fields */}
        <div className="grid grid-cols-2 gap-2">
          {[['Última visita', result.ultima_visita], ['Tipo', result.tipo_ultima_visita]].map(([l,v]) => (
            <div key={l}>
              <div className="text-[10px] text-white/30 mb-0.5">{l}</div>
              <div className="text-xs font-medium text-white/80">{v||'—'}</div>
            </div>
          ))}
        </div>

        {/* Upcoming */}
        {hasFuture && (
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-widest text-white/25 mb-2">Próximas citas</div>
            {result.citas_futuras.map((c,i) => {
              const p = c.fecha.split('/'), d = new Date(p[2],p[1]-1,p[0])
              return (
                <div key={i} className="flex items-center gap-3 bg-green-400/8 border border-green-400/15 rounded-lg p-2.5 mb-1.5">
                  <div className="text-center">
                    <div className="text-xl font-black text-green-400 leading-none">{p[0]}</div>
                    <div className="text-[10px] text-green-400/70 font-semibold">{MONTHS[d.getMonth()]}</div>
                  </div>
                  <div className="w-px bg-green-400/15 self-stretch"/>
                  <div>
                    <div className="text-xs font-semibold text-white/80">{c.hora} · {c.tipo}</div>
                    <div className="text-[11px] text-white/35">{result.nombre}</div>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* History */}
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-widest text-white/25 mb-2">Historial clínico</div>
          {(result.historial||[]).map((h,i) => {
            const [date, desc] = h.split(' — ')
            return (
              <div key={i} className="flex gap-2 py-1.5 border-t border-white/5 first:border-0">
                <div className="w-2 h-2 rounded-full bg-blue-400 flex-shrink-0 mt-1"/>
                <div>
                  <div className="text-xs text-white/75 font-medium">{desc||h}</div>
                  <div className="text-[10px] text-white/30">{date||''}</div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </Card>
  )
}

// ── Calendar card ─────────────────────────────────────────
function CalendarCard({ result, isLoading, proposedSlot, confirmedSlot }) {
  if (isLoading && !result) return (
    <Card>
      <CardHead icon={<CalIcon />} title="Disponibilidad" badge="Buscando…" badgeColor="amber" />
      <Loading text="Consultando agenda de la clínica…" />
    </Card>
  )
  if (!result) return null

  const huecos = (result.huecos||[]).filter(h=>h.disponible)
  if (!huecos.length) return (
    <Card>
      <CardHead icon={<CalIcon />} title="Disponibilidad" badge="Sin huecos" badgeColor="red" />
      <div className="px-4 py-4 text-sm text-white/30">Sin disponibilidad con esos criterios</div>
    </Card>
  )

  const byDate = {}
  huecos.forEach(h => (byDate[h.fecha]=byDate[h.fecha]||[]).push(h))
  const dates = Object.keys(byDate).slice(0,5)

  return (
    <Card glow="blue">
      <CardHead icon={<CalIcon />} title="Disponibilidad" badge={`${huecos.length} huecos`} badgeColor="green" />
      <div className="p-3">
        <div className="flex gap-3 mb-3">
          {[['rgba(255,255,255,.2)','Libre'],['#60a5fa','Propuesta'],['#4ade80','Confirmada']].map(([c,l])=>(
            <div key={l} className="flex items-center gap-1.5 text-[10px] text-white/35">
              <div className="w-2 h-2 rounded-full" style={{background:c}}/>
              {l}
            </div>
          ))}
        </div>
        <div className="grid gap-1.5" style={{gridTemplateColumns:`repeat(${dates.length},1fr)`}}>
          {dates.map(fecha => {
            const p = fecha.split('/'), d = new Date(p[2],p[1]-1,p[0])
            return (
              <div key={fecha}>
                <div className="text-[9px] font-semibold text-center text-white/30 uppercase mb-1">{DAYS[d.getDay()]}</div>
                <div className="text-[11px] font-bold text-center text-white/60 mb-1.5">{p[0]} {MONTHS[d.getMonth()]}</div>
                {byDate[fecha].map((s,si) => {
                  const isConfirmed = confirmedSlot?.fecha === fecha && confirmedSlot?.idx === si
                  const isProposed  = !isConfirmed && proposedSlot?.fecha === fecha && proposedSlot?.idx === si
                  return (
                    <div key={si} className={`text-[11px] font-semibold text-center rounded-md py-1.5 mb-1 transition-all duration-500 ${
                      isConfirmed ? 'bg-green-400/20 border border-green-400/40 text-green-400' :
                      isProposed  ? 'bg-blue-500/25 border border-blue-400/50 text-blue-300' :
                      'bg-white/3 border border-white/8 text-white/40'
                    }`}>
                      {s.hora}
                      {isConfirmed && <div className="text-[8px] font-black">✓</div>}
                      {isProposed  && <div className="text-[8px] opacity-60">▲</div>}
                    </div>
                  )
                })}
              </div>
            )
          })}
        </div>
      </div>
    </Card>
  )
}

// ── Confirmation card ─────────────────────────────────────
function ConfirmCard({ result, isLoading }) {
  if (isLoading && !result) return (
    <Card>
      <CardHead icon={<CheckIcon />} title="Confirmación" badge="Guardando…" badgeColor="amber" />
      <Loading text="Registrando cita en el sistema…" />
    </Card>
  )
  if (!result) return null

  const c = result.cita
  const d = parseDate(c?.fecha)
  const dateStr = d ? `${DAYS[d.getDay()]} ${c.fecha.split('/')[0]} ${MONTHS[d.getMonth()]} ${d.getFullYear()}` : c?.fecha

  return (
    <Card glow="green">
      <CardHead icon={<CheckIcon />} title="Confirmación" badge="Confirmada ✓" badgeColor="green" />
      <div className="p-4 flex flex-col items-center text-center gap-3">
        <div className="w-12 h-12 rounded-full bg-green-400/20 flex items-center justify-center text-2xl animate-[popIn_.5s_cubic-bezier(.34,1.56,.64,1)_both]">
          ✅
        </div>
        <div>
          <div className="font-bold text-base">Cita registrada</div>
          <div className="text-xs text-white/40 mt-0.5">SMS de confirmación enviado al paciente</div>
        </div>
        <div className="w-full bg-green-400/8 border border-green-400/15 rounded-lg p-3 grid grid-cols-2 gap-2 text-left">
          {[['Paciente',c?.paciente],['Fecha',dateStr],['Hora',c?.hora],['Tipo',c?.tipo]].map(([l,v])=>(
            <div key={l}>
              <div className="text-[10px] text-white/30">{l}</div>
              <div className="text-xs font-semibold text-green-400">{v}</div>
            </div>
          ))}
        </div>
      </div>
    </Card>
  )
}

// ── Icons ─────────────────────────────────────────────────
const PersonIcon = () => <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="#60a5fa" strokeWidth="2.2"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/></svg>
const CalIcon    = () => <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="#4ade80" strokeWidth="2.2"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>
const CheckIcon  = () => <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="#4ade80" strokeWidth="2.2"><path d="M20 6L9 17l-5-5"/></svg>

// ── Main panel ────────────────────────────────────────────
export default function AgendaPanel({ events, callCount }) {
  // Derive state from events
  const patLoading  = events.some(e => e.type === 'buscar_paciente_loading')
  const patResult   = events.findLast?.(e => e.type === 'buscar_paciente_result')?.result
  const calLoading  = events.some(e => e.type === 'buscar_huecos_loading')
  const calResult   = events.findLast?.(e => e.type === 'buscar_huecos_result')?.result
  const confLoading = events.some(e => e.type === 'confirmar_cita_loading')
  const confResult  = events.findLast?.(e => e.type === 'confirmar_cita_result')?.result

  // Determine proposed slot (first available) and confirmed slot
  const proposedSlot = calResult ? (() => {
    const huecos = (calResult.huecos||[]).filter(h=>h.disponible)
    const byDate = {}
    huecos.forEach(h => (byDate[h.fecha]=byDate[h.fecha]||[]).push(h))
    const firstDate = Object.keys(byDate)[0]
    return firstDate ? { fecha: firstDate, idx: 0 } : null
  })() : null

  const confirmedSlot = confResult?.confirmado && calResult ? (() => {
    const huecos = (calResult.huecos||[]).filter(h=>h.disponible)
    const byDate = {}
    huecos.forEach(h => (byDate[h.fecha]=byDate[h.fecha]||[]).push(h))
    const firstDate = Object.keys(byDate)[0]
    return firstDate ? { fecha: firstDate, idx: 0 } : null
  })() : null

  const hasAny = patLoading || patResult || calLoading || calResult || confLoading || confResult

  return (
    <div className="w-[400px] flex-shrink-0 flex flex-col bg-[#0c0c18] border-l border-white/6 overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-white/6 flex items-center justify-between flex-shrink-0">
        <h3 className="text-[11px] font-semibold uppercase tracking-widest text-white/30">Agenda · En vivo</h3>
        {callCount > 0 && (
          <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-white/5 text-white/30">
            Llamada {callCount}
          </span>
        )}
      </div>

      {/* Cards */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 scrollbar-thin scrollbar-thumb-white/10">
        {!hasAny ? (
          <div className="flex flex-col items-center justify-center h-full gap-3 text-white/20 text-sm text-center py-16">
            <svg width="40" height="40" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.2">
              <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
            </svg>
            La información aparecerá<br/>aquí durante la llamada
          </div>
        ) : (
          <>
            <PatientCard result={patResult} isLoading={patLoading} />
            <CalendarCard result={calResult} isLoading={calLoading} proposedSlot={proposedSlot} confirmedSlot={confirmedSlot} />
            <ConfirmCard result={confResult} isLoading={confLoading} />
          </>
        )}
      </div>
    </div>
  )
}
