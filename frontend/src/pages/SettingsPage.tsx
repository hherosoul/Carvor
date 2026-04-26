import React, { useEffect, useState } from 'react';
import { Typography, Card, Form, Input, Button, message, Space, InputNumber, Modal, Table, Tag } from 'antd';
import { PlusOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { api } from '../services/api';
import { confirmDelete } from '../utils/confirm';
import type { LLMProvider } from '../types';

const { Title, Text } = Typography;

export const SettingsPage: React.FC = () => {
  const [providers, setProviders] = useState<LLMProvider[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingProvider, setEditingProvider] = useState<LLMProvider | null>(null);
  const [form] = Form.useForm();
  const [testing, setTesting] = useState<number | null>(null);

  const loadProviders = () => {
    api.providers.list().then(setProviders);
  };

  useEffect(() => {
    loadProviders();
  }, []);

  const handleAdd = () => {
    setEditingProvider(null);
    form.resetFields();
    setModalOpen(true);
  };

  const handleEdit = (provider: LLMProvider) => {
    setEditingProvider(provider);
    form.setFieldsValue({
      name: provider.name,
      base_url: provider.base_url,
      api_key: '',
      model: provider.model,
      max_context_tokens: provider.max_context_tokens,
    });
    setModalOpen(true);
  };

  const handleSave = async () => {
    const values = await form.validateFields();
    if (editingProvider) {
      await api.providers.update(editingProvider.id, values);
      message.success('配置已更新');
    } else {
      await api.providers.create(values);
      message.success('配置已添加');
    }
    setModalOpen(false);
    form.resetFields();
    setEditingProvider(null);
    loadProviders();
  };

  const handleActivate = async (id: number) => {
    await api.providers.activate(id);
    message.success('已切换启用配置');
    loadProviders();
  };

  const handleDelete = async (id: number) => {
    await api.providers.delete(id);
    message.success('配置已删除');
    loadProviders();
  };

  const handleTest = async (id: number) => {
    setTesting(id);
    try {
      const result = await api.providers.test(id);
      if (result.ok) {
        message.success('连接成功！');
      } else {
        message.error(`连接失败：${result.error}`);
      }
    } finally {
      setTesting(null);
    }
  };

  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: LLMProvider) => (
        <Space>
          <span>{name}</span>
          {record.is_active ? <Tag color="green" icon={<CheckCircleOutlined />}>启用中</Tag> : null}
        </Space>
      ),
    },
    {
      title: 'Base URL',
      dataIndex: 'base_url',
      key: 'base_url',
      ellipsis: true,
    },
    {
      title: '模型',
      dataIndex: 'model',
      key: 'model',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: unknown, record: LLMProvider) => (
        <Space>
          {!record.is_active && (
            <Button size="small" type="link" onClick={() => handleActivate(record.id)}>
              启用
            </Button>
          )}
          <Button size="small" type="link" onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Button
            size="small"
            type="link"
            loading={testing === record.id}
            onClick={() => handleTest(record.id)}
          >
            测试
          </Button>
          {!record.is_active && (
            <Button size="small" type="link" danger onClick={() => confirmDelete('确定删除此配置？', () => handleDelete(record.id))}>
              删除
            </Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div style={{ maxWidth: 800 }}>
      <Title level={4}>设置</Title>

      <Card
        title="LLM API 配置"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
            添加配置
          </Button>
        }
      >
        <Table
          dataSource={providers}
          columns={columns}
          rowKey="id"
          size="small"
          pagination={false}
          locale={{ emptyText: '暂无配置，点击"添加配置"开始' }}
        />
      </Card>

      <Modal
        title={editingProvider ? '编辑配置' : '添加配置'}
        open={modalOpen}
        onOk={handleSave}
        onCancel={() => { setModalOpen(false); form.resetFields(); setEditingProvider(null); }}
        okText="保存"
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="配置名称" rules={[{ required: true, message: '请输入配置名称' }]}>
            <Input placeholder="例如：Moonshot、OpenAI、DeepSeek" />
          </Form.Item>
          <Form.Item name="base_url" label="API Base URL" rules={[{ required: true }]}>
            <Input placeholder="https://api.openai.com/v1" />
          </Form.Item>
          <Form.Item name="api_key" label="API Key" rules={editingProvider ? [] : [{ required: true, message: '请输入API Key' }]}>
            <Input.Password placeholder={editingProvider ? '留空则不修改' : 'sk-...'} />
          </Form.Item>
          <Form.Item name="model" label="模型名称" rules={[{ required: true }]}>
            <Input placeholder="gpt-4o" />
          </Form.Item>
          <Form.Item name="max_context_tokens" label="最大上下文 Token 数">
            <InputNumber min={1000} max={1000000} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};
