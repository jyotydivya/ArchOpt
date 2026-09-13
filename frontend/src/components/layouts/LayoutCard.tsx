import React from 'react';
import type { LayoutSummary } from '../../types/layout.ts';
import { formatPercent, formatScore, getMetricColor } from '../../utils/formatters.ts';

interface LayoutCardProps {
  layout: LayoutSummary;
  isSelected?: boolean;
  onInspect: () => void;
  onSelect?: () => void;
}

export const LayoutCard: React.FC<LayoutCardProps> = ({
  layout,
  isSelected,
  onInspect,
  onSelect,
}) => {
  const m = layout.metrics;

  const metricRows = [
    { label: 'Land Utilization', val: m.landUtilization, display: formatPercent(m.landUtilization) },
    { label: 'Green Ratio', val: m.greenRatio, display: formatPercent(m.greenRatio) },
    { label: 'Parking Ratio', val: m.parkingRatio, display: formatPercent(m.parkingRatio) },
    { label: 'Accessibility', val: m.accessibilityScore, display: formatScore(m.accessibilityScore) },
    { label: 'Road Efficiency', val: m.roadEfficiency, display: formatScore(m.roadEfficiency) },
    { label: 'Constraint Compliance', val: m.constraintScore, display: formatPercent(m.constraintScore) },
  ];

  return (
    <div
      className="card"
      style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        border: isSelected
          ? '2px solid var(--accent-emerald)'
          : layout.rank === 1
          ? '1px solid rgba(14, 165, 233, 0.5)'
          : '1px solid var(--border-color)',
        boxShadow: isSelected ? '0 0 16px rgba(16, 185, 129, 0.2)' : 'var(--shadow-md)',
      }}
    >
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span
              style={{
                width: '28px',
                height: '28px',
                borderRadius: '50%',
                backgroundColor: layout.rank === 1 ? 'rgba(14, 165, 233, 0.2)' : 'rgba(255, 255, 255, 0.08)',
                color: layout.rank === 1 ? 'var(--accent-cyan)' : 'var(--text-muted)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 700,
                fontSize: '0.875rem',
              }}
            >
              #{layout.rank}
            </span>
            <h3 style={{ fontSize: '1.125rem' }}>Plan Candidate #{layout.id}</h3>
          </div>

          <div style={{ display: 'flex', gap: '6px' }}>
            {isSelected && <span className="badge badge-selected">SELECTED PLAN</span>}
            <span className={`badge ${layout.feasible ? 'badge-feasible' : 'badge-infeasible'}`}>
              {layout.feasible ? 'FEASIBLE' : 'INFEASIBLE'}
            </span>
          </div>
        </div>

        {/* Metrics Grid */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', margin: '16px 0 20px' }}>
          {metricRows.map((item) => {
            const color = getMetricColor(item.label, item.val);
            const fillWidth = Math.min(100, Math.max(0, item.val * 100));

            return (
              <div key={item.label}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8125rem', marginBottom: '3px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>{item.label}</span>
                  <span style={{ fontWeight: 600, color, fontFamily: 'var(--font-mono)' }}>
                    {item.display}
                  </span>
                </div>
                <div className="metric-bar-container" style={{ height: '5px' }}>
                  <div className="metric-bar-fill" style={{ width: `${fillWidth}%`, backgroundColor: color }} />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div style={{ display: 'flex', gap: '8px', paddingTop: '16px', borderTop: '1px solid var(--border-color)' }}>
        <button onClick={onInspect} className="btn btn-secondary btn-sm" style={{ flex: 1 }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polygon points="12 2 2 7 12 12 22 7 12 2" />
            <polyline points="2 17 12 22 22 17" />
          </svg>
          2D Viewer
        </button>

        {onSelect && !isSelected && (
          <button onClick={onSelect} className="btn btn-primary btn-sm" style={{ flex: 1 }}>
            Select Plan
          </button>
        )}
      </div>
    </div>
  );
};
export default LayoutCard;
