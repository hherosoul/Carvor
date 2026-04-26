import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { AppShell } from './components/AppShell';
import { TimelinePage } from './pages/TimelinePage';
import { WeekDetailPage } from './pages/WeekDetailPage';
import { WeeklyReportPage } from './pages/WeeklyReportPage';
import { IdeasPage } from './pages/IdeasPage';
import { IdeaDetailPage } from './pages/IdeaDetailPage';
import { TaskDetailPage } from './pages/TaskDetailPage';
import { EvolutionPage } from './pages/EvolutionPage';
import { OperationLogsPage } from './pages/OperationLogsPage';
import { SettingsPage } from './pages/SettingsPage';
import { PaperLibraryPage } from './pages/PaperLibraryPage';
import { NotesPage } from './pages/NotesPage';

const App: React.FC = () => {
  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Routes>
          <Route element={<AppShell />}>
            <Route path="/" element={<TimelinePage />} />
            <Route path="/week/:date" element={<WeekDetailPage />} />
            <Route path="/weekly-report" element={<WeeklyReportPage />} />
            <Route path="/papers" element={<PaperLibraryPage />} />
            <Route path="/notes" element={<NotesPage />} />
            <Route path="/ideas" element={<IdeasPage />} />
            <Route path="/ideas/:id" element={<IdeaDetailPage />} />
            <Route path="/tasks/:id" element={<TaskDetailPage />} />
            <Route path="/evolution" element={<EvolutionPage />} />
            <Route path="/operation-logs" element={<OperationLogsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
};

export default App;
