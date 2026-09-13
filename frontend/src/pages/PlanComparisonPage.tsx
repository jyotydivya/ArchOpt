import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useProject } from '../hooks/useProject.ts';
import { layoutsApi } from '../api/layouts.ts';
import { ProjectHeader } from '../components/projects/ProjectHeader.tsx';
import { LayoutCard } from '../components/layouts/LayoutCard.tsx';
import { MetricsTable } from '../components/layouts/MetricsTable.tsx';
import { Modal } from '../components/common/Modal.tsx';
import { ErrorBanner } from '../components/common/ErrorBanner.tsx';
import { EmptyState } from '../components/common/EmptyState.tsx';
import { LoadingSpinner } from '../components/common/LoadingSpinner.tsx';
import type { LayoutSummary } from '../types/layout.ts';
import { mockLayoutsSummary } from '../mocks/mockData.ts';

export const PlanComparisonPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const { project, loading: projectLoading, refreshProject } = useProject();
  const navigate = useNavigate();

  const [layouts, setLayouts] = useState<LayoutSummary[]>([]);
  const [viewMode, setViewMode] = useState<'cards' | 'table'>('cards');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Selection Modal state
  const [isSelectModalOpen, setIsSelectModalOpen] = useState<boolean>(false);
  const [selectedCandidateId, setSelectedCandidateId] = useState<number | null>(null);
  const [selectLoading, setSelectLoading] = useState<boolean>(false);

  const numProjectId = parseInt(projectId || '1', 10);

  const loadLayouts = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('archopt_token');
      if (token?.includes('mock-demo')) {
        setLayouts(mockLayoutsSummary);
      } else {
        const list = await layoutsApi.getLayouts(numProjectId);
        setLayouts(list);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch generated layouts.');
    } finally {
      setLoading(false);
    }
  }, [numProjectId]);

  useEffect(() => {
    loadLayouts();
  }, [loadLayouts]);

  const handleOpenSelectModal = (layoutId: number) => {
    setSelectedCandidateId(layoutId);
    setIsSelectModalOpen(true);
  };

  const handleConfirmSelect = async () => {
    if (!selectedCandidateId) return;

    setSelectLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('archopt_token');
      if (!token?.includes('mock-demo')) {
        // Call Real API: POST /api/layouts/{layoutId}/select
        await layoutsApi.selectLayout(selectedCandidateId);
      }

      await refreshProject();
      setSuccess(`Layout #${selectedCandidateId} successfully confirmed as the official winning campus plan!`);
      setIsSelectModalOpen(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to select winning plan.');
    } finally {
      setSelectLoading(false);
    }
  };

  if (projectLoading || (loading && layouts.length === 0)) {
    return <LoadingSpinner message="Loading generated Pareto layouts..." />;
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <ProjectHeader project={project} activeStepTitle="5. Pareto Layout Evaluation & Comparison">
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={() => setViewMode('cards')}
            className={`btn btn-sm ${viewMode === 'cards' ? 'btn-primary' : 'btn-secondary'}`}
            title="Card View"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="7" height="7" />
              <rect x="14" y="3" width="7" height="7" />
              <rect x="14" y="14" width="7" height="7" />
              <rect x="3" y="14" width="7" height="7" />
            </svg>
            Cards
          </button>
          <button
            onClick={() => setViewMode('table')}
            className={`btn btn-sm ${viewMode === 'table' ? 'btn-primary' : 'btn-secondary'}`}
            title="Table View"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="8" y1="6" x2="21" y2="6" />
              <line x1="8" y1="12" x2="21" y2="12" />
              <line x1="8" y1="18" x2="21" y2="18" />
              <line x1="3" y1="6" x2="3.01" y2="6" />
              <line x1="3" y1="12" x2="3.01" y2="12" />
              <line x1="3" y1="18" x2="3.01" y2="18" />
            </svg>
            Table
          </button>
        </div>
      </ProjectHeader>

      <ErrorBanner message={error} onDismiss={() => setError(null)} />

      {success && (
        <div className="alert alert-success" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>{success}</span>
          <button onClick={() => setSuccess(null)} style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }}>✕</button>
        </div>
      )}

      {layouts.length === 0 ? (
        <EmptyState
          title="No Layouts Generated Yet"
          description="Execute the GNN Candidate Generation and NSGA-II Multi-Objective Optimization pipeline to produce ranked campus layouts."
          actionText="⚡ Go to Generate Plans"
          onAction={() => navigate(`/projects/${numProjectId}/generate`)}
        />
      ) : (
        <>
          {viewMode === 'cards' ? (
            <div className="grid-3" style={{ marginBottom: '28px' }}>
              {layouts.map((l) => (
                <LayoutCard
                  key={l.id}
                  layout={l}
                  onInspect={() => navigate(`/projects/${numProjectId}/viewer/${l.id}`)}
                  onSelect={() => handleOpenSelectModal(l.id)}
                />
              ))}
            </div>
          ) : (
            <div className="card" style={{ marginBottom: '28px' }}>
              <MetricsTable
                layouts={layouts}
                onInspect={(layoutId) => navigate(`/projects/${numProjectId}/viewer/${layoutId}`)}
                onSelect={(layoutId) => handleOpenSelectModal(layoutId)}
              />
            </div>
          )}

          {/* Bottom Navigation */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Link to={`/projects/${numProjectId}/generate`} className="btn btn-secondary">
              ← Back to Generation
            </Link>

            <button
              onClick={() => navigate(`/projects/${numProjectId}/viewer/${layouts[0]?.id || ''}`)}
              className="btn btn-primary"
            >
              Open 2D Campus Viewer →
            </button>
          </div>
        </>
      )}

      {/* Confirmation Modal for Winning Plan Selection */}
      <Modal
        isOpen={isSelectModalOpen}
        onClose={() => setIsSelectModalOpen(false)}
        title="Confirm Winning Campus Plan Selection"
        footer={
          <>
            <button
              type="button"
              onClick={() => setIsSelectModalOpen(false)}
              className="btn btn-secondary"
              disabled={selectLoading}
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleConfirmSelect}
              className="btn btn-accent"
              disabled={selectLoading}
            >
              {selectLoading ? 'Confirming...' : 'Confirm Selection'}
            </button>
          </>
        }
      >
        <p style={{ color: 'var(--text-main)', marginBottom: '12px' }}>
          Are you sure you want to select <strong>Layout #{selectedCandidateId}</strong> as the official winning campus plan for this project?
        </p>
        <div style={{ padding: '12px', backgroundColor: '#0b1329', borderRadius: 'var(--radius-md)', fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
          <p>• Updates project status to <strong style={{ color: 'var(--accent-emerald)' }}>SELECTED</strong> (Contract Section 3.16).</p>
          <p style={{ marginTop: '6px' }}>• Freezes the blueprint coordinates for Person 6 procedural Blender 3D extrusion.</p>
        </div>
      </Modal>
    </div>
  );
};
export default PlanComparisonPage;
