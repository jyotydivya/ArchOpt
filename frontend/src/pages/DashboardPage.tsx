import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import type { Project } from '../types/project.ts';
import { projectsApi } from '../api/projects.ts';
import { Modal } from '../components/common/Modal.tsx';
import { ErrorBanner } from '../components/common/ErrorBanner.tsx';
import { EmptyState } from '../components/common/EmptyState.tsx';
import { mockProject } from '../mocks/mockData.ts';

const STORAGE_KEY = 'archopt_saved_projects';

export const DashboardPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [activeProject, setActiveProject] = useState<Project | null>(null);

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  // Load known project IDs from localStorage and refresh from backend
  useEffect(() => {
    const loadProjects = async () => {
      try {
        const stored = localStorage.getItem(STORAGE_KEY);
        let list: Project[] = stored ? JSON.parse(stored) : [];

        // If list is empty and user is in demo mode or initial state, provide sample project
        const token = localStorage.getItem('archopt_token');
        if (list.length === 0 && token?.includes('mock-demo')) {
          list = [mockProject];
          localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
        }

        // Try to refresh each project from backend GET /api/projects/{id}
        const updatedList: Project[] = [];
        for (const p of list) {
          try {
            const fresh = await projectsApi.getProject(p.id);
            updatedList.push(fresh);
          } catch {
            // Keep existing cached record if offline
            updatedList.push(p);
          }
        }

        setProjects(updatedList);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedList));
      } catch {
        // Fallback
      }
    };

    loadProjects();
  }, []);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('archopt_token');
      let newProj: Project;

      if (token?.includes('mock-demo')) {
        // Demo mode offline creation
        newProj = {
          id: Date.now() % 10000,
          name: name.trim(),
          description: description.trim() || null,
          status: 'DRAFT',
        };
      } else {
        // Call Real API: POST /api/projects
        newProj = await projectsApi.createProject({
          name: name.trim(),
          description: description.trim() || undefined,
        });
      }

      const updated = [newProj, ...projects];
      setProjects(updated);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));

      setIsModalOpen(false);
      setName('');
      setDescription('');

      // Navigate immediately to Stage 1: Requirements
      navigate(`/projects/${newProj.id}/requirements`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create project. Please verify the backend connection.');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeProject || !name.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('archopt_token');
      let updatedProj: Project;

      if (token?.includes('mock-demo')) {
        updatedProj = {
          ...activeProject,
          name: name.trim(),
          description: description.trim() || null,
        };
      } else {
        // Call Real API: PUT /api/projects/{projectId}
        updatedProj = await projectsApi.updateProject(activeProject.id, {
          name: name.trim(),
          description: description.trim() || undefined,
        });
      }

      const updatedList = projects.map((p) => (p.id === updatedProj.id ? updatedProj : p));
      setProjects(updatedList);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedList));

      setIsEditModalOpen(false);
      setActiveProject(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update project.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteProject = async () => {
    if (!activeProject) return;

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('archopt_token');
      if (!token?.includes('mock-demo')) {
        // Call Real API: DELETE /api/projects/{projectId}
        await projectsApi.deleteProject(activeProject.id);
      }

      const updatedList = projects.filter((p) => p.id !== activeProject.id);
      setProjects(updatedList);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedList));

      setIsDeleteModalOpen(false);
      setActiveProject(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete project.');
    } finally {
      setLoading(false);
    }
  };

  const openEditModal = (p: Project) => {
    setActiveProject(p);
    setName(p.name);
    setDescription(p.description || '');
    setIsEditModalOpen(true);
  };

  const openDeleteModal = (p: Project) => {
    setActiveProject(p);
    setIsDeleteModalOpen(true);
  };

  return (
    <div style={{ maxWidth: '1140px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '28px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '6px' }}>Campus Master Plans</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            Create and manage architectural projects, configure zoning criteria, and optimize layouts.
          </p>
        </div>
        <button onClick={() => setIsModalOpen(true)} className="btn btn-primary">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          New Campus Project
        </button>
      </div>

      <ErrorBanner message={error} onDismiss={() => setError(null)} />

      {projects.length === 0 ? (
        <EmptyState
          title="No Campus Projects Yet"
          description="Create your first campus planning project to configure site boundaries, add building inventories, and generate AI layouts."
          actionText="+ Create Campus Project"
          onAction={() => setIsModalOpen(true)}
        />
      ) : (
        <div className="grid-2">
          {projects.map((p) => (
            <div key={p.id} className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                      PROJECT #{p.id}
                    </span>
                    <h3 style={{ fontSize: '1.25rem', marginTop: '2px' }}>{p.name}</h3>
                  </div>
                  <span className={`badge ${p.status === 'SELECTED' ? 'badge-selected' : 'badge-draft'}`}>
                    {p.status}
                  </span>
                </div>

                <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: '20px', minHeight: '42px' }}>
                  {p.description || 'No description provided for this campus project.'}
                </p>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '16px', borderTop: '1px solid var(--border-color)' }}>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    onClick={() => openEditModal(p)}
                    className="btn btn-secondary btn-sm"
                    title="Edit Project Name & Description"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => openDeleteModal(p)}
                    className="btn btn-danger btn-sm"
                    title="Delete Project"
                  >
                    Delete
                  </button>
                </div>

                <Link to={`/projects/${p.id}/requirements`} className="btn btn-primary btn-sm">
                  Open Planner →
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal: Create Project */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setName('');
          setDescription('');
        }}
        title="Create New Campus Project"
        footer={
          <>
            <button
              type="button"
              onClick={() => setIsModalOpen(false)}
              className="btn btn-secondary"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              form="create-project-form"
              className="btn btn-primary"
              disabled={loading || !name.trim()}
            >
              {loading ? 'Creating Project...' : 'Initialize Project'}
            </button>
          </>
        }
      >
        <form id="create-project-form" onSubmit={handleCreateProject}>
          <div className="form-group">
            <label className="form-label" htmlFor="project-name">Project Title *</label>
            <input
              id="project-name"
              type="text"
              className="form-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. VIT South Campus Expansion"
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="project-desc">Description</label>
            <textarea
              id="project-desc"
              className="form-input"
              style={{ minHeight: '80px', resize: 'vertical' }}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Case study for multi-zone academic and residential layout optimization."
            />
          </div>
        </form>
      </Modal>

      {/* Modal: Edit Project */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="Edit Project Details"
        footer={
          <>
            <button
              type="button"
              onClick={() => setIsEditModalOpen(false)}
              className="btn btn-secondary"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              form="edit-project-form"
              className="btn btn-primary"
              disabled={loading || !name.trim()}
            >
              {loading ? 'Saving Changes...' : 'Save Changes'}
            </button>
          </>
        }
      >
        <form id="edit-project-form" onSubmit={handleUpdateProject}>
          <div className="form-group">
            <label className="form-label" htmlFor="edit-project-name">Project Title *</label>
            <input
              id="edit-project-name"
              type="text"
              className="form-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="edit-project-desc">Description</label>
            <textarea
              id="edit-project-desc"
              className="form-input"
              style={{ minHeight: '80px', resize: 'vertical' }}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
        </form>
      </Modal>

      {/* Modal: Delete Project Confirmation */}
      <Modal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        title="Confirm Project Deletion"
        footer={
          <>
            <button
              type="button"
              onClick={() => setIsDeleteModalOpen(false)}
              className="btn btn-secondary"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleDeleteProject}
              className="btn btn-danger"
              disabled={loading}
            >
              {loading ? 'Deleting...' : 'Delete Permanently'}
            </button>
          </>
        }
      >
        <p style={{ color: 'var(--text-muted)' }}>
          Are you sure you want to delete <strong style={{ color: '#ffffff' }}>{activeProject?.name}</strong> (ID: #{activeProject?.id})?
        </p>
        <p style={{ color: 'var(--accent-rose)', fontSize: '0.8125rem', marginTop: '10px' }}>
          This will permanently delete the project along with all associated site requirements, building inventory, constraints, and generated layouts.
        </p>
      </Modal>
    </div>
  );
};
export default DashboardPage;
