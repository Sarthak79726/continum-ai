import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Layout, PageLoadingFallback } from './components/layout/Layout';

// Lazy-loaded Pages for Route-Level Code Splitting
const LoginPage = lazy(() => import('./pages/LoginPage').then(m => ({ default: m.LoginPage })));
const DashboardPage = lazy(() => import('./pages/DashboardPage').then(m => ({ default: m.DashboardPage })));
const ProjectsPage = lazy(() => import('./pages/ProjectsPage').then(m => ({ default: m.ProjectsPage })));
const ProjectDetailPage = lazy(() => import('./pages/ProjectDetailPage').then(m => ({ default: m.ProjectDetailPage })));
const DocumentsPage = lazy(() => import('./pages/DocumentsPage').then(m => ({ default: m.DocumentsPage })));
const KnowledgeGraphPage = lazy(() => import('./pages/KnowledgeGraphPage').then(m => ({ default: m.KnowledgeGraphPage })));
const EvidencePassportPage = lazy(() => import('./pages/EvidencePassportPage').then(m => ({ default: m.EvidencePassportPage })));
const ContinuityBlueprintPage = lazy(() => import('./pages/ContinuityBlueprintPage').then(m => ({ default: m.ContinuityBlueprintPage })));
const HandoverReportsPage = lazy(() => import('./pages/HandoverReportsPage').then(m => ({ default: m.HandoverReportsPage })));
const ReviewCentrePage = lazy(() => import('./pages/ReviewCentrePage').then(m => ({ default: m.ReviewCentrePage })));
const TeamPage = lazy(() => import('./pages/TeamPage').then(m => ({ default: m.TeamPage })));
const SettingsPage = lazy(() => import('./pages/SettingsPage').then(m => ({ default: m.SettingsPage })));
const EmployeePassportPage = lazy(() => import('./pages/EmployeePassportPage').then(m => ({ default: m.EmployeePassportPage })));
const IncomingWorkspacePage = lazy(() => import('./pages/IncomingWorkspacePage').then(m => ({ default: m.IncomingWorkspacePage })));
const AskProjectAIPage = lazy(() => import('./pages/AskProjectAIPage').then(m => ({ default: m.AskProjectAIPage })));
const SourceIntegrationsPage = lazy(() => import('./pages/SourceIntegrationsPage').then(m => ({ default: m.SourceIntegrationsPage })));
const ConflictsPage = lazy(() => import('./pages/ConflictsPage').then(m => ({ default: m.ConflictsPage })));

// Protected Route Wrapper
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-xs text-teal-400 font-mono animate-pulse">
          Authenticating session...
        </div>
      </div>
    );
  }

  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Suspense fallback={<PageLoadingFallback />}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />

            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<DashboardPage />} />
              <Route path="projects" element={<ProjectsPage />} />
              <Route path="projects/:id" element={<ProjectDetailPage />} />
              <Route path="documents" element={<DocumentsPage />} />
              <Route path="sources" element={<SourceIntegrationsPage />} />
              <Route path="employees" element={<EmployeePassportPage />} />
              <Route path="incoming-workspace" element={<IncomingWorkspacePage />} />
              <Route path="ask-ai" element={<AskProjectAIPage />} />
              <Route path="conflicts" element={<ConflictsPage />} />
              <Route path="graph" element={<KnowledgeGraphPage />} />
              <Route path="evidence" element={<EvidencePassportPage />} />
              <Route path="tasks" element={<ContinuityBlueprintPage />} />
              <Route path="handovers" element={<HandoverReportsPage />} />
              <Route path="reviews" element={<ReviewCentrePage />} />
              <Route path="team" element={<TeamPage />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
