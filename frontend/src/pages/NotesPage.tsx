import React, { useEffect, useState } from 'react';
import { Typography, Card, List, Button, Space, Empty, Spin, Modal, message } from 'antd';
import { DeleteOutlined, EyeOutlined, EditOutlined } from '@ant-design/icons';
import { api } from '../services/api';
import { confirmDelete } from '../utils/confirm';
import type { PaperNote } from '../types';

const { Title, Text } = Typography;

export const NotesPage: React.FC = () => {
  const [notes, setNotes] = useState<PaperNote[]>([]);
  const [loading, setLoading] = useState(false);
  const [viewNote, setViewNote] = useState<PaperNote | null>(null);

  const loadNotes = () => {
    setLoading(true);
    api.notes
      .list(1, 50)
      .then(setNotes)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadNotes();
  }, []);

  const handleDelete = async (id: number) => {
    await api.notes.delete(id);
    message.success('笔记已删除');
    loadNotes();
  };

  const handleView = async (id: number) => {
    const note = await api.notes.get(id);
    setViewNote(note);
  };

  if (loading) {
    return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>阅读笔记</Title>
      </div>

      {notes.length === 0 ? (
        <Empty description="暂无笔记，在论文周详情中点击'写笔记'开始记录" />
      ) : (
        <List
          dataSource={notes}
          renderItem={(note) => (
            <List.Item
              actions={[
                <Button
                  size="small"
                  type="link"
                  icon={<EyeOutlined />}
                  onClick={() => handleView(note.id)}
                >
                  查看
                </Button>,
                <Button
                  size="small"
                  type="link"
                  danger
                  icon={<DeleteOutlined />}
                  onClick={() => confirmDelete('确定删除此笔记？', () => handleDelete(note.id))}
                >
                  删除
                </Button>,
              ]}
            >
              <List.Item.Meta
                avatar={<EditOutlined style={{ fontSize: 20, color: '#1677ff', marginTop: 4 }} />}
                title={
                  <span style={{ cursor: 'pointer' }} onClick={() => handleView(note.id)}>
                    {note.content.length > 60 ? note.content.substring(0, 60) + '...' : note.content}
                  </span>
                }
                description={
                  <Space size={8}>
                    <Text type="secondary">{note.created_at.substring(0, 16)}</Text>
                    <Text type="secondary">论文：{note.paper_title}</Text>
                  </Space>
                }
              />
            </List.Item>
          )}
        />
      )}

      <Modal
        title={viewNote ? `笔记 - ${viewNote.paper_title}` : '笔记'}
        open={!!viewNote}
        onCancel={() => setViewNote(null)}
        footer={null}
        width={600}
        centered
      >
        {viewNote && (
          <div>
            <div style={{ marginBottom: 12 }}>
              <Text type="secondary">时间：{viewNote.created_at.substring(0, 16)}</Text>
            </div>
            <div style={{
              padding: 16,
              background: '#f9f9f9',
              borderRadius: 8,
              lineHeight: 1.8,
              fontSize: 14,
              whiteSpace: 'pre-wrap',
            }}>
              {viewNote.content}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
