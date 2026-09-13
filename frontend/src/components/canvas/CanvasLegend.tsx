import React from 'react';

export const CanvasLegend: React.FC = () => {
  const items = [
    { label: 'Academic Zone', color: 'var(--zone-academic)' },
    { label: 'Residential Zone', color: 'var(--zone-residential)' },
    { label: 'Sports & Recreation', color: 'var(--zone-sports)' },
    { label: 'Administration', color: 'var(--zone-admin)' },
    { label: 'Library', color: 'var(--zone-library)' },
    { label: 'Green Landscape', color: 'var(--zone-green)' },
    { label: 'Surface Parking', color: 'var(--zone-parking)' },
    { label: 'Circulation Road', color: 'var(--zone-road)' },
    { label: 'Campus Entrance', color: 'var(--zone-entrance)' },
  ];

  return (
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        gap: '12px',
        padding: '10px 16px',
        backgroundColor: '#0b1329',
        borderTop: '1px solid var(--border-color)',
        fontSize: '0.75rem',
      }}
    >
      <span style={{ fontWeight: 600, color: 'var(--text-muted)' }}>Zoning Legend:</span>
      {items.map((item) => (
        <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <span
            style={{
              width: '10px',
              height: '10px',
              borderRadius: '2px',
              backgroundColor: item.color,
              display: 'inline-block',
            }}
          />
          <span style={{ color: 'var(--text-main)' }}>{item.label}</span>
        </div>
      ))}
    </div>
  );
};
export default CanvasLegend;
