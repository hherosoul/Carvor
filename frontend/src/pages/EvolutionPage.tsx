import React, { useEffect, useState } from 'react';
import { Typography, Card, List, Button, Tag, Empty, Space } from 'antd';
import { api } from '../services/api';
import type { EvolutionLog } from '../types';

const { Title, Text } = Typography;

export const EvolutionPage: React.FC = () => {
  const [logs, setLogs] = useState<EvolutionLog[]>([]);

  useEffect(() => {
    api.evolution.list().then(setLogs);
  }, []);

  const handleConfirm = async (id: number) => {
    await api.evolution.confirm(id);
    api.evolution.list().then(setLogs);
  };

  const handleRollback = async (id: number) => {
    await api.evolution.rollback(id);
    api.evolution.list().then(setLogs);
  };

  const levelLabels: Record<number, { text: string; color: string }> = {
    1: { text: '观察中', color: 'default' },
    2: { text: '待确认', color: 'orange' },
    3: { text: '已写入', color: 'green' },
  };

  return (
    <div>
      <Title level={4}>进化日志</Title>
      {logs.length === 0 && <Empty description="暂无进化记录" />}
      <List
        dataSource={logs}
        renderItem={(log) => (
          <List.Item
            actions={[
              log.level === 2 && (
                <Button key="confirm" type="primary" size="small" onClick={() => handleConfirm(log.id)}>
                  确认写入
                </Button>
              ),
              log.level === 3 && (
                <Button key="rollback" size="small" danger onClick={() => handleRollback(log.id)}>
                  回滚
                </Button>
              ),
            ].filter(Boolean)}
          >
            <List.Item.Meta
              title={
                <Space>
                  <Tag color={levelLabels[log.level]?.color}>{levelLabels[log.level]?.text}</Tag>
                  <Tag>{log.dimension}</Tag>
                  <Text type="secondary">{log.skill_name}</Text>
                </Space>
              }
              description={log.content}
            />
          </List.Item>
        )}
      />
    </div>
  );
};
