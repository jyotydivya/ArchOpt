import React from 'react';
import type { LayoutSummary } from '../../types/layout.ts';
import { formatPercent, formatScore } from '../../utils/formatters.ts';

interface MetricsTableProps {
  layouts: LayoutSummary[];
  selectedLayoutId?: number | null;
  onInspect: (layoutId: number) => void;
  onSelect?: (layoutId: number) => void;
}

export const MetricsTable: React.FC<MetricsTableProps> = ({
  layouts,
  selectedLayoutId,
  onInspect,
  onSelect,
}) => {
  return (
    <div className="table-container">
      <table className="table">
        <thead>
          <tr>
            <th>Rank</th>
            <th>Candidate ID</th>
            <th>Feasibility</th>
            <th>Land Utilization</th>
            <th>Green Ratio</th>
            <th>Parking Ratio</th>
            <th>Accessibility</th>
            <th>Road Efficiency</th>
            <th>Constraint Score</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {layouts.map((l) => {
            const isSel = selectedLayoutId === l.id;
            return (
              <tr
                key={l.id}
                style={{
                  backgroundColor: isSel ? 'rgba(16, 185, 129, 0.1)' : undefined,
                }}
              >
                <td>
                  <span
                    style={{
                      width: '24px',
                      height: '24px',
                      borderRadius: '50%',
                      backgroundColor: l.rank === 1 ? 'rgba(14, 165, 233, 0.2)' : 'rgba(255, 255, 255, 0.08)',
                      color: l.rank === 1 ? 'var(--accent-cyan)' : 'var(--text-muted)',
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 700,
                      fontSize: '0.75rem',
                    }}
                  >
                    #{l.rank}
                  </span>
                </td>
                <td style={{ fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                  Layout #{l.id} {isSel && <span className="badge badge-selected" style={{ marginLeft: '4px' }}>SELECTED</span>}
                </td>
                <td>
                  <span className={`badge ${l.feasible ? 'badge-feasible' : 'badge-infeasible'}`}>
                    {l.feasible ? 'FEASIBLE' : 'INFEASIBLE'}
                  </span>
                </td>
                <td style={{ fontFamily: 'var(--font-mono)' }}>{formatPercent(l.metrics.landUtilization)}</td>
                <td style={{ fontFamily: 'var(--font-mono)' }}>{formatPercent(l.metrics.greenRatio)}</td>
                <td style={{ fontFamily: 'var(--font-mono)' }}>{formatPercent(l.metrics.parkingRatio)}</td>
                <td style={{ fontFamily: 'var(--font-mono)' }}>{formatScore(l.metrics.accessibilityScore)}</td>
                <td style={{ fontFamily: 'var(--font-mono)' }}>{formatScore(l.metrics.roadEfficiency)}</td>
                <td style={{ fontFamily: 'var(--font-mono)', color: l.metrics.constraintScore >= 1.0 ? 'var(--accent-emerald)' : 'var(--accent-rose)', fontWeight: 600 }}>
                  {formatPercent(l.metrics.constraintScore)}
                </td>
                <td>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <button
                      onClick={() => onInspect(l.id)}
                      className="btn btn-secondary btn-sm"
                      title="Inspect 2D Campus Canvas"
                    >
                      Inspect 2D
                    </button>
                    {onSelect && !isSel && (
                      <button
                        onClick={() => onSelect(l.id)}
                        className="btn btn-primary btn-sm"
                        title="Select Plan"
                      >
                        Select
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
export default MetricsTable;
