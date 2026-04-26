import React, { useRef, useEffect, useState } from 'react';
import { Input, Button, Space, Typography, Spin } from 'antd';
import { SendOutlined, CloseOutlined } from '@ant-design/icons';
import { useAppStore, type ChatScenario } from '../stores/appStore';
import { useChatStream } from '../hooks/useChatStream';
import ReactMarkdown from 'react-markdown';

const { TextArea } = Input;
const { Text } = Typography;

const scenarioLabels: Record<NonNullable<ChatScenario>, string> = {
  deep_reading: '深度阅读',
  idea_refine: 'Idea 锤炼',
  review: '综述讨论',
  method: '方法讨论',
  prompt_doc: '提示词文档',
  polish: '论文润色',
};

export const ChatPanel: React.FC = () => {
  const { chatHistory, chatContext, chatSending, clearChatHistory, appendChatMessage, setChatContext, setChatSending } = useAppStore();
  const { sendChat } = useChatStream();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  const handleSend = () => {
    if (!input.trim()) return;
    const { scenario, entityId, existingContent } = chatContext;
    appendChatMessage({ role: 'user', content: input });
    appendChatMessage({ role: 'assistant', content: '' });

    if (scenario && entityId) {
      sendChat(scenario, {
        entity_id: entityId,
        user_input: input,
        conversation_id: useAppStore.getState().currentConversationId,
        existing_content: existingContent || '',
      });
    }

    setInput('');
  };

  const handleClose = () => {
    clearChatHistory();
    setChatContext({ scenario: null, entityId: null, entityTitle: '', existingContent: '' });
  };

  const title = chatContext.scenario
    ? scenarioLabels[chatContext.scenario]
    : 'AI 对话';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div
        style={{
          padding: '10px 16px',
          borderBottom: '1px solid #f0f0f0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Text strong>{title}</Text>
        <Space size="small">
          <Button size="small" type="text" onClick={clearChatHistory}>
            清空
          </Button>
          <Button size="small" type="text" icon={<CloseOutlined />} onClick={handleClose} />
        </Space>
      </div>

      {chatContext.entityTitle && (
        <div
          style={{
            padding: '6px 16px',
            background: '#f6f8fa',
            borderBottom: '1px solid #f0f0f0',
            fontSize: 12,
            color: '#666',
          }}
        >
          {chatContext.entityTitle}
        </div>
      )}

      <div style={{ flex: 1, overflow: 'auto', padding: 16 }}>
        {chatHistory.length === 0 && (
          <div style={{ color: '#bbb', textAlign: 'center', marginTop: 40 }}>
            在主内容区操作后，在此处与AI对话
          </div>
        )}
        {chatHistory.map((msg, idx) => (
          <div
            key={idx}
            style={{
              marginBottom: 12,
              display: 'flex',
              justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
            }}
          >
            <div
              style={{
                maxWidth: '85%',
                padding: '8px 12px',
                borderRadius: 8,
                background: msg.role === 'user' ? '#1677ff' : '#f5f5f5',
                color: msg.role === 'user' ? '#fff' : '#333',
              }}
            >
              {msg.role === 'assistant' ? (
                msg.content ? (
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                ) : (
                  <Spin size="small" />
                )
              ) : (
                msg.content
              )}
            </div>
          </div>
        ))}
        {chatSending && chatHistory.length > 0 && chatHistory[chatHistory.length - 1]?.role === 'assistant' && !chatHistory[chatHistory.length - 1]?.content && (
          <div style={{ textAlign: 'center', color: '#999', fontSize: 12, marginTop: 4 }}>
            AI 正在思考...
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div style={{ padding: 12, borderTop: '1px solid #f0f0f0' }}>
        <Space.Compact style={{ width: '100%' }}>
          <TextArea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              chatContext.scenario
                ? `输入关于${scenarioLabels[chatContext.scenario]}的问题...`
                : '输入消息...'
            }
            autoSize={{ minRows: 1, maxRows: 4 }}
            onPressEnter={(e) => {
              if (!e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
          />
          <Button type="primary" icon={<SendOutlined />} onClick={handleSend} loading={chatSending} />
        </Space.Compact>
      </div>
    </div>
  );
};
