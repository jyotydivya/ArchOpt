import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useProject } from '../hooks/useProject.ts';
import { layoutsApi } from '../api/layouts.ts';
import { buildingsApi } from '../api/buildings.ts';
import { ProjectHeader } from '../components/projects/ProjectHeader.tsx';
import { CampusCanvas2D } from '../components/canvas/CampusCanvas2D.tsx';
import { CanvasToolbar } from '../components/canvas/CanvasToolbar.tsx';
import { CanvasLegend } from '../components/canvas/CanvasLegend.tsx';
import { BlueprintModal } from '../components/layouts/BlueprintModal.tsx';
import { Modal } from '../components/common/Modal.tsx';
import { ErrorBanner } from '../components/common/ErrorBanner.tsx';
import { LoadingSpinner } from '../components/common/LoadingSpinner.tsx';
import {
  type ViewportTransform,
  calculateFitTransform,
} from '../utils/coordinates.ts';
import { formatPercent, formatScore } from '../utils/formatters.ts';
import type { LayoutDetail, LayoutSummary } from '../types/layout.ts';
import type { Building } from '../types/building.ts';
import type { Blueprint } from '../types/blueprint.ts';
import {
  mockLayoutsDetail,
  mockLayoutsSummary,
  mockBuildings,
  mockBlueprint,
} from '../mocks/mockData.ts';

export const CampusViewerPage: React.FC = () => {
  const { projectId, layoutId } = useParams<{ projectId: string; layoutId?: string }>();
  const { project, loading: projectLoading, refreshProject } = useProject();
  const navigate = useNavigate();

  const [layoutsList, setLayoutsList] = useState<LayoutSummary[]>([]);
  const [activeLayout, setActiveLayout] = useState<LayoutDetail | null>(null);
  const [buildings, setBuildings] = useState<Building[]>([]);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Canvas Viewport Transform state
  const [transform, setTransform] = useState<ViewportTransform>({
    scale: 1.5,
    offsetX: 60,
    offsetY: 60,
  });

  // Layer Toggles
  const [showGrid, setShowGrid] = useState<boolean>(true);
  const [showLabels, setShowLabels] = useState<boolean>(true);
  const [showLayers, setShowLayers] = useState<boolean>(true);

  // Selection Modal
  const [isSelectModalOpen, setIsSelectModalOpen] = useState<boolean>(false);
  const [selectLoading, setSelectLoading] = useState<boolean>(false);

  // Blueprint Modal
  const [isBlueprintModalOpen, setIsBlueprintModalOpen] = useState<boolean>(false);
  const [blueprintData, setBlueprintData] = useState<Blueprint | null>(null);
  const [blueprintLoading, setBlueprintLoading] = useState<boolean>(false);

  const numProjectId = parseInt(projectId || '1', 10);
  const targetLayoutId = layoutId ? parseInt(layoutId, 10) : null;

  const loadDetail = useCallback(async (id: number) => {
    try {
      const token = localStorage.getItem('archopt_token');
      let detail: LayoutDetail;

      if (token?.includes('mock-demo')) {
        detail = mockLayoutsDetail.find((l) => l.id === id) || mockLayoutsDetail[0];
      } else {
        detail = await layoutsApi.getLayoutDetail(id);
      }

      setActiveLayout(detail);

      // Auto-fit site to canvas
      const fit = calculateFitTransform(detail.site.width, detail.site.height, 900, 620);
      setTransform(fit);
    } catch (err: any) {
      setError(err.response?.data?.detail || `Failed to load details for Layout #${id}`);
    }
  }, []);

  // Load project's generated layouts list and building catalog
  useEffect(() => {
    const initData = async () => {
      setLoading(true);
      setError(null);

      try {
        const token = localStorage.getItem('archopt_token');
        let summaries: LayoutSummary[] = [];
        let bldgs: Building[] = [];

        if (token?.includes('mock-demo')) {
          summaries = mockLayoutsSummary;
          bldgs = mockBuildings;
        } else {
          const [sList, bList] = await Promise.all([
            layoutsApi.getLayouts(numProjectId),
            buildingsApi.getBuildings(numProjectId),
          ]);
          summaries = sList;
          bldgs = bList;
        }

        setLayoutsList(summaries);
        setBuildings(bldgs);

        // Determine which layout to load
        const chosenId = targetLayoutId || (summaries[0]?.id ?? null);
        if (chosenId) {
          await loadDetail(chosenId);
        }
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to initialize 2D viewer.');
      } finally {
        setLoading(false);
      }
    };

    initData();
  }, [numProjectId, targetLayoutId, loadDetail]);

  const handleSwitchLayout = (id: number) => {
    navigate(`/projects/${numProjectId}/viewer/${id}`);
  };

  const handleFit = () => {
    if (!activeLayout) return;
    const fit = calculateFitTransform(activeLayout.site.width, activeLayout.site.height, 900, 620);
    setTransform(fit);
  };

  const handleReset = () => {
    setTransform({ scale: 1.5, offsetX: 60, offsetY: 60 });
  };

  const handleZoomIn = () => {
    setTransform((prev) => ({ ...prev, scale: Math.min(10, prev.scale * 1.25) }));
  };

  const handleZoomOut = () => {
    setTransform((prev) => ({ ...prev, scale: Math.max(0.2, prev.scale * 0.8) }));
  };

  // Winning Plan Selection Action
  const handleSelectWinningPlan = async () => {
    if (!activeLayout) return;
    setSelectLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('archopt_token');
      if (!token?.includes('mock-demo')) {
        await layoutsApi.selectLayout(activeLayout.id);
      }
      await refreshProject();
      setSuccess(`Layout #${activeLayout.id} selected as the official campus plan!`);
      setIsSelectModalOpen(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to select winning layout.');
    } finally {
      setSelectLoading(false);
    }
  };

  // Blueprint Export Action
  const handleOpenBlueprint = async () => {
    if (!activeLayout) return;
    setIsBlueprintModalOpen(true);
    setBlueprintLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('archopt_token');
      let bp: Blueprint;

      if (token?.includes('mock-demo')) {
        bp = { ...mockBlueprint, layoutId: activeLayout.id };
      } else {
        bp = await layoutsApi.getBlueprint(activeLayout.id);
      }

      setBlueprintData(bp);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch 3D Blender Blueprint.');
    } finally {
      setBlueprintLoading(false);
    }
  };

  if (projectLoading || loading) {
    return <LoadingSpinner message="Loading 2D campus spatial planner..." />;
  }

  if (!activeLayout) {
    return (
      <div style={{ maxWidth: '1000px', margin: '0 auto', textAlign: 'center', padding: '60px 20px' }}>
        <h2>No Layouts Available</h2>
        <p style={{ color: 'var(--text-muted)', margin: '12px 0 24px' }}>
          You must generate campus plans before inspecting them in the 2D viewer.
        </p>
        <Link to={`/projects/${numProjectId}/generate`} className="btn btn-primary">
          Generate Campus Plans →
        </Link>
      </div>
    );
  }

  const m = activeLayout.metrics;

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
      <ProjectHeader project={project} activeStepTitle="6. Interactive 2D Campus Spatial Viewer">
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={() => setIsSelectModalOpen(true)}
            className="btn btn-accent btn-sm"
          >
            ✓ Select as Winning Plan
          </button>
          <button
            onClick={handleOpenBlueprint}
            className="btn btn-primary btn-sm"
          >
            Export Blueprint (JSON)
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

      {/* Plan Switcher Bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: 'var(--bg-card)',
          padding: '12px 18px',
          borderRadius: 'var(--radius-lg) var(--radius-lg) 0 0',
          border: '1px solid var(--border-color)',
          borderBottom: 'none',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-muted)' }}>
            Switch Layout:
          </span>
          <div style={{ display: 'flex', gap: '6px' }}>
            {layoutsList.map((l) => (
              <button
                key={l.id}
                onClick={() => handleSwitchLayout(l.id)}
                className={`btn btn-sm ${activeLayout.id === l.id ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '4px 10px', fontSize: '0.75rem' }}
              >
                #{l.rank} (Plan {l.id})
              </button>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '0.8125rem', color: 'var(--text-dim)' }}>
            Site: {activeLayout.site.width}m × {activeLayout.site.height}m
          </span>
          <span className={`badge ${activeLayout.feasible ? 'badge-feasible' : 'badge-infeasible'}`}>
            {activeLayout.feasible ? 'Feasible Plan' : 'Constraint Violations'}
          </span>
        </div>
      </div>

      {/* Metrics Strip */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(6, 1fr)',
          backgroundColor: '#0b1329',
          borderLeft: '1px solid var(--border-color)',
          borderRight: '1px solid var(--border-color)',
          borderBottom: '1px solid var(--border-color)',
          padding: '10px 16px',
          gap: '12px',
          fontSize: '0.75rem',
        }}
      >
        <div>
          <span style={{ color: 'var(--text-dim)' }}>Land Utilization:</span>{' '}
          <strong style={{ color: 'var(--accent-cyan)' }}>{formatPercent(m.landUtilization)}</strong>
        </div>
        <div>
          <span style={{ color: 'var(--text-dim)' }}>Green Space:</span>{' '}
          <strong style={{ color: 'var(--accent-emerald)' }}>{formatPercent(m.greenRatio)}</strong>
        </div>
        <div>
          <span style={{ color: 'var(--text-dim)' }}>Parking Ratio:</span>{' '}
          <strong style={{ color: 'var(--text-main)' }}>{formatPercent(m.parkingRatio)}</strong>
        </div>
        <div>
          <span style={{ color: 'var(--text-dim)' }}>Pedestrian Access:</span>{' '}
          <strong style={{ color: 'var(--accent-cyan)' }}>{formatScore(m.accessibilityScore)}</strong>
        </div>
        <div>
          <span style={{ color: 'var(--text-dim)' }}>Road Circulation:</span>{' '}
          <strong style={{ color: 'var(--accent-cyan)' }}>{formatScore(m.roadEfficiency)}</strong>
        </div>
        <div>
          <span style={{ color: 'var(--text-dim)' }}>Constraint Score:</span>{' '}
          <strong style={{ color: m.constraintScore >= 1 ? 'var(--accent-emerald)' : 'var(--accent-rose)' }}>
            {formatPercent(m.constraintScore)}
          </strong>
        </div>
      </div>

      {/* 2D Canvas Viewer Container */}
      <div
        style={{
          border: '1px solid var(--border-color)',
          borderTop: 'none',
          borderRadius: '0 0 var(--radius-lg) var(--radius-lg)',
          overflow: 'hidden',
          boxShadow: 'var(--shadow-lg)',
          marginBottom: '24px',
        }}
      >
        <CanvasToolbar
          onZoomIn={handleZoomIn}
          onZoomOut={handleZoomOut}
          onFit={handleFit}
          onReset={handleReset}
          showGrid={showGrid}
          setShowGrid={setShowGrid}
          showLabels={showLabels}
          setShowLabels={setShowLabels}
          showLayers={showLayers}
          setShowLayers={setShowLayers}
        />

        <CampusCanvas2D
          layout={activeLayout}
          buildings={buildings}
          showGrid={showGrid}
          showLabels={showLabels}
          showLayers={showLayers}
          transform={transform}
          setTransform={setTransform}
        />

        <CanvasLegend />
      </div>

      {/* Bottom Navigation */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Link to={`/projects/${numProjectId}/compare`} className="btn btn-secondary">
          ← Back to Plan Comparison
        </Link>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button onClick={handleOpenBlueprint} className="btn btn-secondary">
            View Contract 9 Blueprint
          </button>
          <button onClick={() => setIsSelectModalOpen(true)} className="btn btn-primary">
            Confirm Selection
          </button>
        </div>
      </div>

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
              onClick={handleSelectWinningPlan}
              className="btn btn-accent"
              disabled={selectLoading}
            >
              {selectLoading ? 'Saving Selection...' : 'Confirm Plan Selection'}
            </button>
          </>
        }
      >
        <p style={{ color: 'var(--text-main)', marginBottom: '12px' }}>
          Select <strong>Layout #{activeLayout.id} (Rank #{activeLayout.rank})</strong> as the final winning master plan for project #{numProjectId}?
        </p>
        <div style={{ padding: '12px', backgroundColor: '#0b1329', borderRadius: 'var(--radius-md)', fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
          <p>• Triggers <code>POST /api/layouts/{activeLayout.id}/select</code>.</p>
          <p style={{ marginTop: '6px' }}>• Marks project status as <strong style={{ color: 'var(--accent-emerald)' }}>SELECTED</strong>.</p>
          <p style={{ marginTop: '6px' }}>• Person 6 will consume this plan's blueprint for Blender 3D procedural generation.</p>
        </div>
      </Modal>

      {/* Blueprint Export Modal */}
      <BlueprintModal
        isOpen={isBlueprintModalOpen}
        onClose={() => setIsBlueprintModalOpen(false)}
        blueprint={blueprintData}
        loading={blueprintLoading}
      />
    </div>
  );
};
export default CampusViewerPage;
