import { useEffect, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { useAuthStore } from '@/stores/authStore'

/**
 * Real-time notification socket.
 *
 * Connects to the Channels consumer at `/ws/notifications/?token=<jwt>` and,
 * on each pushed event, refreshes the bell (unread count + list) and toasts new
 * notifications. Reconnects with backoff. If the WebSocket can't connect (e.g.
 * the server is running under plain WSGI without daphne/ASGI), it fails quietly
 * and the existing polling in TopBar keeps the bell working.
 */
export function useNotificationSocket() {
  const qc = useQueryClient()
  const token = useAuthStore(s => s.tokens?.access)
  const socketRef = useRef<WebSocket | null>(null)
  const retryRef = useRef(0)
  const closedRef = useRef(false)

  useEffect(() => {
    if (!token) return
    closedRef.current = false
    let reconnectTimer: ReturnType<typeof setTimeout>

    const refreshBell = () => {
      qc.invalidateQueries({ queryKey: ['notifications'] })
      qc.invalidateQueries({ queryKey: ['notifications-unread-count'] })
    }

    const connect = () => {
      if (closedRef.current) return
      const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const url = `${proto}//${window.location.host}/ws/notifications/?token=${token}`
      let ws: WebSocket
      try {
        ws = new WebSocket(url)
      } catch {
        return // WS unavailable — polling fallback handles it
      }
      socketRef.current = ws

      ws.onopen = () => { retryRef.current = 0 }

      ws.onmessage = (evt) => {
        try {
          const msg = JSON.parse(evt.data)
          if (msg.type === 'new_notification') {
            refreshBell()
            if (msg.notification?.title) {
              toast(msg.notification.title, { icon: '🔔' })
            }
          } else if (msg.type === 'unread_count') {
            refreshBell()
          }
        } catch {
          /* ignore malformed frames */
        }
      }

      ws.onclose = () => {
        socketRef.current = null
        if (closedRef.current) return
        // Exponential backoff, capped at 30s, give up after several tries.
        retryRef.current += 1
        if (retryRef.current > 6) return
        const delay = Math.min(1000 * 2 ** retryRef.current, 30000)
        reconnectTimer = setTimeout(connect, delay)
      }

      ws.onerror = () => { try { ws.close() } catch { /* noop */ } }
    }

    connect()

    return () => {
      closedRef.current = true
      clearTimeout(reconnectTimer)
      try { socketRef.current?.close() } catch { /* noop */ }
      socketRef.current = null
    }
  }, [token, qc])
}
