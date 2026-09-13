import type { RequirementsSaveRequest } from '../types/requirements.ts';
import type { BuildingCreateRequest } from '../types/building.ts';
import type { ConstraintCreateRequest } from '../types/constraint.ts';

export const validateRequirements = (data: RequirementsSaveRequest): string | null => {
  if (data.siteWidth <= 0 || data.siteHeight <= 0) {
    return 'Site dimensions must be positive numbers.';
  }
  if (data.minGreenPercent < 0 || data.minGreenPercent > 100) {
    return 'Minimum green percentage must be between 0 and 100%.';
  }
  if (data.minParkingPercent < 0 || data.minParkingPercent > 100) {
    return 'Minimum parking percentage must be between 0 and 100%.';
  }
  if (data.minGreenPercent + data.minParkingPercent > 100) {
    return 'The sum of green and parking percentages cannot exceed 100%.';
  }
  if (data.minRoadWidth <= 0) {
    return 'Minimum road width must be greater than 0.';
  }
  if (data.minBuildingGap <= 0) {
    return 'Minimum building gap must be greater than 0.';
  }

  for (let i = 0; i < data.entrances.length; i++) {
    const e = data.entrances[i];
    if (e.width <= 0) {
      return `Entrance #${i + 1} width must be greater than 0.`;
    }
    if (e.x < 0 || e.x > data.siteWidth || e.y < 0 || e.y > data.siteHeight) {
      return `Entrance #${i + 1} coordinate (${e.x}, ${e.y}) is outside the campus boundaries (${data.siteWidth} x ${data.siteHeight}).`;
    }
  }

  return null;
};

export const validateBuilding = (data: BuildingCreateRequest): string | null => {
  if (!data.name.trim()) {
    return 'Building name is required.';
  }
  if (data.width <= 0 || data.depth <= 0 || data.height <= 0) {
    return 'Building dimensions (width, depth, height) must be positive.';
  }
  if (data.floorCount < 1) {
    return 'Floor count must be at least 1.';
  }
  if (data.requiredCount < 1) {
    return 'Required count must be at least 1.';
  }
  return null;
};

export const validateConstraint = (
  data: ConstraintCreateRequest,
  availableBuildingIds: number[]
): string | null => {
  if (!data.type) {
    return 'Constraint type is required.';
  }
  if (data.sourceId === null || data.sourceId === undefined) {
    return 'Source building must be selected.';
  }
  if (data.targetId === null || data.targetId === undefined) {
    return 'Target building must be selected.';
  }
  if (data.sourceId === data.targetId) {
    return 'Source building and target building must be different.';
  }
  if (!availableBuildingIds.includes(data.sourceId) || !availableBuildingIds.includes(data.targetId)) {
    return 'Selected building does not exist in this project.';
  }
  return null;
};
