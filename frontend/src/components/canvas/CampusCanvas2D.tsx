import React, { useRef, useState, useEffect, useCallback, useMemo } from 'react';
import type { LayoutDetail } from '../../types/layout.ts';
import type { Building } from '../../types/building.ts';
import {
  type ViewportTransform,
  isPointInRotatedRect,
} from '../../utils/coordinates.ts';

interface CampusCanvas2DProps {
  layout: LayoutDetail;
  buildings: Building[];
  showGrid: boolean;
  showLabels: boolean;
  showLayers: boolean;
  transform: ViewportTransform;
  setTransform: React.Dispatch<React.SetStateAction<ViewportTransform>>;
}

interface HoveredBuildingInfo {
  building: Building;
  x: number;
  y: number;
  rotation: number;
  screenX: number;
  screenY: number;
}

export const CampusCanvas2D: React.FC<CampusCanvas2DProps> = ({
  layout,
  buildings,
  showGrid,
  showLabels,
  showLayers,
  transform,
  setTransform,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [hovered, setHovered] = useState<HoveredBuildingInfo | null>(null);

  const buildingMap = useMemo(
    () => new Map<number, Building>(buildings.map((b) => [b.id, b])),
    [buildings]
  );

  const getZoneColor = (zone?: string) => {
    switch (zone?.toLowerCase()) {
      case 'academic': return '#3b82f6';
      case 'residential': return '#f59e0b';
      case 'sports': return '#ec4899';
      case 'admin': return '#8b5cf6';
      case 'library': return '#06b6d4';
      default: return '#64748b';
    }
  };

  // Main Canvas Render Loop
  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const { width: canvasWidth, height: canvasHeight } = canvas;
    const { siteWidth, siteHeight } = {
      siteWidth: layout.site.width,
      siteHeight: layout.site.height,
    };
    const { scale, offsetX, offsetY } = transform;

    // Clear canvas
    ctx.clearRect(0, 0, canvasWidth, canvasHeight);

    // Background ground plane
    ctx.fillStyle = '#080c14';
    ctx.fillRect(0, 0, canvasWidth, canvasHeight);

    // 1. Site Boundary
    const siteScreenX = offsetX;
    const siteScreenY = offsetY;
    const siteScreenWidth = siteWidth * scale;
    const siteScreenHeight = siteHeight * scale;

    ctx.fillStyle = '#0d1527';
    ctx.fillRect(siteScreenX, siteScreenY, siteScreenWidth, siteScreenHeight);

    // 2. Coordinate Grid (every 25m or 50m)
    if (showGrid) {
      ctx.strokeStyle = 'rgba(51, 65, 85, 0.35)';
      ctx.lineWidth = 1;
      const gridSize = siteWidth > 400 ? 50 : 25;

      for (let gx = 0; gx <= siteWidth; gx += gridSize) {
        const x = siteScreenX + gx * scale;
        ctx.beginPath();
        ctx.moveTo(x, siteScreenY);
        ctx.lineTo(x, siteScreenY + siteScreenHeight);
        ctx.stroke();

        // Grid label
        ctx.fillStyle = 'rgba(148, 163, 184, 0.4)';
        ctx.font = '10px ui-monospace, monospace';
        ctx.fillText(`${gx}m`, x + 3, siteScreenY + siteScreenHeight - 6);
      }

      for (let gy = 0; gy <= siteHeight; gy += gridSize) {
        const y = siteScreenY + (siteHeight - gy) * scale;
        ctx.beginPath();
        ctx.moveTo(siteScreenX, y);
        ctx.lineTo(siteScreenX + siteScreenWidth, y);
        ctx.stroke();

        // Grid label
        ctx.fillStyle = 'rgba(148, 163, 184, 0.4)';
        ctx.font = '10px ui-monospace, monospace';
        ctx.fillText(`${gy}m`, siteScreenX + 4, y - 4);
      }
    }

    // Site border outline
    ctx.strokeStyle = 'rgba(14, 165, 233, 0.7)';
    ctx.lineWidth = 2;
    ctx.strokeRect(siteScreenX, siteScreenY, siteScreenWidth, siteScreenHeight);

    // 3. Landscape Green Areas
    if (showLayers && layout.greenAreas) {
      layout.greenAreas.forEach((area: any) => {
        const ax = siteScreenX + area.x * scale;
        const ay = siteScreenY + (siteHeight - area.y - area.height) * scale;
        const aw = area.width * scale;
        const ah = area.height * scale;

        ctx.fillStyle = 'rgba(16, 185, 129, 0.2)';
        ctx.fillRect(ax, ay, aw, ah);
        ctx.strokeStyle = 'rgba(16, 185, 129, 0.6)';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([4, 4]);
        ctx.strokeRect(ax, ay, aw, ah);
        ctx.setLineDash([]);

        if (showLabels && aw > 30) {
          ctx.fillStyle = '#6ee7b7';
          ctx.font = '11px system-ui, sans-serif';
          ctx.fillText('Landscape', ax + 6, ay + 16);
        }
      });
    }

    // 4. Surface Parking Areas
    if (showLayers && layout.parkingAreas) {
      layout.parkingAreas.forEach((area: any) => {
        const px = siteScreenX + area.x * scale;
        const py = siteScreenY + (siteHeight - area.y - area.height) * scale;
        const pw = area.width * scale;
        const ph = area.height * scale;

        ctx.fillStyle = 'rgba(100, 116, 139, 0.25)';
        ctx.fillRect(px, py, pw, ph);
        ctx.strokeStyle = 'rgba(148, 163, 184, 0.5)';
        ctx.lineWidth = 1.5;
        ctx.strokeRect(px, py, pw, ph);

        if (showLabels && pw > 25) {
          ctx.fillStyle = '#cbd5e1';
          ctx.font = '11px system-ui, sans-serif';
          ctx.fillText('P', px + pw / 2 - 4, py + ph / 2 + 4);
        }
      });
    }

    // 5. Road Networks
    if (showLayers && layout.roads) {
      layout.roads.forEach((road: any) => {
        const rx = siteScreenX + road.x * scale;
        const ry = siteScreenY + (siteHeight - road.y) * scale;
        const rw = road.width * scale;
        const rlen = road.length * scale;

        ctx.save();
        ctx.translate(rx, ry);
        ctx.rotate((-road.rotation * Math.PI) / 180);

        ctx.fillStyle = 'rgba(51, 65, 85, 0.6)';
        ctx.fillRect(0, -rw / 2, rlen, rw);
        ctx.strokeStyle = 'rgba(148, 163, 184, 0.4)';
        ctx.lineWidth = 1;
        ctx.strokeRect(0, -rw / 2, rlen, rw);

        ctx.restore();
      });
    }

    // 6. Buildings Rendering
    layout.buildings.forEach((pos) => {
      const bMeta = buildingMap.get(pos.buildingId);
      const widthMetres = bMeta ? bMeta.width : 60;
      const depthMetres = bMeta ? bMeta.depth : 40;
      const zoneColor = getZoneColor(bMeta?.zone);

      const bWidthPx = widthMetres * scale;
      const bDepthPx = depthMetres * scale;

      // Center point calculation with Y-inversion
      const centerX = siteScreenX + (pos.x + widthMetres / 2) * scale;
      const centerY = siteScreenY + (siteHeight - (pos.y + depthMetres / 2)) * scale;

      ctx.save();
      ctx.translate(centerX, centerY);
      ctx.rotate((-pos.rotation * Math.PI) / 180);

      // Building footprint fill
      ctx.fillStyle = `${zoneColor}33`; // 20% opacity
      ctx.fillRect(-bWidthPx / 2, -bDepthPx / 2, bWidthPx, bDepthPx);

      // Building boundary stroke
      ctx.strokeStyle = zoneColor;
      ctx.lineWidth = 2;
      ctx.strokeRect(-bWidthPx / 2, -bDepthPx / 2, bWidthPx, bDepthPx);

      // Roof hatch / diagonal line accent
      ctx.strokeStyle = `${zoneColor}55`;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(-bWidthPx / 2, -bDepthPx / 2);
      ctx.lineTo(bWidthPx / 2, bDepthPx / 2);
      ctx.stroke();

      // Building Label inside footprint
      if (showLabels && bWidthPx > 30 && bDepthPx > 20) {
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 11px system-ui, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        const name = bMeta ? bMeta.name : `Bldg #${pos.buildingId}`;
        const shortName = name.length > 14 ? `${name.substring(0, 12)}...` : name;
        ctx.fillText(shortName, 0, -4);

        ctx.font = '9px ui-monospace, monospace';
        ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
        ctx.fillText(`${widthMetres}×${depthMetres}m`, 0, 8);
      }

      ctx.restore();
    });

    // 7. Entrances & Access Arrows
    if (layout.entrances) {
      layout.entrances.forEach((entrance, idx) => {
        const ex = siteScreenX + entrance.x * scale;
        const ey = siteScreenY + (siteHeight - entrance.y) * scale;
        const gateWidthPx = entrance.width * scale;

        ctx.save();
        ctx.translate(ex, ey);

        // Entrance marker (Red accent)
        ctx.fillStyle = 'var(--zone-entrance)';
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2;

        // Draw gate bar
        ctx.fillRect(-gateWidthPx / 2, -4, gateWidthPx, 8);
        ctx.strokeRect(-gateWidthPx / 2, -4, gateWidthPx, 8);

        // Directional arrow into site
        ctx.beginPath();
        const arrowDir = entrance.y === 0 ? -1 : 1; // pointing inward
        ctx.moveTo(-6, arrowDir * 6);
        ctx.lineTo(0, arrowDir * 16);
        ctx.lineTo(6, arrowDir * 6);
        ctx.fillStyle = '#ef4444';
        ctx.fill();

        if (showLabels) {
          ctx.fillStyle = '#f87171';
          ctx.font = 'bold 10px system-ui, sans-serif';
          ctx.textAlign = 'center';
          ctx.fillText(`Gate ${idx + 1}`, 0, arrowDir * 26);
        }

        ctx.restore();
      });
    }

    // 8. Compass / North Arrow
    const compassX = canvasWidth - 50;
    const compassY = 50;
    ctx.save();
    ctx.translate(compassX, compassY);
    ctx.strokeStyle = 'rgba(148, 163, 184, 0.6)';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(0, 0, 20, 0, Math.PI * 2);
    ctx.stroke();

    // North Pointer
    ctx.beginPath();
    ctx.moveTo(0, -16);
    ctx.lineTo(6, 6);
    ctx.lineTo(0, 2);
    ctx.lineTo(-6, 6);
    ctx.closePath();
    ctx.fillStyle = 'var(--accent-rose)';
    ctx.fill();

    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 10px system-ui, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('N', 0, -22);
    ctx.restore();

    // Scale Bar Indicator at bottom left
    const barMetres = 50;
    const barWidthPx = barMetres * scale;
    const barX = 24;
    const barY = canvasHeight - 24;

    ctx.fillStyle = '#ffffff';
    ctx.font = '10px ui-monospace, monospace';
    ctx.fillText(`0`, barX, barY - 6);
    ctx.fillText(`${barMetres}m`, barX + barWidthPx - 14, barY - 6);

    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(barX, barY);
    ctx.lineTo(barX + barWidthPx, barY);
    ctx.moveTo(barX, barY - 4);
    ctx.lineTo(barX, barY + 4);
    ctx.moveTo(barX + barWidthPx, barY - 4);
    ctx.lineTo(barX + barWidthPx, barY + 4);
    ctx.stroke();
  }, [layout, showGrid, showLabels, showLayers, transform, buildingMap]);

  useEffect(() => {
    draw();
  }, [draw]);

  // Handle Canvas Resize
  useEffect(() => {
    const handleResize = () => {
      const canvas = canvasRef.current;
      const container = containerRef.current;
      if (!canvas || !container) return;

      canvas.width = container.clientWidth;
      canvas.height = container.clientHeight;
      draw();
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [draw]);

  // Mouse Wheel Zooming
  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const zoomFactor = e.deltaY < 0 ? 1.15 : 0.85;
    const newScale = Math.max(0.2, Math.min(10, transform.scale * zoomFactor));

    // Zoom centered around mouse pointer
    const newOffsetX = mouseX - (mouseX - transform.offsetX) * (newScale / transform.scale);
    const newOffsetY = mouseY - (mouseY - transform.offsetY) * (newScale / transform.scale);

    setTransform({
      scale: newScale,
      offsetX: newOffsetX,
      offsetY: newOffsetY,
    });
  };

  // Mouse Drag Panning
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - transform.offsetX, y: e.clientY - transform.offsetY });
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    if (isDragging) {
      setTransform((prev) => ({
        ...prev,
        offsetX: e.clientX - dragStart.x,
        offsetY: e.clientY - dragStart.y,
      }));
      return;
    }

    // Hover detection
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const siteHeight = layout.site.height;
    let found: HoveredBuildingInfo | null = null;

    for (const pos of layout.buildings) {
      const bMeta = buildingMap.get(pos.buildingId);
      if (!bMeta) continue;

      const centerX = transform.offsetX + (pos.x + bMeta.width / 2) * transform.scale;
      const centerY = transform.offsetY + (siteHeight - (pos.y + bMeta.depth / 2)) * transform.scale;
      const widthPx = bMeta.width * transform.scale;
      const depthPx = bMeta.depth * transform.scale;

      if (isPointInRotatedRect(mouseX, mouseY, centerX, centerY, widthPx, depthPx, pos.rotation)) {
        found = {
          building: bMeta,
          x: pos.x,
          y: pos.y,
          rotation: pos.rotation,
          screenX: mouseX + 16,
          screenY: mouseY + 16,
        };
        break;
      }
    }

    setHovered(found);
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  return (
    <div
      ref={containerRef}
      style={{
        width: '100%',
        height: '620px',
        position: 'relative',
        overflow: 'hidden',
        cursor: isDragging ? 'grabbing' : 'grab',
        backgroundColor: '#080c14',
      }}
    >
      <canvas
        ref={canvasRef}
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={() => {
          setIsDragging(false);
          setHovered(null);
        }}
        style={{ display: 'block', width: '100%', height: '100%' }}
      />

      {/* Floating Hover Tooltip */}
      {hovered && (
        <div
          style={{
            position: 'absolute',
            left: `${hovered.screenX}px`,
            top: `${hovered.screenY}px`,
            backgroundColor: 'rgba(15, 23, 42, 0.95)',
            border: '1px solid var(--border-focus)',
            borderRadius: 'var(--radius-md)',
            padding: '10px 14px',
            boxShadow: 'var(--shadow-lg)',
            pointerEvents: 'none',
            zIndex: 10,
            fontSize: '0.8125rem',
            maxWidth: '240px',
          }}
        >
          <div style={{ fontWeight: 700, color: '#ffffff', marginBottom: '4px' }}>
            {hovered.building.name}
          </div>
          <div style={{ color: 'var(--accent-cyan)', fontSize: '0.75rem', textTransform: 'uppercase', marginBottom: '6px' }}>
            {hovered.building.type} • {hovered.building.zone} zone
          </div>
          <div style={{ color: 'var(--text-muted)' }}>
            Dimensions: {hovered.building.width}m × {hovered.building.depth}m ({hovered.building.height}m high)
          </div>
          <div style={{ color: 'var(--text-muted)' }}>
            Floors: {hovered.building.floorCount} • Origin: ({hovered.x}m, {hovered.y}m)
          </div>
          {hovered.rotation !== 0 && (
            <div style={{ color: 'var(--accent-amber)', marginTop: '2px' }}>
              Rotation: {hovered.rotation}°
            </div>
          )}
        </div>
      )}
    </div>
  );
};
export default CampusCanvas2D;
