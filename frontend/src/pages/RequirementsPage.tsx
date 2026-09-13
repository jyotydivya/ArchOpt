import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useProject } from '../hooks/useProject.ts';
import { requirementsApi } from '../api/requirements.ts';
import { ProjectHeader } from '../components/projects/ProjectHeader.tsx';
import { ErrorBanner } from '../components/common/ErrorBanner.tsx';
import { LoadingSpinner } from '../components/common/LoadingSpinner.tsx';
import { validateRequirements } from '../utils/validation.ts';
import type { Entrance, RequirementsSaveRequest } from '../types/requirements.ts';
import { mockRequirements } from '../mocks/mockData.ts';

export const RequirementsPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const { project, loading: projectLoading } = useProject();
  const navigate = useNavigate();

  const [siteWidth, setSiteWidth] = useState<number>(300);
  const [siteHeight, setSiteHeight] = useState<number>(300);
  const [minGreenPercent, setMinGreenPercent] = useState<number>(25);
  const [minParkingPercent, setMinParkingPercent] = useState<number>(10);
  const [minRoadWidth, setMinRoadWidth] = useState<number>(8);
  const [minBuildingGap, setMinBuildingGap] = useState<number>(10);
  const [entrances, setEntrances] = useState<Entrance[]>([
    { x: 150, y: 0, width: 10 },
  ]);

  const [loading, setLoading] = useState<boolean>(false);
  const [initialLoading, setInitialLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const numProjectId = parseInt(projectId || '1', 10);

  // Fetch existing requirements on mount
  useEffect(() => {
    const fetchExisting = async () => {
      setInitialLoading(true);
      setError(null);

      try {
        const token = localStorage.getItem('archopt_token');
        if (token?.includes('mock-demo')) {
          setSiteWidth(mockRequirements.siteWidth);
          setSiteHeight(mockRequirements.siteHeight);
          setMinGreenPercent(mockRequirements.minGreenPercent);
          setMinParkingPercent(mockRequirements.minParkingPercent);
          setMinRoadWidth(mockRequirements.minRoadWidth);
          setMinBuildingGap(mockRequirements.minBuildingGap);
          setEntrances(mockRequirements.entrances);
        } else {
          const reqs = await requirementsApi.getRequirements(numProjectId);
          setSiteWidth(reqs.siteWidth);
          setSiteHeight(reqs.siteHeight);
          setMinGreenPercent(reqs.minGreenPercent);
          setMinParkingPercent(reqs.minParkingPercent);
          setMinRoadWidth(reqs.minRoadWidth);
          setMinBuildingGap(reqs.minBuildingGap);
          setEntrances(reqs.entrances && reqs.entrances.length > 0 ? reqs.entrances : [{ x: 150, y: 0, width: 10 }]);
        }
      } catch (err: any) {
        // 404 is normal for a fresh project that has no requirements yet
        if (err.response?.status !== 404) {
          // Keep defaults
        }
      } finally {
        setInitialLoading(false);
      }
    };

    fetchExisting();
  }, [numProjectId]);

  const handleAddEntrance = () => {
    setEntrances([...entrances, { x: 0, y: Math.round(siteHeight / 2), width: 10 }]);
  };

  const handleRemoveEntrance = (index: number) => {
    setEntrances(entrances.filter((_, i) => i !== index));
  };

  const handleEntranceChange = (index: number, field: keyof Entrance, val: number) => {
    const updated = entrances.map((item, i) => {
      if (i === index) {
        return { ...item, [field]: val };
      }
      return item;
    });
    setEntrances(updated);
  };

  const handleSubmit = async (e: React.FormEvent, navigateNext = false) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    const payload: RequirementsSaveRequest = {
      siteWidth: Number(siteWidth),
      siteHeight: Number(siteHeight),
      minGreenPercent: Number(minGreenPercent),
      minParkingPercent: Number(minParkingPercent),
      minRoadWidth: Number(minRoadWidth),
      minBuildingGap: Number(minBuildingGap),
      entrances,
    };

    // Client-side validation
    const validationErr = validateRequirements(payload);
    if (validationErr) {
      setError(validationErr);
      return;
    }

    setLoading(true);

    try {
      const token = localStorage.getItem('archopt_token');
      if (!token?.includes('mock-demo')) {
        await requirementsApi.saveRequirements(numProjectId, payload);
      }

      setSuccess('Site requirements saved successfully.');

      if (navigateNext) {
        navigate(`/projects/${numProjectId}/buildings`);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save campus requirements.');
    } finally {
      setLoading(false);
    }
  };

  if (projectLoading || initialLoading) {
    return <LoadingSpinner message="Loading campus site requirements..." />;
  }

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
      <ProjectHeader project={project} activeStepTitle="1. Site Boundary & Environmental Requirements" />

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

      <form onSubmit={(e) => handleSubmit(e, false)}>
        <div className="grid-2">
          {/* Site Geometry Card */}
          <div className="card">
            <h3 className="card-title" style={{ marginBottom: '16px' }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="3" width="18" height="18" rx="2" />
                <path d="M3 9h18" />
                <path d="M9 21V9" />
              </svg>
              Site Boundary Dimensions
            </h3>

            <div className="form-group">
              <label className="form-label" htmlFor="site-width">Site Width (metres) *</label>
              <input
                id="site-width"
                type="number"
                min="10"
                max="2000"
                step="1"
                className="form-input"
                value={siteWidth}
                onChange={(e) => setSiteWidth(parseFloat(e.target.value) || 0)}
                required
              />
              <span className="form-hint">East-West horizontal dimension</span>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="site-height">Site Height (metres) *</label>
              <input
                id="site-height"
                type="number"
                min="10"
                max="2000"
                step="1"
                className="form-input"
                value={siteHeight}
                onChange={(e) => setSiteHeight(parseFloat(e.target.value) || 0)}
                required
              />
              <span className="form-hint">North-South vertical dimension</span>
            </div>

            <div style={{ padding: '12px', backgroundColor: '#0b1329', borderRadius: 'var(--radius-md)', marginTop: '8px' }}>
              <div style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>Total Site Area:</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                {(siteWidth * siteHeight).toLocaleString()} m²
              </div>
            </div>
          </div>

          {/* Environmental & Road Standards */}
          <div className="card">
            <h3 className="card-title" style={{ marginBottom: '16px' }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              </svg>
              Zoning & Environmental Ratios
            </h3>

            <div className="form-group">
              <label className="form-label" htmlFor="min-green">Minimum Green Space (%) *</label>
              <input
                id="min-green"
                type="number"
                min="0"
                max="100"
                step="0.5"
                className="form-input"
                value={minGreenPercent}
                onChange={(e) => setMinGreenPercent(parseFloat(e.target.value) || 0)}
                required
              />
              <span className="form-hint">Target green canopy / landscape coverage</span>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="min-parking">Minimum Parking (%) *</label>
              <input
                id="min-parking"
                type="number"
                min="0"
                max="100"
                step="0.5"
                className="form-input"
                value={minParkingPercent}
                onChange={(e) => setMinParkingPercent(parseFloat(e.target.value) || 0)}
                required
              />
              <span className="form-hint">Surface parking & transit bays</span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div className="form-group">
                <label className="form-label" htmlFor="road-width">Road Width (m) *</label>
                <input
                  id="road-width"
                  type="number"
                  min="2"
                  max="50"
                  step="0.5"
                  className="form-input"
                  value={minRoadWidth}
                  onChange={(e) => setMinRoadWidth(parseFloat(e.target.value) || 0)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="bldg-gap">Building Gap (m) *</label>
                <input
                  id="bldg-gap"
                  type="number"
                  min="1"
                  max="50"
                  step="0.5"
                  className="form-input"
                  value={minBuildingGap}
                  onChange={(e) => setMinBuildingGap(parseFloat(e.target.value) || 0)}
                  required
                />
              </div>
            </div>
          </div>
        </div>

        {/* Entrances Configuration Card */}
        <div className="card" style={{ marginTop: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 className="card-title">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M15 3h6v6" />
                <path d="M10 14 21 3" />
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
              </svg>
              Campus Entry Gate Coordinates ({entrances.length})
            </h3>
            <button
              type="button"
              onClick={handleAddEntrance}
              className="btn btn-secondary btn-sm"
            >
              + Add Entry Gate
            </button>
          </div>

          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Gate #</th>
                  <th>X Coordinate (East) [m]</th>
                  <th>Y Coordinate (North) [m]</th>
                  <th>Gate Width [m]</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {entrances.map((e, idx) => (
                  <tr key={idx}>
                    <td style={{ fontWeight: 600 }}>Gate {idx + 1}</td>
                    <td>
                      <input
                        type="number"
                        min="0"
                        max={siteWidth}
                        step="1"
                        className="form-input"
                        style={{ width: '120px' }}
                        value={e.x}
                        onChange={(ev) => handleEntranceChange(idx, 'x', parseFloat(ev.target.value) || 0)}
                        required
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        min="0"
                        max={siteHeight}
                        step="1"
                        className="form-input"
                        style={{ width: '120px' }}
                        value={e.y}
                        onChange={(ev) => handleEntranceChange(idx, 'y', parseFloat(ev.target.value) || 0)}
                        required
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        min="1"
                        max="50"
                        step="1"
                        className="form-input"
                        style={{ width: '100px' }}
                        value={e.width}
                        onChange={(ev) => handleEntranceChange(idx, 'width', parseFloat(ev.target.value) || 0)}
                        required
                      />
                    </td>
                    <td>
                      <button
                        type="button"
                        onClick={() => handleRemoveEntrance(idx)}
                        className="btn btn-danger btn-sm"
                        disabled={entrances.length <= 1}
                        title={entrances.length <= 1 ? 'At least one entrance is required' : 'Remove Gate'}
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '24px' }}>
          <Link to="/projects" className="btn btn-secondary">
            ← Back to Projects
          </Link>

          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              type="submit"
              className="btn btn-secondary"
              disabled={loading}
            >
              {loading ? 'Saving...' : 'Save Requirements'}
            </button>
            <button
              type="button"
              onClick={(e) => handleSubmit(e, true)}
              className="btn btn-primary"
              disabled={loading}
            >
              Save & Proceed to Buildings →
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};
export default RequirementsPage;
