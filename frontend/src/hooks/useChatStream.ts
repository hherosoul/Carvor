import { useCallback } from 'react';
import { useAppStore } from '../stores/appStore';

export function useChatStream() {
  const appendChatMessage = useAppStore((s) => s.appendChatMessage);
  const updateLastAssistantMessage = useAppStore((s) => s.updateLastAssistantMessage);
  const setChatSending = useAppStore((s) => s.setChatSending);
  const setCurrentConversation = useAppStore((s) => s.setCurrentConversation);

  const sendChat = useCallback(
    async (scenario: string, payload: Record<string, unknown>) => {
      setChatSending(true);
      try {
        const res = await fetch('/api/chat/stream', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ scenario, ...payload }),
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: res.statusText }));
          throw new Error(err.detail || res.statusText);
        }

        const reader = res.body?.getReader();
        if (!reader) throw new Error('No response body');

        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          let currentEvent = '';
          for (const line of lines) {
            if (line.startsWith('event: ')) {
              currentEvent = line.slice(7).trim();
            } else if (line.startsWith('data: ')) {
              const dataStr = line.slice(6);
              try {
                const data = JSON.parse(dataStr);
                if (currentEvent === 'conversation.created' && data.conversation_id) {
                  setCurrentConversation(data.conversation_id);
                } else if (currentEvent === 'chunk' && data.content) {
                  updateLastAssistantMessage(data.content);
                } else if (currentEvent === 'done') {
                  // stream complete
                } else if (currentEvent === 'error') {
                  updateLastAssistantMessage(`\n[Error: ${data.message || 'Unknown error'}]`);
                }
              } catch {
                // ignore parse errors
              }
              currentEvent = '';
            }
          }
        }
      } catch (err: unknown) {
        updateLastAssistantMessage(`\n[Error: ${err instanceof Error ? err.message : 'Unknown error'}]`);
      } finally {
        setChatSending(false);
      }
    },
    [appendChatMessage, updateLastAssistantMessage, setChatSending, setCurrentConversation]
  );

  return { sendChat };
}
