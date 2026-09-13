import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useProject } from '../hooks/useProject.ts';
import { constraintsApi } from '../api/constraints.ts';
import { buildingsApi } from '../api/buildings.ts';
import { ProjectHeader } from '../components/projects/ProjectHeader.tsx';
import { ConstraintList } from '../components/constraints/ConstraintList.tsx';
import { ConstraintForm } from '../components/constraints/ConstraintForm.tsx';
import { Modal } from '../components/common/Modal.tsx';
import { ErrorBanner } from '../components/common/ErrorBanner.tsx';
import { LoadingSpinner } from '../components/common/LoadingSpinner.tsx';
import type { Constraint, ConstraintCreateRequest } from '../types/constraint.ts';
import type { Building } from '../types/building.ts';
import { mockConstraints, mockBuildings } from '../mocks/mockData.ts';

export const ConstraintsPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const { project, loading: projectLoading } = useProject();
  const navigate = useNavigate();

  const [constraints, setConstraints] = useState<Constraint[]>([]);
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [modalLoading, setModalLoading] = useState<boolean>(false);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const numProjectId = parseInt(projectId || '1', 10);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('archopt_token');
      if (token?.includes('mock-demo')) {
        setBuildings(mockBuildings);
        setConstraints(mockConstraints);
      } else {
        const [bList, cList] = await Promise.all([
          buildingsApi.getBuildings(numProjectId),
          constraintsApi.getConstraints(numProjectId),
        ]);
        setBuildings(bList);
        setConstraints(cList);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch constraints.');
    } finally {
      setLoading(false);
    }
  }, [numProjectId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleAddConstraint = async (data: ConstraintCreateRequest) => {
    setModalLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('archopt_token');
      let created: Constraint;

      if (token?.includes('mock-demo')) {
        created = {
          id: constraints.length + 1,
          ...data,
        };
      } else {
        created = await constraintsApi.createConstraint(numProjectId, data);
      }

      setConstraints([...constraints, created]);
      setSuccess(`Spatial constraint "${created.type}" added successfully.`);
      setIsModalOpen(false);
    } catch (err: any) {
      throw err;
    } finally {
      setModalLoading(false);
    }
  };

  if (projectLoading || (loading && buildings.length === 0)) {
    return <LoadingSpinner message="Loading spatial constraints..." />;
  }

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
      <ProjectHeader project={project} activeStepTitle="3. Spatial & Relational Constraints">
        <button
          onClick={() => setIsModalOpen(true)}
          className="btn btn-primary"
          disabled={buildings.length < 2}
          title={buildings.length < 2 ? 'At least 2 buildings are required to define relational constraints' : 'Add Constraint'}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          Add Spatial Constraint
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

      {buildings.length < 2 && (
        <div className="alert alert-info">
          <span>You currently have {buildings.length} building configured. At least 2 buildings are recommended to configure relational distance constraints between them.</span>
        </div>
      )}

      {/* Constraints List Card */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <h3 className="card-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
            </svg>
            Active Campus Constraints ({constraints.length})
          </h3>
          <span style={{ fontSize: '0.8125rem', color: 'var(--text-dim)' }}>
            Used by Person 3 NSGA-II Multi-Objective Optimizer
          </span>
        </div>

        <ConstraintList
          constraints={constraints}
          buildings={buildings}
          onAddClick={() => setIsModalOpen(true)}
        />
      </div>

      {/* Bottom Navigation */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Link to={`/projects/${numProjectId}/buildings`} className="btn btn-secondary">
          ← Back to Buildings
        </Link>

        <button
          onClick={() => navigate(`/projects/${numProjectId}/generate`)}
          className="btn btn-primary"
        >
          Next: Generate Plans →
        </button>
      </div>

      {/* Modal: Add Constraint */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Add Spatial / Relational Constraint"
        maxWidth="600px"
      >
        <ConstraintForm
          buildings={buildings}
          onSubmit={handleAddConstraint}
          onCancel={() => setIsModalOpen(false)}
          loading={modalLoading}
        />
      </Modal>
    </div>
  );
};
export default ConstraintsPage;
