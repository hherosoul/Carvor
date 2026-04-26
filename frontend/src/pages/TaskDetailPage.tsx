import React, { useEffect, useState, useRef } from 'react';
import { Typography, Card, Tabs, Table, Button, Space, Upload, message, Tag, Modal, Steps } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';
import { useParams } from 'react-router-dom';
import { api } from '../services/api';
import { useAppStore, type ChatScenario } from '../stores/appStore';
import type { Task, TaskReference, Experiment } from '../types';
import ReactMarkdown from 'react-markdown';

const { Title, Text } = Typography;

const scenarioToTabKey: Record<string, string> = {
  review: 'review',
  method: 'method',
  prompt_doc: 'prompt-doc',
  polish: 'polish',
};

interface EditableDocProps {
  content: string;
  editContent: string;
  editMode: boolean;
  onEditChange: (val: string) => void;
  onToggleEdit: () => void;
  placeholder: string;
  onCopyToChat?: (selectedText: string) => void;
}

const EditableDoc: React.FC<EditableDocProps> = ({
  content, editContent, editMode, onEditChange, onToggleEdit, placeholder, onCopyToChat,
}) => {
  const contentRef = useRef<HTMLDivElement>(null);

  const handleMouseUp = () => {
    if (!onCopyToChat) return;
    const selection = window.getSelection();
    const text = selection?.toString().trim();
    if (text && text.length > 0) {
      onCopyToChat(text);
    }
  };

  if (editMode) {
    return (
      <textarea
        value={editContent}
        onChange={(e) => onEditChange(e.target.value)}
        style={{
          width: '100%',
          minHeight: 400,
          padding: 12,
          border: '1px solid #d9d9d9',
          borderRadius: 6,
          fontSize: 14,
          lineHeight: 1.8,
          fontFamily: 'monospace',
          resize: 'vertical',
        }}
      />
    );
  }
  return (
    <div ref={contentRef} onMouseUp={handleMouseUp} style={{ minHeight: 300, cursor: 'text', userSelect: 'text' }}>
      <ReactMarkdown>{content || placeholder}</ReactMarkdown>
      {onCopyToChat && (
        <div style={{ marginTop: 8, fontSize: 12, color: '#999' }}>
          选中文字后自动复制到AI讨论
        </div>
      )}
    </div>
  );
};

export const TaskDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { setChatContext, openChatPanel, clearChatHistory, chatHistory, chatContext, chatSending } = useAppStore();
  const [task, setTask] = useState<Task | null>(null);
  const [references, setReferences] = useState<TaskReference[]>([]);
  const [experiments, setExperiments] = useState<Experiment[]>([]);

  const [reviewDoc, setReviewDoc] = useState('');
  const [reviewEditDoc, setReviewEditDoc] = useState('');
  const [reviewEditMode, setReviewEditMode] = useState(false);

  const [methodDoc, setMethodDoc] = useState('');
  const [methodEditDoc, setMethodEditDoc] = useState('');
  const [methodEditMode, setMethodEditMode] = useState(false);

  const [researchDoc, setResearchDoc] = useState('');
  const [researchEditDoc, setResearchEditDoc] = useState('');
  const [researchEditMode, setResearchEditMode] = useState(false);

  const [promptDocs, setPromptDocs] = useState<{ filename: string; content: string }[]>([]);

  const [polishContent, setPolishContent] = useState('');
  const [polishEditContent, setPolishEditContent] = useState('');
  const [polishEditMode, setPolishEditMode] = useState(false);

  const [activeTab, setActiveTab] = useState('references');
  const [bibtexContent, setBibtexContent] = useState('');
  const [bibtexModalOpen, setBibtexModalOpen] = useState(false);

  const taskId = Number(id);

  useEffect(() => {
    if (!id) return;
    api.tasks.get(taskId).then(setTask);
    api.tasks.references(taskId).then(setReferences);
    api.tasks.experiments(taskId).then(setExperiments);
    api.tasks.getReview(taskId).then((r) => { setReviewDoc(r.content); setReviewEditDoc(r.content); });
    api.tasks.getMethod(taskId).then((r) => { setMethodDoc(r.content); setMethodEditDoc(r.content); });
    api.tasks.getResearch(taskId).then((r) => { setResearchDoc(r.content); setResearchEditDoc(r.content); });
    api.tasks.getPolish(taskId).then((r) => { setPolishContent(r.content); setPolishEditContent(r.content); });
    api.tasks.promptDocs(taskId).then(setPromptDocs);
    return () => {
      setChatContext({ scenario: null, entityId: null, entityTitle: '' });
    };
  }, [id]);

  const prevSendingRef = useRef(true);
  useEffect(() => {
    if (chatSending) {
      prevSendingRef.current = true;
      return;
    }
    if (!prevSendingRef.current) return;
    prevSendingRef.current = false;

    if (chatHistory.length < 2) return;
    const lastMsg = chatHistory[chatHistory.length - 1];
    if (lastMsg.role !== 'assistant' || !lastMsg.content) return;

    const scenario = chatContext.scenario;
    if (!scenario) return;

    const tabKey = scenarioToTabKey[scenario];
    if (!tabKey) return;

    if (tabKey === 'review') {
      setReviewDoc((prev) => {
        const updated = prev ? prev + '\n\n---\n\n' + lastMsg.content : lastMsg.content;
        setReviewEditDoc(updated);
        api.tasks.saveReview(taskId, updated);
        return updated;
      });
    } else if (tabKey === 'method') {
      setMethodDoc((prev) => {
        const updated = prev ? prev + '\n\n---\n\n' + lastMsg.content : lastMsg.content;
        setMethodEditDoc(updated);
        api.tasks.saveMethod(taskId, updated);
        return updated;
      });
    } else if (tabKey === 'polish') {
      setPolishContent((prev) => {
        const updated = prev ? prev + '\n\n---\n\n' + lastMsg.content : lastMsg.content;
        setPolishEditContent(updated);
        api.tasks.savePolish(taskId, updated);
        return updated;
      });
    }
  }, [chatSending]);

  const activateChat = (scenario: ChatScenario, title: string) => {
    clearChatHistory();
    let existingContent = '';
    if (scenario === 'review') existingContent = reviewEditMode ? reviewEditDoc : reviewDoc;
    else if (scenario === 'method') existingContent = methodEditMode ? methodEditDoc : methodDoc;
    else if (scenario === 'polish') existingContent = polishEditMode ? polishEditContent : polishContent;
    setChatContext({
      scenario,
      entityId: taskId,
      entityTitle: `${task?.name || ''} - ${title}`,
      existingContent,
    });
    openChatPanel();
  };

  const handleGenerateResearch = async () => {
    const result = await api.tasks.generateResearch(taskId);
    if (result.ok) {
      setResearchDoc(result.content || '');
      setResearchEditDoc(result.content || '');
      message.success('研究文档已生成');
    } else {
      message.warning(result.message || '请先完成综述讨论和方法讨论');
    }
  };

  const refColumns = [
    { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
    { title: '作者', dataIndex: 'authors', key: 'authors', render: (a: string[]) => a?.join(', '), ellipsis: true },
    {
      title: 'BibTeX',
      dataIndex: 'bibtex',
      key: 'bibtex',
      width: 80,
      render: (bibtex: string | undefined, record: TaskReference) => {
        if (bibtex) {
          return (
            <Button size="small" type="link" onClick={() => { setBibtexContent(bibtex); setBibtexModalOpen(true); }}>
              查看
            </Button>
          );
        }
        return <Text type="secondary">-</Text>;
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 160,
      render: (_: unknown, record: TaskReference) => (
        <Space size="small">
          <Button size="small" type="link" onClick={async () => {
            const result = await api.tasks.generateBibtex(taskId, record.paper_id);
            message.success('BibTeX 已生成');
            setBibtexContent(result.bibtex || '');
            setBibtexModalOpen(true);
            api.tasks.references(taskId).then(setReferences);
          }}>
            生成BibTeX
          </Button>
          <Button size="small" type="link" danger onClick={() => api.tasks.removeReference(taskId, record.paper_id).then(() => {
            setReferences((prev) => prev.filter((r) => r.paper_id !== record.paper_id));
          })}>
            移除
          </Button>
        </Space>
      ),
    },
  ];

  const expColumns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: '日志路径', dataIndex: 'log_path', key: 'log_path', ellipsis: true },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at' },
    {
      title: '操作',
      key: 'action',
      render: (_: unknown, record: Experiment) => (
        <Button
          size="small"
          onClick={() => api.tasks.analyzeExperiment(taskId, record.id).then((r) => message.info(r.report?.substring(0, 100)))}
        >
          分析
        </Button>
      ),
    },
  ];

  if (!task) return null;

  const currentStep = activeTab === 'references' ? 0
    : activeTab === 'review' ? 1
    : activeTab === 'method' ? 2
    : activeTab === 'research' ? 3
    : activeTab === 'prompt-doc' ? 4
    : activeTab === 'experiments' ? 5
    : activeTab === 'polish' ? 6 : 0;

  return (
    <div>
      <Title level={4}>{task.name}</Title>
      {task.research_goal && (
        <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
          {task.research_goal}
        </Text>
      )}

      <Steps
        current={currentStep}
        size="small"
        style={{ marginBottom: 20 }}
        items={[
          { title: '引用池' },
          { title: '综述讨论' },
          { title: '方法讨论' },
          { title: '研究文档' },
          { title: '提示词文档' },
          { title: '实验' },
          { title: '论文润色' },
        ]}
      />

      <Tabs activeKey={activeTab} onChange={setActiveTab} items={[
        {
          key: 'references',
          label: '引用池',
          children: (
            <Table
              dataSource={references}
              columns={refColumns}
              rowKey="paper_id"
              size="small"
              pagination={false}
            />
          ),
        },
        {
          key: 'review',
          label: '综述讨论',
          children: (
            <Card
              title="文献综述"
              extra={
                <Space>
                  <Button size="small" icon={<DownloadOutlined />} onClick={() => api.tasks.exportDoc(taskId, 'review')} disabled={!reviewDoc}>
                    导出
                  </Button>
                  <Button size="small" onClick={() => {
                    if (reviewEditMode) {
                      setReviewDoc(reviewEditDoc);
                      api.tasks.saveReview(taskId, reviewEditDoc);
                    }
                    setReviewEditMode(!reviewEditMode);
                  }}>
                    {reviewEditMode ? '保存' : '编辑'}
                  </Button>
                  <Button type="primary" onClick={() => activateChat('review', '综述讨论')}>
                    与AI讨论
                  </Button>
                </Space>
              }
            >
              <EditableDoc
                content={reviewDoc}
                editContent={reviewEditDoc}
                editMode={reviewEditMode}
                onEditChange={setReviewEditDoc}
                onToggleEdit={() => setReviewEditMode(!reviewEditMode)}
                placeholder={'*暂无综述内容，点击「与AI讨论」开始综述讨论*'}
              />
            </Card>
          ),
        },
        {
          key: 'method',
          label: '方法讨论',
          children: (
            <Card
              title="研究方法"
              extra={
                <Space>
                  <Button size="small" icon={<DownloadOutlined />} onClick={() => api.tasks.exportDoc(taskId, 'method')} disabled={!methodDoc}>
                    导出
                  </Button>
                  <Button size="small" onClick={() => {
                    if (methodEditMode) {
                      setMethodDoc(methodEditDoc);
                      api.tasks.saveMethod(taskId, methodEditDoc);
                    }
                    setMethodEditMode(!methodEditMode);
                  }}>
                    {methodEditMode ? '保存' : '编辑'}
                  </Button>
                  <Button type="primary" onClick={() => activateChat('method', '方法讨论')}>
                    与AI讨论
                  </Button>
                </Space>
              }
            >
              <EditableDoc
                content={methodDoc}
                editContent={methodEditDoc}
                editMode={methodEditMode}
                onEditChange={setMethodEditDoc}
                onToggleEdit={() => setMethodEditMode(!methodEditMode)}
                placeholder={'*暂无方法内容，点击「与AI讨论」开始方法讨论*'}
              />
            </Card>
          ),
        },
        {
          key: 'research',
          label: '研究文档',
          children: (
            <Card
              title="研究文档"
              extra={
                <Space>
                  <Button size="small" icon={<DownloadOutlined />} onClick={() => api.tasks.exportDoc(taskId, 'research')} disabled={!researchDoc}>
                    导出
                  </Button>
                  <Button size="small" onClick={() => {
                    if (researchEditMode) {
                      setResearchDoc(researchEditDoc);
                      api.tasks.saveResearch(taskId, researchEditDoc);
                    }
                    setResearchEditMode(!researchEditMode);
                  }}>
                    {researchEditMode ? '保存' : '编辑'}
                  </Button>
                  <Button type="primary" onClick={handleGenerateResearch}>
                    生成研究文档
                  </Button>
                </Space>
              }
            >
              <EditableDoc
                content={researchDoc}
                editContent={researchEditDoc}
                editMode={researchEditMode}
                onEditChange={setResearchEditDoc}
                onToggleEdit={() => setResearchEditMode(!researchEditMode)}
                placeholder={'*暂无研究文档。请先完成综述讨论和方法讨论，然后点击「生成研究文档」*'}
              />
            </Card>
          ),
        },
        {
          key: 'prompt-doc',
          label: '提示词文档',
          children: (
            <Space direction="vertical" style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <Button type="primary" onClick={() => activateChat('prompt_doc', '提示词文档')}>
                  与AI讨论生成
                </Button>
              </div>
              {promptDocs.length === 0 ? (
                <Card>
                  <div style={{ minHeight: 200, color: '#999', textAlign: 'center', paddingTop: 60 }}>
                    暂无提示词文档，点击"与AI讨论生成"开始创建
                  </div>
                </Card>
              ) : (
                promptDocs.map((doc, idx) => (
                  <Card key={idx} title={doc.filename} extra={
                    <Button size="small" icon={<DownloadOutlined />} onClick={() => api.tasks.exportPromptDoc(taskId, doc.filename)}>
                      导出
                    </Button>
                  }>
                    <ReactMarkdown>{doc.content}</ReactMarkdown>
                  </Card>
                ))
              )}
            </Space>
          ),
        },
        {
          key: 'experiments',
          label: '实验',
          children: (
            <Space direction="vertical" style={{ width: '100%' }}>
              <Upload
                accept=".json,.csv,.txt,.log,.jsonl"
                beforeUpload={(file) => {
                  api.tasks.uploadExperiment(taskId, file).then(() => {
                    message.success('日志已上传');
                    api.tasks.experiments(taskId).then(setExperiments);
                  }).catch((err) => {
                    message.error('上传失败：' + (err.message || '未知错误'));
                  });
                  return false;
                }}
                showUploadList={false}
              >
                <Button>上传训练日志</Button>
              </Upload>
              <Text type="secondary" style={{ fontSize: 12 }}>支持 JSON / CSV / TXT / LOG / JSONL 格式</Text>
              <Table
                dataSource={experiments}
                columns={expColumns}
                rowKey="id"
                size="small"
                pagination={false}
              />
            </Space>
          ),
        },
        {
          key: 'polish',
          label: '论文润色',
          children: (
            <Card
              title="论文润色"
              extra={
                <Space>
                  <Upload
                    accept=".docx,.doc"
                    showUploadList={false}
                    beforeUpload={(file) => {
                      api.tasks.uploadPolishDocx(taskId, file).then((result) => {
                        setPolishContent(result.content);
                        setPolishEditContent(result.content);
                        message.success(`已导入 ${result.filename}`);
                      }).catch((err) => {
                        message.error('导入失败：' + (err.message || '未知错误'));
                      });
                      return false;
                    }}
                  >
                    <Button size="small">上传论文</Button>
                  </Upload>
                  <Button size="small" icon={<DownloadOutlined />} onClick={() => api.tasks.exportDoc(taskId, 'polish')} disabled={!polishContent}>
                    导出
                  </Button>
                  <Button size="small" onClick={() => {
                    if (polishEditMode) {
                      setPolishContent(polishEditContent);
                      api.tasks.savePolish(taskId, polishEditContent);
                    }
                    setPolishEditMode(!polishEditMode);
                  }}>
                    {polishEditMode ? '保存' : '编辑'}
                  </Button>
                  <Button type="primary" onClick={() => activateChat('polish', '论文润色')}>
                    与AI讨论润色
                  </Button>
                </Space>
              }
            >
              <EditableDoc
                content={polishContent}
                editContent={polishEditContent}
                editMode={polishEditMode}
                onEditChange={setPolishEditContent}
                onToggleEdit={() => setPolishEditMode(!polishEditMode)}
                placeholder={'*暂无润色内容，点击「上传论文」导入或「与AI讨论润色」开始*'}
                onCopyToChat={(text) => {
                  activateChat('polish', '论文润色');
                  setTimeout(() => {
                    useAppStore.getState().appendChatMessage({ role: 'user', content: `请润色以下内容：\n${text}` });
                  }, 100);
                }}
              />
            </Card>
          ),
        },
      ]} />

      <Modal
        title="BibTeX"
        open={bibtexModalOpen}
        onCancel={() => setBibtexModalOpen(false)}
        footer={null}
        width={600}
      >
        <pre style={{
          background: '#f5f5f5',
          padding: 16,
          borderRadius: 6,
          fontSize: 13,
          lineHeight: 1.6,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-all',
        }}>
          {bibtexContent}
        </pre>
      </Modal>
    </div>
  );
};
