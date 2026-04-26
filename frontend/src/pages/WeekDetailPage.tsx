import React, { useEffect, useState } from 'react';
import { Card, Typography, Tag, Button, Space, Spin, Empty, Modal, Select, message } from 'antd';
import { BookOutlined, PlusOutlined, HeartOutlined, HeartFilled, CheckCircleFilled, EditOutlined, ThunderboltOutlined } from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { useAppStore } from '../stores/appStore';
import { api } from '../services/api';
import type { Paper, Task } from '../types';

const { Text, Title } = Typography;

export const WeekDetailPage: React.FC = () => {
  const { date } = useParams<{ date: string }>();
  const navigate = useNavigate();
  const { currentLibraryId, setChatContext, openChatPanel, clearChatHistory, currentTaskId } = useAppStore();
  const [papers, setPapers] = useState<Paper[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);
  const [noteModalOpen, setNoteModalOpen] = useState(false);
  const [notePaper, setNotePaper] = useState<Paper | null>(null);
  const [noteText, setNoteText] = useState('');
  const [noteOptimizing, setNoteOptimizing] = useState(false);

  useEffect(() => {
    if (!currentLibraryId || !date) return;
    setLoading(true);
    api.timeline
      .getWeek(date, currentLibraryId)
      .then(setPapers)
      .finally(() => setLoading(false));
    api.tasks.list().then(setTasks);
  }, [currentLibraryId, date]);

  const handleMarkRead = async (paperId: number) => {
    if (!currentLibraryId) return;
    await api.papers.markRead(paperId, currentLibraryId);
    setPapers((prev) =>
      prev.map((p) => (p.id === paperId ? { ...p, is_read: 1 } : p))
    );
  };

  const handleToggleInterest = async (paperId: number, current: number) => {
    if (!currentLibraryId) return;
    if (current === 1) {
      await api.papers.markInterest(paperId, currentLibraryId);
      setPapers((prev) =>
        prev.map((p) => (p.id === paperId ? { ...p, is_interested: 0 } : p))
      );
    } else {
      await api.papers.markInterest(paperId, currentLibraryId);
      setPapers((prev) =>
        prev.map((p) => (p.id === paperId ? { ...p, is_interested: 1 } : p))
      );
    }
  };

  const handleDeepReading = (paper: Paper) => {
    clearChatHistory();
    setChatContext({
      scenario: 'deep_reading',
      entityId: paper.id,
      entityTitle: paper.title,
    });
    openChatPanel();
  };

  const handleAddToTask = async (paperId: number) => {
    if (tasks.length === 0) {
      message.warning('请先创建任务');
      return;
    }

    const defaultTaskId = currentTaskId || tasks[0]?.id;

    Modal.confirm({
      title: '加入引用池',
      icon: <PlusOutlined style={{ color: '#1677ff' }} />,
      content: (
        <div style={{ marginTop: 12 }}>
          <Select
            id="task-select-modal"
            style={{ width: '100%' }}
            defaultValue={defaultTaskId}
            options={tasks.map((t) => ({ label: t.name, value: t.id }))}
          />
        </div>
      ),
      okText: '加入',
      cancelText: '取消',
      centered: true,
      onOk: async () => {
        const selectEl = document.querySelector('#task-select-modal .ant-select-selection-item') as HTMLElement;
        const taskName = selectEl?.getAttribute('title');
        const task = tasks.find((t) => t.name === taskName) || tasks.find((t) => t.id === defaultTaskId);
        if (task) {
          try {
            const result = await api.tasks.addReference(task.id, paperId);
            if (result.message === 'Already in reference pool') {
              message.warning('该论文已在引用池中');
            } else {
              message.success('已加入引用池');
            }
          } catch (err: any) {
            if (err.message?.includes('Already')) {
              message.warning('该论文已在引用池中');
            } else {
              message.success('已加入引用池');
            }
          }
        }
      },
    });
  };

  const handleOpenNote = (paper: Paper) => {
    setNotePaper(paper);
    setNoteText('');
    setNoteModalOpen(true);
  };

  const handleSaveNote = async () => {
    if (!notePaper || !noteText.trim()) return;
    try {
      await api.notes.create(notePaper.id, noteText.trim());
      message.success('笔记已保存');
      setNoteModalOpen(false);
    } catch (err: any) {
      message.error(`保存失败：${err.message}`);
    }
  };

  const handleOptimizeNote = async () => {
    if (!noteText.trim()) {
      message.warning('请先输入笔记内容');
      return;
    }
    setNoteOptimizing(true);
    try {
      const result = await api.notes.optimize(noteText, notePaper?.title || '');
      setNoteText(result.optimized_note);
      message.success('笔记已优化');
    } catch (err: unknown) {
      message.error(`优化失败：${err instanceof Error ? err.message : '未知错误'}`);
    } finally {
      setNoteOptimizing(false);
    }
  };

  if (loading) {
    return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  }

  return (
    <div>
      <Title level={4}>周详情：{date}</Title>
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        {papers.length === 0 && <Empty description="本周无论文" />}
        {papers.map((paper) => (
          <Card key={paper.id} size="small" style={{ borderRadius: 8 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div style={{ flex: 1, paddingRight: 16 }}>
                <Text strong style={{ fontSize: 15 }}>
                  {paper.title}
                </Text>
                <div style={{ marginTop: 4, color: '#666', fontSize: 13 }}>
                  {Array.isArray(paper.authors) ? paper.authors.join(', ') : paper.authors}
                  {paper.institution && ` · ${paper.institution}`}
                </div>
                {paper.structured_summary && (
                  <div style={{ marginTop: 8, color: '#444', fontSize: 14, lineHeight: 1.6 }}>
                    {paper.structured_summary}
                  </div>
                )}
                <div style={{ marginTop: 8, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  <Tag color={paper.source === 'llm_search' ? 'blue' : 'green'}>
                    {paper.source === 'llm_search' ? 'LLM搜索' : '手动导入'}
                  </Tag>
                  {paper.is_read === 1 && <Tag icon={<CheckCircleFilled />} color="success">已读</Tag>}
                  {paper.is_interested === 1 && <Tag icon={<HeartFilled />} color="warning">感兴趣</Tag>}
                </div>
              </div>
              <Space direction="vertical" size={8}>
                <Button
                  size="middle"
                  type="primary"
                  ghost
                  icon={<BookOutlined />}
                  onClick={() => handleDeepReading(paper)}
                  style={{ borderRadius: 6, width: '100%' }}
                >
                  深度阅读
                </Button>
                <Button
                  size="middle"
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={() => handleAddToTask(paper.id)}
                  style={{ borderRadius: 6, width: '100%' }}
                >
                  加入引用池
                </Button>
                <Button
                  size="middle"
                  icon={paper.is_interested === 1 ? <HeartFilled /> : <HeartOutlined />}
                  onClick={() => handleToggleInterest(paper.id, paper.is_interested || 0)}
                  style={{
                    borderRadius: 6,
                    width: '100%',
                    color: paper.is_interested === 1 ? '#ff4d4f' : undefined,
                    borderColor: paper.is_interested === 1 ? '#ff4d4f' : undefined,
                  }}
                >
                  {paper.is_interested === 1 ? '取消感兴趣' : '标记感兴趣'}
                </Button>
                <Button
                  size="middle"
                  icon={<EditOutlined />}
                  onClick={() => handleOpenNote(paper)}
                  style={{ borderRadius: 6, width: '100%' }}
                >
                  写笔记
                </Button>
                {paper.is_read !== 1 && (
                  <Button
                    size="middle"
                    onClick={() => handleMarkRead(paper.id)}
                    style={{ borderRadius: 6, width: '100%' }}
                  >
                    标记已读
                  </Button>
                )}
              </Space>
            </div>
          </Card>
        ))}
      </Space>

      <Modal
        title={
          <span style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingRight: 28 }}>
            <span>{notePaper ? `笔记 - ${notePaper.title.substring(0, 30)}...` : '笔记'}</span>
            <Button
              size="small"
              type="primary"
              ghost
              icon={<ThunderboltOutlined />}
              onClick={handleOptimizeNote}
              loading={noteOptimizing}
            >
              AI优化
            </Button>
          </span>
        }
        open={noteModalOpen}
        onOk={handleSaveNote}
        onCancel={() => setNoteModalOpen(false)}
        okText="保存"
        cancelText="取消"
        centered
      >
        <textarea
          value={noteText}
          onChange={(e) => setNoteText(e.target.value)}
          placeholder="记录阅读这篇论文的灵感和想法..."
          style={{
            width: '100%',
            minHeight: 200,
            padding: 12,
            border: '1px solid #d9d9d9',
            borderRadius: 6,
            fontSize: 14,
            lineHeight: 1.8,
            resize: 'vertical',
            marginTop: 8,
          }}
        />
      </Modal>
    </div>
  );
};
