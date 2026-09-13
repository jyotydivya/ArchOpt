import type { Entrance } from './requirements.ts';

export interface LayoutMetrics {
  landUtilization: number;
  greenRatio: number;
  parkingRatio: number;
  accessibilityScore: number;
  roadEfficiency: number;
  constraintScore: number;
}

export interface LayoutSummary {
  id: number;
  rank: number;
  feasible: boolean;
  metrics: LayoutMetrics;
}

export interface LayoutListResponse {
  layouts: LayoutSummary[];
}

export interface SiteDimension {
  width: number;
  height: number;
}

export interface CandidateBuildingPosition {
  buildingId: number;
  x: number;
  y: number;
  rotation: number;
}

export interface LayoutDetail {
  id: number;
  rank: number;
  feasible: boolean;
  site: SiteDimension;
  buildings: CandidateBuildingPosition[];
  roads: any[];
  greenAreas: any[];
  parkingAreas: any[];
  entrances: Entrance[];
  metrics: LayoutMetrics;
}

export interface LayoutRunCreateRequest {
  candidateCount: number;
  topK: number;
  algorithm: string;
}

export interface LayoutRunCreateResponse {
  runId: number;
  status: string;
  layoutCount: number;
}

export interface LayoutSelectResponse {
  projectId: number;
  layoutId: number;
  status: string;
}
