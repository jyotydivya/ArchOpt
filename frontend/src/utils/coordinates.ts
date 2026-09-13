export interface ViewportTransform {
  scale: number;    // pixels per metre
  offsetX: number;  // canvas x offset
  offsetY: number;  // canvas y offset
}

export interface Point {
  x: number;
  y: number;
}

/**
 * Transforms campus coordinates (origin bottom-left, Y north)
 * into HTML5 canvas coordinates (origin top-left, Y down).
 */
export const toCanvasPoint = (
  x: number,
  y: number,
  siteHeight: number,
  transform: ViewportTransform
): Point => {
  return {
    x: transform.offsetX + x * transform.scale,
    y: transform.offsetY + (siteHeight - y) * transform.scale,
  };
};

/**
 * Computes optimal scale and offset to fit the campus site centered within the canvas viewport.
 */
export const calculateFitTransform = (
  siteWidth: number,
  siteHeight: number,
  canvasWidth: number,
  canvasHeight: number,
  padding: number = 40
): ViewportTransform => {
  const availableWidth = Math.max(100, canvasWidth - padding * 2);
  const availableHeight = Math.max(100, canvasHeight - padding * 2);

  const scaleX = availableWidth / siteWidth;
  const scaleY = availableHeight / siteHeight;
  const scale = Math.min(scaleX, scaleY);

  const offsetX = (canvasWidth - siteWidth * scale) / 2;
  const offsetY = (canvasHeight - siteHeight * scale) / 2;

  return { scale, offsetX, offsetY };
};

/**
 * Checks if a screen point (px, py) is inside a building rectangle with rotation.
 */
export const isPointInRotatedRect = (
  px: number,
  py: number,
  centerX: number,
  centerY: number,
  widthPx: number,
  depthPx: number,
  rotationDeg: number
): boolean => {
  const rad = (-rotationDeg * Math.PI) / 180;
  const cos = Math.cos(-rad);
  const sin = Math.sin(-rad);

  // Translate point to origin (centered at building)
  const dx = px - centerX;
  const dy = py - centerY;

  // Un-rotate point
  const unrotX = cos * dx - sin * dy;
  const unrotY = sin * dx + cos * dy;

  return (
    unrotX >= -widthPx / 2 &&
    unrotX <= widthPx / 2 &&
    unrotY >= -depthPx / 2 &&
    unrotY <= depthPx / 2
  );
};
