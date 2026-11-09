import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Layout } from './components/layout/Layout';

// Pages
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { ProjectsPage } from './pages/ProjectsPage';
import { ProjectDetailPage } from './pages/ProjectDetailPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { KnowledgeGraphPage } from './pages/KnowledgeGraphPage';
import { EvidencePassportPage } from './pages/EvidencePassportPage';
import { ContinuityBlueprintPage } from './pages/ContinuityBlueprintPage';
import { HandoverReportsPage } from './pages/HandoverReportsPage';
import { ReviewCentrePage } from './pages/ReviewCentrePage';
import { TeamPage } from './pages/TeamPage';
import { SettingsPage } from './pages/SettingsPage';

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
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
