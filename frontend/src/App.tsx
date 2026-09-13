import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext.tsx';
import { ProtectedRoute } from './components/common/ProtectedRoute.tsx';
import { LayoutWrapper } from './components/common/LayoutWrapper.tsx';

// Pages
import { LoginPage } from './pages/LoginPage.tsx';
import { RegisterPage } from './pages/RegisterPage.tsx';
import { DashboardPage } from './pages/DashboardPage.tsx';
import { RequirementsPage } from './pages/RequirementsPage.tsx';
import { BuildingsPage } from './pages/BuildingsPage.tsx';
import { ConstraintsPage } from './pages/ConstraintsPage.tsx';
import { GeneratePlansPage } from './pages/GeneratePlansPage.tsx';
import { PlanComparisonPage } from './pages/PlanComparisonPage.tsx';
import { CampusViewerPage } from './pages/CampusViewerPage.tsx';
import { NotFoundPage } from './pages/NotFoundPage.tsx';

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Protected Planning Routes */}
          <Route
            element={
              <ProtectedRoute>
                <LayoutWrapper />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<Navigate to="/projects" replace />} />
            <Route path="/projects" element={<DashboardPage />} />
            <Route path="/projects/:projectId/requirements" element={<RequirementsPage />} />
            <Route path="/projects/:projectId/buildings" element={<BuildingsPage />} />
            <Route path="/projects/:projectId/constraints" element={<ConstraintsPage />} />
            <Route path="/projects/:projectId/generate" element={<GeneratePlansPage />} />
            <Route path="/projects/:projectId/compare" element={<PlanComparisonPage />} />
            <Route path="/projects/:projectId/viewer" element={<CampusViewerPage />} />
            <Route path="/projects/:projectId/viewer/:layoutId" element={<CampusViewerPage />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
