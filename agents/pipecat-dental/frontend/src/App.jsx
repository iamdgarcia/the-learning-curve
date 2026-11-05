import { useState, useEffect, useCallback } from 'react'
import { PipecatClient } from '@pipecat-ai/client-js'
import { PipecatClientProvider } from '@pipecat-ai/client-react'
import { SmallWebRTCTransport } from '@pipecat-ai/small-webrtc-transport'

import { ConnectButton } from '@/components/pipecat/connect-button'
import { usePipecatClient } from '@pipecat-ai/client-react'
import { BotAudioOutput, unlockBotAudio } from '@/components/pipecat/bot-audio'
import { DuplexTimeline } from '@/components/pipecat/duplex-timeline'
import { LatencyPanel } from '@/components/pipecat/latency-panel'
import { AudioVisualizerWave } from '@/components/pipecat/audio-visualizer-wave'
import AgendaPanel from '@/components/AgendaPanel'

const BOT_URL = `http://${location.hostname}:7860/start`
const WS_URL  = `ws://${location.hostname}:7860/events`

function pad(n) { return String(n).padStart(2, '0') }

// ── Create pipecat client once ─────────────────────────────
// Transport created lazily (WebRTC requires secure context; defer until connect)
function createClient() {
  return new PipecatClient({
    transport: new SmallWebRTCTransport(),
    enableMic: true,
    enableCam: false,
  })
}

function DemoApp() {
  const pipecatClient = usePipecatClient()
  const [transcript, setTranscript] = useState(null)
  const [timerSecs, setTimerSecs] = useState(null)
  const [toolTag, setToolTag]     = useState(null)
  const [agendaEvents, setAgendaEvents] = useState([])
  const [callCount, setCallCount] = useState(0)
  const [connected, setConnected] = useState(false)

  // ── Timer ──────────────────────────────────────────────
  useEffect(() => {
    if (!connected) return
    setTimerSecs(0)
    let s = 0
    const id = setInterval(() => setTimerSecs(++s), 1000)
    return () => clearInterval(id)
  }, [connected])

  // ── Tool tag auto-hide ─────────────────────────────────
  const showTag = useCallback((text) => {
    setToolTag(text)
    const t = setTimeout(() => setToolTag(null), 3500)
    return () => clearTimeout(t)
  }, [])

  // ── Events WebSocket ───────────────────────────────────
  useEffect(() => {
    let ws, dead = false
    function connect() {
      if (dead) return
      ws = new WebSocket(WS_URL)
      ws.onmessage = (e) => {
        try {
          const ev = JSON.parse(e.data)
          if (ev.type === 'call_start') {
            setCallCount(c => c + 1)
            setAgendaEvents([])           // reset panels for new call
          }
          if (ev.type === 'call_end') setConnected(false)
          if (ev.type === 'tool_call') {
            showTag(`${ev.tool}()`)
            setAgendaEvents(prev => [...prev, { type: `${ev.tool}_loading`, id: Date.now() }])
          }
          if (ev.type === 'tool_result') {
            setAgendaEvents(prev => [...prev, { type: `${ev.tool}_result`, result: ev.result, id: Date.now() }])
          }
        } catch {}
      }
      ws.onclose = () => !dead && setTimeout(connect, 3000)
    }
    connect()
    return () => { dead = true; ws?.close() }
  }, [showTag])

  const timerStr = timerSecs == null ? null
    : `${Math.floor(timerSecs / 60)}:${pad(timerSecs % 60)}`

  return (
    <div className="flex h-screen bg-black text-white overflow-hidden">

      {/* ── LEFT: Sofía ──────────────────────────────── */}
      <div className="flex flex-col flex-1 min-w-0 relative bg-[#080810]">

        {/* Header */}
        <header className="absolute inset-x-0 top-0 z-10 flex items-center justify-between px-6 py-4"
          style={{ background: 'linear-gradient(to bottom, rgba(8,8,16,.95) 0%, transparent 100%)' }}>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center flex-shrink-0">
              <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="white" strokeWidth="2.2">
                <path d="M12 2C9.5 2 7 4.5 7 7.5c0 1.8.6 3.5 1.4 5.2C9.8 15.3 11 18 12 22c1-4 2.2-6.7 3.6-9.3.8-1.7 1.4-3.4 1.4-5.2C17 4.5 14.5 2 12 2z"/>
              </svg>
            </div>
            <span className="font-semibold text-sm">Clínica Dental Sonrisa</span>
          </div>

          <div className="flex items-center gap-2">
            {toolTag && (
              <span className="font-mono text-xs px-2 py-1 rounded bg-blue-950/60 border border-blue-500/30 text-blue-300">
                {toolTag}
              </span>
            )}
            {timerStr && (
              <span className="text-xs font-semibold tabular-nums text-white/40">{timerStr}</span>
            )}
            <ConnectButton
              onConnect={async () => {
                unlockBotAudio()  // must be sync inside the click gesture
                setConnected(true)
                await pipecatClient.startBotAndConnect({
                  endpoint: BOT_URL,
                  requestData: { transport: 'webrtc', enableDefaultIceServers: true },
                })
              }}
              onDisconnect={() => {
                setConnected(false)
                pipecatClient.disconnect()
              }}
              stateProps={{
                disconnected: { children: '📞 Iniciar llamada' },
                ready: { children: '✕ Colgar' },
              }}
            />
          </div>
        </header>

        {/* Wave visualizer — hero */}
        <div className="flex-1 flex items-center justify-center relative">
          <AudioVisualizerWave participantType="bot" size={280} />
          <div className="absolute bottom-20 left-0 right-0 text-center pointer-events-none">
            <h2 className="text-2xl font-bold tracking-tight">Sofía</h2>
            <p className="text-sm text-white/40 mt-1">Asistente de Clínica Dental Sonrisa</p>
          </div>
        </div>

        {/* Transcript strip */}
        {transcript && (
          <div className="absolute bottom-[110px] inset-x-0 px-6 z-10 pointer-events-none">
            <div className="text-sm">
              <span className={`text-xs font-semibold uppercase tracking-widest mr-2 ${transcript.speaker === 'bot' ? 'text-blue-400' : 'text-violet-400'}`}>
                {transcript.speaker === 'bot' ? 'Sofía' : 'Paciente'}
              </span>
              <span className="text-white/80">{transcript.text}</span>
            </div>
          </div>
        )}

        {/* DuplexTimeline + latency breakdown */}
        <div className="flex-shrink-0 px-4 pb-4 flex flex-col gap-3">
          <DuplexTimeline className="rounded-xl overflow-hidden" />
          <LatencyPanel className="px-1" />
        </div>

      </div>

      {/* ── RIGHT: Agenda ─────────────────────────────── */}
      <AgendaPanel events={agendaEvents} callCount={callCount} />

      {/* Audio output (invisible) */}
      <BotAudioOutput />
    </div>
  )
}

export default function App() {
  // shortcut: create client at mount — must open from localhost (WebRTC needs secure context)
  // If you see "WebRTC not supported" open http://localhost:5173 instead of the LAN IP
  const [client] = useState(() => {
    try { return createClient() } catch { return null }
  })

  if (!client) return (
    <div className="flex h-screen items-center justify-center bg-black text-white flex-col gap-4">
      <div className="text-2xl">⚠️ WebRTC no disponible</div>
      <div className="text-white/60 text-sm">Abre desde <code className="bg-white/10 px-2 py-1 rounded">http://localhost:5173</code></div>
      <div className="text-white/40 text-xs">WebRTC requiere contexto seguro (localhost o HTTPS)</div>
    </div>
  )

  return (
    <PipecatClientProvider client={client}>
      <DemoApp />
    </PipecatClientProvider>
  )
}
