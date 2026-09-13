import React from 'react';
import type { Constraint } from '../../types/constraint.ts';
import type { Building } from '../../types/building.ts';
import { EmptyState } from '../common/EmptyState.tsx';

interface ConstraintListProps {
  constraints: Constraint[];
  buildings: Building[];
  onAddClick?: () => void;
}

export const ConstraintList: React.FC<ConstraintListProps> = ({
  constraints,
  buildings,
  onAddClick,
}) => {
  const buildingMap = new Map<number, Building>(buildings.map((b) => [b.id, b]));

  if (constraints.length === 0) {
    return (
      <EmptyState
        title="No Spatial Constraints Configured"
        description="Set minimum distance buffers, zoning groupings, or proximity requirements between buildings to guide the AI optimizer."
        actionText="+ Add First Constraint"
        onAction={onAddClick}
      />
    );
  }

  return (
    <div className="table-container">
      <table className="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Type</th>
            <th>Source Entity</th>
            <th>Target Entity</th>
            <th>Rule Definition</th>
            <th>Priority</th>
          </tr>
        </thead>
        <tbody>
          {constraints.map((c) => {
            const src = c.sourceId ? buildingMap.get(c.sourceId) : null;
            const tgt = c.targetId ? buildingMap.get(c.targetId) : null;
            const isHard = c.priority?.toLowerCase() === 'hard';

            return (
              <tr key={c.id}>
                <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>
                  #{c.id}
                </td>
                <td style={{ fontWeight: 600, color: 'var(--accent-cyan)' }}>
                  {c.type}
                </td>
                <td>
                  {src ? (
                    <div>
                      <span style={{ fontWeight: 600 }}>{src.name}</span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginLeft: '6px' }}>
                        (#{src.id})
                      </span>
                    </div>
                  ) : (
                    <span style={{ color: 'var(--text-dim)' }}>Entity #{c.sourceId}</span>
                  )}
                </td>
                <td>
                  {tgt ? (
                    <div>
                      <span style={{ fontWeight: 600 }}>{tgt.name}</span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginLeft: '6px' }}>
                        (#{tgt.id})
                      </span>
                    </div>
                  ) : (
                    <span style={{ color: 'var(--text-dim)' }}>Entity #{c.targetId}</span>
                  )}
                </td>
                <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.875rem' }}>
                  distance {c.operator || '>='} {c.value !== undefined && c.value !== null ? `${c.value}m` : 'N/A'}
                </td>
                <td>
                  <span className={`badge ${isHard ? 'badge-hard' : 'badge-soft'}`}>
                    {c.priority || 'soft'}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
export default ConstraintList;
