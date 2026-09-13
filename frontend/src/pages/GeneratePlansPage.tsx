import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useProject } from '../hooks/useProject.ts';
import { layoutsApi } from '../api/layouts.ts';
import { requirementsApi } from '../api/requirements.ts';
import { buildingsApi } from '../api/buildings.ts';
import { constraintsApi } from '../api/constraints.ts';
import { ProjectHeader } from '../components/projects/ProjectHeader.tsx';
import { ErrorBanner } from '../components/common/ErrorBanner.tsx';
import { LoadingSpinner } from '../components/common/LoadingSpinner.tsx';
import type { CampusRequirements } from '../types/requirements.ts';
import type { Building } from '../types/building.ts';
import type { Constraint } from '../types/constraint.ts';
import type { LayoutRunCreateResponse } from '../types/layout.ts';
import { mockRequirements, mockBuildings, mockConstraints } from '../mocks/mockData.ts';

export const GeneratePlansPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const { project, loading: projectLoading } = useProject();
  const navigate = useNavigate();

  const [requirements, setRequirements] = useState<CampusRequirements | null>(null);
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [constraints, setConstraints] = useState<Constraint[]>([]);
  const [dataLoading, setDataLoading] = useState<boolean>(true);

  // Run parameters
  const [candidateCount, setCandidateCount] = useState<number>(100);
  const [topK, setTopK] = useState<number>(5);
  const [algorithm] = useState<string>('GNN_NSGA2');

  const [generating, setGenerating] = useState<boolean>(false);
  const [generationStep, setGenerationStep] = useState<number>(1);
  const [result, setResult] = useState<LayoutRunCreateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const numProjectId = parseInt(projectId || '1', 10);

  useEffect(() => {
    const fetchPreflight = async () => {
      setDataLoading(true);
      setError(null);

      try {
        const token = localStorage.getItem('archopt_token');
        if (token?.includes('mock-demo')) {
          setRequirements(mockRequirements);
          setBuildings(mockBuildings);
          setConstraints(mockConstraints);
        } else {
          const [reqs, bList, cList] = await Promise.all([
            requirementsApi.getRequirements(numProjectId).catch(() => null),
            buildingsApi.getBuildings(numProjectId).catch(() => []),
            constraintsApi.getConstraints(numProjectId).catch(() => []),
          ]);
          setRequirements(reqs);
          setBuildings(bList);
          setConstraints(cList);
        }
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to verify project setup.');
      } finally {
        setDataLoading(false);
      }
    };

    fetchPreflight();
  }, [numProjectId]);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!requirements || buildings.length === 0) {
      setError('Cannot generate layouts without site requirements and at least one building.');
      return;
    }

    setGenerating(true);
    setError(null);
    setResult(null);
    setGenerationStep(1);

    const stepInterval = setInterval(() => {
      setGenerationStep((prev) => (prev < 4 ? prev + 1 : prev));
    }, 700);

    try {
      const token = localStorage.getItem('archopt_token');
      let runResponse: LayoutRunCreateResponse;

      if (token?.includes('mock-demo')) {
        // Simulate local generation latency
        await new Promise((resolve) => setTimeout(resolve, 2000));
        runResponse = {
          runId: 101,
          status: 'COMPLETED',
          layoutCount: topK,
        };
      } else {
        // Call Real API: POST /api/projects/{projectId}/layout-runs
        runResponse = await layoutsApi.createLayoutRun(numProjectId, {
          candidateCount: Number(candidateCount),
          topK: Number(topK),
          algorithm,
        });
      }

      setResult(runResponse);
    } catch (err: any) {
      if (err.response?.status === 400) {
        setError('400 INVALID_REQUIREMENTS: Site requirements or buildings are missing or incomplete.');
      } else if (err.response?.status === 422) {
        setError('422 GENERATION_FAILED: Upstream ML/optimization algorithm failed or could not find feasible candidates.');
      } else if (err.response?.data?.detail) {
        setError(typeof err.response.data.detail === 'string' ? err.response.data.detail : 'Optimization run failed');
      } else {
        setError('Connection error occurred while executing layout run on the server.');
      }
    } finally {
      clearInterval(stepInterval);
      setGenerating(false);
    }
  };

  if (projectLoading || dataLoading) {
    return <LoadingSpinner message="Checking project readiness..." />;
  }

  const isReady = !!requirements && buildings.length > 0;

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
      <ProjectHeader project={project} activeStepTitle="4. AI Generation & Optimization Execution" />

      <ErrorBanner message={error} onDismiss={() => setError(null)} />

      {/* Pre-flight Checklist Card */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <h3 className="card-title" style={{ marginBottom: '16px' }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="9 11 12 14 22 4" />
            <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
          </svg>
          Pre-Flight Optimization Checklist
        </h3>

        <div className="grid-3">
          <div style={{ padding: '14px', backgroundColor: '#0b1329', borderRadius: 'var(--radius-md)', border: `1px solid ${requirements ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)'}` }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <span style={{ color: requirements ? 'var(--accent-emerald)' : 'var(--accent-rose)', fontWeight: 700 }}>
                {requirements ? '✓' : '✕'}
              </span>
              <strong style={{ fontSize: '0.875rem' }}>Site Boundaries</strong>
            </div>
            <div style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
              {requirements ? `${requirements.siteWidth}m × ${requirements.siteHeight}m (${requirements.entrances.length} gates)` : 'Not configured yet'}
            </div>
          </div>

          <div style={{ padding: '14px', backgroundColor: '#0b1329', borderRadius: 'var(--radius-md)', border: `1px solid ${buildings.length > 0 ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)'}` }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <span style={{ color: buildings.length > 0 ? 'var(--accent-emerald)' : 'var(--accent-rose)', fontWeight: 700 }}>
                {buildings.length > 0 ? '✓' : '✕'}
              </span>
              <strong style={{ fontSize: '0.875rem' }}>Building Inventory</strong>
            </div>
            <div style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
              {buildings.length > 0 ? `${buildings.length} building specifications` : 'No buildings added'}
            </div>
          </div>

          <div style={{ padding: '14px', backgroundColor: '#0b1329', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <span style={{ color: 'var(--accent-cyan)', fontWeight: 700 }}>ℹ</span>
              <strong style={{ fontSize: '0.875rem' }}>Spatial Constraints</strong>
            </div>
            <div style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
              {constraints.length} active constraints defined
            </div>
          </div>
        </div>

        {!isReady && (
          <div className="alert alert-error" style={{ marginTop: '16px' }}>
            <span>Please complete Site Requirements and add at least one Building before generating plans.</span>
          </div>
        )}
      </div>

      {/* Generation Parameters & Trigger Card */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <h3 className="card-title" style={{ marginBottom: '16px' }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2v4" />
            <path d="M12 18v4" />
            <path d="m4.93 4.93 2.83 2.83" />
            <path d="m16.24 16.24 2.83 2.83" />
            <path d="M2 12h4" />
            <path d="M18 12h4" />
          </svg>
          Run Parameters
        </h3>

        <form onSubmit={handleGenerate}>
          <div className="grid-3">
            <div className="form-group">
              <label className="form-label" htmlFor="gen-candidates">Candidate Population (GNN)</label>
              <input
                id="gen-candidates"
                type="number"
                min="10"
                max="500"
                step="10"
                className="form-input"
                value={candidateCount}
                onChange={(e) => setCandidateCount(parseInt(e.target.value, 10) || 100)}
                disabled={generating}
                required
              />
              <span className="form-hint">Number of layouts generated by GNN</span>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="gen-topk">Top Pareto Plans (NSGA-II)</label>
              <input
                id="gen-topk"
                type="number"
                min="1"
                max="20"
                step="1"
                className="form-input"
                value={topK}
                onChange={(e) => setTopK(parseInt(e.target.value, 10) || 5)}
                disabled={generating}
                required
              />
              <span className="form-hint">Best Pareto-optimal layouts returned</span>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="gen-algo">Optimization Engine</label>
              <input
                id="gen-algo"
                type="text"
                className="form-input"
                value="GNN + NSGA-II (Contract 8)"
                disabled
              />
              <span className="form-hint">P1 Graph $\rightarrow$ P2 GNN $\rightarrow$ P3 NSGA-II</span>
            </div>
          </div>

          <div style={{ marginTop: '20px' }}>
            <button
              type="submit"
              className="btn btn-primary btn-lg"
              style={{ width: '100%' }}
              disabled={generating || !isReady}
            >
              {generating ? 'Executing AI Campus Optimization Pipeline...' : 'Generate AI Campus Layouts'}
            </button>
          </div>
        </form>
      </div>

      {/* Live Generation Progress State */}
      {generating && (
        <div className="card" style={{ textAlign: 'center', padding: '36px 20px', marginBottom: '24px' }}>
          <LoadingSpinner size="lg" message="" />
          <h3 style={{ fontSize: '1.25rem', marginTop: '16px', marginBottom: '8px' }}>
            Generating Campus Master Plans
          </h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: '20px' }}>
            {generationStep === 1 && 'Step 1/4: Constructing Campus Graph from requirements & constraints (Contract 5)...'}
            {generationStep === 2 && 'Step 2/4: Generating candidate layouts with Graph Neural Network (Contract 6)...'}
            {generationStep === 3 && 'Step 3/4: Evaluating 6 Pareto objectives & resolving constraint violations (NSGA-II)...'}
            {generationStep >= 4 && 'Step 4/4: Ranking Pareto-optimal layouts and persisting records in PostgreSQL...'}
          </p>

          <div className="metric-bar-container" style={{ maxWidth: '500px', margin: '0 auto', height: '8px' }}>
            <div
              className="metric-bar-fill"
              style={{
                width: `${(generationStep / 4) * 100}%`,
                backgroundColor: 'var(--accent-cyan)',
              }}
            />
          </div>
        </div>
      )}

      {/* Success Result State */}
      {result && (
        <div className="card" style={{ border: '1px solid rgba(16, 185, 129, 0.4)', backgroundColor: 'rgba(16, 185, 129, 0.05)', marginBottom: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                <span style={{ color: 'var(--accent-emerald)', fontSize: '1.25rem' }}>✓</span>
                <h3 style={{ fontSize: '1.25rem', color: 'var(--accent-emerald)' }}>
                  Layout Generation Run Completed!
                </h3>
              </div>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                Run ID: #{result.runId} • Successfully generated and ranked {result.layoutCount} Pareto-optimal campus layouts.
              </p>
            </div>

            <button
              onClick={() => navigate(`/projects/${numProjectId}/compare`)}
              className="btn btn-accent"
            >
              Compare Generated Plans →
            </button>
          </div>
        </div>
      )}

      {/* Bottom Navigation */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Link to={`/projects/${numProjectId}/constraints`} className="btn btn-secondary">
          ← Back to Constraints
        </Link>

        <button
          onClick={() => navigate(`/projects/${numProjectId}/compare`)}
          className="btn btn-secondary"
        >
          View Existing Layouts →
        </button>
      </div>
    </div>
  );
};
export default GeneratePlansPage;
