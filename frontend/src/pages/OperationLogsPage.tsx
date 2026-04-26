import React, { useEffect, useState } from 'react';
import { Typography, Table } from 'antd';
import { api } from '../services/api';

const { Title } = Typography;

export const OperationLogsPage: React.FC = () => {
  const [logs, setLogs] = useState<unknown[]>([]);

  useEffect(() => {
    api.operationLogs.list().then(setLogs);
  }, []);

  const columns = [
    { title: '类型', dataIndex: 'operation_type', key: 'operation_type' },
    { title: '对象', dataIndex: 'operation_object', key: 'operation_object' },
    { title: '结果', dataIndex: 'result', key: 'result', ellipsis: true },
    { title: '时间', dataIndex: 'timestamp', key: 'timestamp' },
  ];

  return (
    <div>
      <Title level={4}>操作日志</Title>
      <Table dataSource={logs} columns={columns} rowKey="id" size="small" />
    </div>
  );
};
