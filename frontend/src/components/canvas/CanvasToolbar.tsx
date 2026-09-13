import React from 'react';

interface CanvasToolbarProps {
  onZoomIn: () => void;
  onZoomOut: () => void;
  onFit: () => void;
  onReset: () => void;
  showGrid: boolean;
  setShowGrid: (val: boolean) => void;
  showLabels: boolean;
  setShowLabels: (val: boolean) => void;
  showLayers: boolean;
  setShowLayers: (val: boolean) => void;
}

export const CanvasToolbar: React.FC<CanvasToolbarProps> = ({
  onZoomIn,
  onZoomOut,
  onFit,
  onReset,
  showGrid,
  setShowGrid,
  showLabels,
  setShowLabels,
  showLayers,
  setShowLayers,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '10px 16px',
        backgroundColor: '#0f172a',
        borderBottom: '1px solid var(--border-color)',
        gap: '12px',
      }}
    >
      {/* Zoom / Navigation Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
        <button
          type="button"
          onClick={onZoomIn}
          className="btn btn-secondary btn-sm"
          title="Zoom In"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          Zoom In
        </button>

        <button
          type="button"
          onClick={onZoomOut}
          className="btn btn-secondary btn-sm"
          title="Zoom Out"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          Zoom Out
        </button>

        <button
          type="button"
          onClick={onFit}
          className="btn btn-secondary btn-sm"
          title="Fit Site to Viewport"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M15 3h6v6" />
            <path d="M9 21H3v-6" />
            <path d="M21 3l-7 7" />
            <path d="M3 21l7-7" />
          </svg>
          Fit Site
        </button>

        <button
          type="button"
          onClick={onReset}
          className="btn btn-secondary btn-sm"
          title="Reset View"
        >
          Reset
        </button>
      </div>

      {/* Layer Visibility Toggles */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.8125rem' }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: '5px', cursor: 'pointer', color: 'var(--text-muted)' }}>
          <input
            type="checkbox"
            checked={showGrid}
            onChange={(e) => setShowGrid(e.target.checked)}
          />
          Grid
        </label>

        <label style={{ display: 'flex', alignItems: 'center', gap: '5px', cursor: 'pointer', color: 'var(--text-muted)' }}>
          <input
            type="checkbox"
            checked={showLabels}
            onChange={(e) => setShowLabels(e.target.checked)}
          />
          Labels
        </label>

        <label style={{ display: 'flex', alignItems: 'center', gap: '5px', cursor: 'pointer', color: 'var(--text-muted)' }}>
          <input
            type="checkbox"
            checked={showLayers}
            onChange={(e) => setShowLayers(e.target.checked)}
          />
          Landscape & Roads
        </label>
      </div>
    </div>
  );
};
export default CanvasToolbar;
