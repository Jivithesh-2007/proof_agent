import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';

// ProofAI Components & Pages
import { Layout as ProofAILayout } from './components/layout/Layout';
import { DashboardPage } from './pages/DashboardPage';
import { DataSourcesPage } from './pages/DataSourcesPage';
import { AnalysisWorkspacePage } from './pages/AnalysisWorkspacePage';
import { AnalysisResultPage } from './pages/AnalysisResultPage';
import { EvidencePage } from './pages/EvidencePage';
import { AnalysisRunsPage } from './pages/AnalysisRunsPage';
import { SettingsPage as ProofAISettingsPage } from './pages/SettingsPage';

// CaseLens AI Components & Pages
import { LandingPage } from './pages/caselens/LandingPage';
import { CaseLensLayout } from './components/caselens/CaseLensLayout';
import { OverviewPage } from './pages/caselens/OverviewPage';
import { DocumentsPage } from './pages/caselens/DocumentsPage';
import { AskCaseLensPage } from './pages/caselens/AskCaseLensPage';
import { CaseAnalysisPage } from './pages/caselens/CaseAnalysisPage';
import { ContradictionsPage } from './pages/caselens/ContradictionsPage';
import { DocumentComparisonPage } from './pages/caselens/DocumentComparisonPage';
import { MissingInfoPage } from './pages/caselens/MissingInfoPage';
import { ReportsPage } from './pages/caselens/ReportsPage';
import { ActivityPage } from './pages/caselens/ActivityPage';
import { SettingsPage as CaseLensSettingsPage } from './pages/caselens/SettingsPage';

export const App: React.FC = () => {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Landing Page */}
          <Route path="/" element={<LandingPage />} />

          {/* CaseLens AI Document Intelligence Workspace */}
          <Route path="/caselens" element={<CaseLensLayout />}>
            <Route index element={<Navigate to="/caselens/overview" replace />} />
            <Route path="overview" element={<OverviewPage />} />
            <Route path="documents" element={<DocumentsPage />} />
            <Route path="ask" element={<AskCaseLensPage />} />
            <Route path="analysis" element={<CaseAnalysisPage />} />
            <Route path="contradictions" element={<ContradictionsPage />} />
            <Route path="compare" element={<DocumentComparisonPage />} />
            <Route path="missing-info" element={<MissingInfoPage />} />
            <Route path="reports" element={<ReportsPage />} />
            <Route path="activity" element={<ActivityPage />} />
            <Route path="settings" element={<CaseLensSettingsPage />} />
            <Route path="*" element={<Navigate to="/caselens/overview" replace />} />
          </Route>

          {/* ProofAI Data Analytics Platform (Preserved) */}
          <Route path="/dashboard" element={<ProofAILayout><DashboardPage /></ProofAILayout>} />
          <Route path="/data" element={<ProofAILayout><DataSourcesPage /></ProofAILayout>} />
          <Route path="/analysis" element={<ProofAILayout><AnalysisWorkspacePage /></ProofAILayout>} />
          <Route path="/analysis/:id" element={<ProofAILayout><AnalysisResultPage /></ProofAILayout>} />
          <Route path="/evidence" element={<ProofAILayout><EvidencePage /></ProofAILayout>} />
          <Route path="/runs" element={<ProofAILayout><AnalysisRunsPage /></ProofAILayout>} />
          <Route path="/settings" element={<ProofAILayout><ProofAISettingsPage /></ProofAILayout>} />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
};

export default App;
