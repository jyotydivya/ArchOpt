import React from 'react';
import type { Building } from '../../types/building.ts';
import { EmptyState } from '../common/EmptyState.tsx';

interface BuildingTableProps {
  buildings: Building[];
  onAddClick?: () => void;
}

export const BuildingTable: React.FC<BuildingTableProps> = ({ buildings, onAddClick }) => {
  if (buildings.length === 0) {
    return (
      <EmptyState
        title="No Buildings Added Yet"
        description="Add academic blocks, hostels, libraries, and facilities to build your campus inventory before generating layouts."
        actionText="+ Add First Building"
        onAction={onAddClick}
      />
    );
  }

  const getZoneColor = (zone: string) => {
    switch (zone.toLowerCase()) {
      case 'academic': return 'var(--zone-academic)';
      case 'residential': return 'var(--zone-residential)';
      case 'sports': return 'var(--zone-sports)';
      case 'admin': return 'var(--zone-admin)';
      default: return 'var(--text-muted)';
    }
  };

  return (
    <div className="table-container">
      <table className="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Building Name</th>
            <th>Type</th>
            <th>Zone</th>
            <th>Footprint (W × D)</th>
            <th>Ground Area</th>
            <th>Height / Floors</th>
            <th>Req. Count</th>
          </tr>
        </thead>
        <tbody>
          {buildings.map((b) => {
            const footprint = b.width * b.depth;
            const zoneColor = getZoneColor(b.zone);

            return (
              <tr key={b.id}>
                <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>
                  #{b.id}
                </td>
                <td style={{ fontWeight: 600, color: 'var(--text-main)' }}>
                  {b.name}
                </td>
                <td style={{ textTransform: 'capitalize', color: 'var(--text-muted)' }}>
                  {b.type}
                </td>
                <td>
                  <span
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '5px',
                      padding: '2px 8px',
                      borderRadius: '9999px',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      backgroundColor: `${zoneColor}22`,
                      color: zoneColor,
                      border: `1px solid ${zoneColor}44`,
                      textTransform: 'uppercase',
                    }}
                  >
                    <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: zoneColor }} />
                    {b.zone}
                  </span>
                </td>
                <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8125rem' }}>
                  {b.width}m × {b.depth}m
                </td>
                <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8125rem', color: 'var(--accent-cyan)' }}>
                  {footprint.toLocaleString()} m²
                </td>
                <td style={{ fontSize: '0.8125rem' }}>
                  {b.height}m ({b.floorCount} {b.floorCount === 1 ? 'floor' : 'floors'})
                </td>
                <td style={{ fontWeight: 600, textAlign: 'center' }}>
                  {b.requiredCount}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
export default BuildingTable;
