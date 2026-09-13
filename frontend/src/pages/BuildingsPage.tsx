import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useProject } from '../hooks/useProject.ts';
import { buildingsApi } from '../api/buildings.ts';
import { ProjectHeader } from '../components/projects/ProjectHeader.tsx';
import { BuildingTable } from '../components/buildings/BuildingTable.tsx';
import { BuildingForm } from '../components/buildings/BuildingForm.tsx';
import { Modal } from '../components/common/Modal.tsx';
import { ErrorBanner } from '../components/common/ErrorBanner.tsx';
import { LoadingSpinner } from '../components/common/LoadingSpinner.tsx';
import type { Building, BuildingCreateRequest } from '../types/building.ts';
import { mockBuildings } from '../mocks/mockData.ts';

export const BuildingsPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const { project, loading: projectLoading } = useProject();
  const navigate = useNavigate();

  const [buildings, setBuildings] = useState<Building[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [modalLoading, setModalLoading] = useState<boolean>(false);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const numProjectId = parseInt(projectId || '1', 10);

  const loadBuildings = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('archopt_token');
      if (token?.includes('mock-demo')) {
        setBuildings(mockBuildings);
      } else {
        const list = await buildingsApi.getBuildings(numProjectId);
        setBuildings(list);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch project buildings.');
    } finally {
      setLoading(false);
    }
  }, [numProjectId]);

  useEffect(() => {
    loadBuildings();
  }, [loadBuildings]);

  const handleAddBuilding = async (data: BuildingCreateRequest) => {
    setModalLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('archopt_token');
      let created: Building;

      if (token?.includes('mock-demo')) {
        created = {
          id: buildings.length + 1,
          projectId: numProjectId,
          ...data,
        };
      } else {
        created = await buildingsApi.createBuilding(numProjectId, data);
      }

      setBuildings([...buildings, created]);
      setSuccess(`Building "${created.name}" added to inventory.`);
      setIsModalOpen(false);
    } catch (err: any) {
      throw err; // Re-thrown for BuildingForm to display inline error
    } finally {
      setModalLoading(false);
    }
  };

  const totalFootprint = buildings.reduce((sum, b) => sum + (b.width * b.depth * b.requiredCount), 0);
  const totalFloorArea = buildings.reduce((sum, b) => sum + (b.width * b.depth * b.floorCount * b.requiredCount), 0);
  const totalBuildingUnits = buildings.reduce((sum, b) => sum + b.requiredCount, 0);

  if (projectLoading || (loading && buildings.length === 0)) {
    return <LoadingSpinner message="Loading campus building inventory..." />;
  }

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
      <ProjectHeader project={project} activeStepTitle="2. Campus Building Inventory & Massing">
        <button onClick={() => setIsModalOpen(true)} className="btn btn-primary">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          Add Building Spec
        </button>
      </ProjectHeader>

      <ErrorBanner message={error} onDismiss={() => setError(null)} />

      {success && (
        <div className="alert alert-success" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>{success}</span>
          <button
            onClick={() => setSuccess(null)}
            style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Stats Summary Cards */}
      <div className="grid-3" style={{ marginBottom: '24px' }}>
        <div className="card" style={{ padding: '16px' }}>
          <div style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>Configured Buildings</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-main)', marginTop: '4px' }}>
            {buildings.length} <span style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-dim)' }}>types ({totalBuildingUnits} total units)</span>
          </div>
        </div>

        <div className="card" style={{ padding: '16px' }}>
          <div style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>Total Ground Footprint</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--accent-cyan)', marginTop: '4px' }}>
            {totalFootprint.toLocaleString()} <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>m²</span>
          </div>
        </div>

        <div className="card" style={{ padding: '16px' }}>
          <div style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>Gross Floor Area (GFA)</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--accent-emerald)', marginTop: '4px' }}>
            {totalFloorArea.toLocaleString()} <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>m²</span>
          </div>
        </div>
      </div>

      {/* Buildings Table */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <h3 className="card-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18" />
              <path d="M6 12H4a2 2 0 0 0-2 2v8" />
              <path d="M18 16h2a2 2 0 0 1 2 2v4" />
            </svg>
            Campus Building Specifications
          </h3>
          <span style={{ fontSize: '0.8125rem', color: 'var(--text-dim)' }}>
            Must have at least 1 building to generate plans
          </span>
        </div>

        <BuildingTable buildings={buildings} onAddClick={() => setIsModalOpen(true)} />
      </div>

      {/* Bottom Navigation */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Link to={`/projects/${numProjectId}/requirements`} className="btn btn-secondary">
          ← Back to Site Requirements
        </Link>

        <button
          onClick={() => navigate(`/projects/${numProjectId}/constraints`)}
          className="btn btn-primary"
          disabled={buildings.length === 0}
          title={buildings.length === 0 ? 'Add at least one building to continue' : 'Proceed to Constraints'}
        >
          Next: Configure Constraints →
        </button>
      </div>

      {/* Add Building Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Add Building Specification"
        maxWidth="620px"
      >
        <BuildingForm
          onSubmit={handleAddBuilding}
          onCancel={() => setIsModalOpen(false)}
          loading={modalLoading}
        />
      </Modal>
    </div>
  );
};
export default BuildingsPage;
