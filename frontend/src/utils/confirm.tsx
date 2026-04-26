import { Modal, message } from 'antd';
import { ExclamationCircleFilled } from '@ant-design/icons';

export function confirmDelete(title: string, onOk: () => void | Promise<void>) {
  Modal.confirm({
    title,
    icon: <ExclamationCircleFilled />,
    content: '删除后不可恢复，请确认操作',
    okText: '确认删除',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try {
        await onOk();
      } catch (err: any) {
        message.error(`操作失败：${err.message || '未知错误'}`);
      }
    },
    centered: true,
  });
}

export function confirmAction(title: string, content: string, onOk: () => void | Promise<void>, okText = '确认') {
  Modal.confirm({
    title,
    icon: <ExclamationCircleFilled />,
    content,
    okText,
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try {
        await onOk();
      } catch (err: any) {
        message.error(`操作失败：${err.message || '未知错误'}`);
      }
    },
    centered: true,
  });
}
