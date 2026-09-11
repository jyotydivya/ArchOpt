/**
 * contracts/layout.ts
 * ====================
 * TypeScript interface contracts for the AI Campus Planner project.
 * Single source of truth — DO NOT modify without team approval.
 *
 * Coordinate system: origin = bottom-left, X = east, Y = north, metres.
 * Rotation = degrees, counter-clockwise from east.
 */

// ── Contract 1: Building ────────────────────────────────────────────────────
export interface Building {
  id: number;
  name: string;
  type: string;           // "academic" | "library" | "hostel" | "admin" | "sports" | "parking"
  zone: string;           // "academic" | "residential" | "sports" | "admin"
  width: number;          // metres
  depth: number;          // metres
  height: number;         // metres
  floorCount: number;
  requiredCount: number;
}

// ── Contract 2: Campus Requirements ─────────────────────────────────────────
export interface CampusRequirements {
  projectId: number;
  siteWidth: number;
  siteHeight: number;
  minGreenPercent: number;    // 0–100
  minParkingPercent: number;  // 0–100
  minRoadWidth: number;       // metres
  minBuildingGap: number;     // metres
  entrances: Entrance[];
}

// ── Contract 3: Entrance ─────────────────────────────────────────────────────
export interface Entrance {
  x: number;
  y: number;
  width: number;
}

// ── Contract 4: Spatial Relationship ────────────────────────────────────────
export interface SpatialRelationship {
  sourceId: number;
  targetId: number;
  relation:
    | "NEAR"
    | "FAR"
    | "SAME_ZONE"
    | "ACCESSIBLE_FROM"
    | "ROAD_ACCESS";
  weight: number;
}

// ── Contract 5: Campus Graph ─────────────────────────────────────────────────
export interface CampusGraph {
  nodeFeatures: number[][];   // [N, F]
  edgeIndex: number[][];      // [2, E]
  edgeFeatures: number[][];   // [E, G]
}

// ── Contract 6: Candidate Layout ─────────────────────────────────────────────
export interface CandidateBuilding {
  buildingId: number;
  x: number;
  y: number;
  rotation: number;
  width?: number;
  depth?: number;
  zone?: string;
  name?: string;
  type?: string;
  height?: number;
  floorCount?: number;
}

export interface CandidateLayout {
  candidateId: string;
  siteWidth: number;
  siteHeight: number;
  buildings: CandidateBuilding[];
}

// ── Contract 7: Validation Result ────────────────────────────────────────────
export interface Violation {
  type: string;
  buildingIds: number[];
  message: string;
  severity: "hard" | "soft";
}

export interface ValidationResult {
  feasible: boolean;
  violations: Violation[];
  constraintScore: number;
}

// ── Contract 8: Ranked Layout ────────────────────────────────────────────────
export interface LayoutMetrics {
  landUtilization: number;
  greenRatio: number;
  parkingRatio: number;
  accessibilityScore: number;
  roadEfficiency: number;
  constraintScore: number;
}

export interface RankedLayout {
  candidateId: string;
  rank: number;
  feasible: boolean;
  buildings: CandidateBuilding[];
  metrics: LayoutMetrics;
  siteWidth: number;
  siteHeight: number;
}

// ── Contract 9: Blueprint ────────────────────────────────────────────────────
export interface BlueprintBuilding {
  id: number;
  name: string;
  type: string;
  zone: string;
  x: number;
  y: number;
  width: number;
  depth: number;
  height: number;
  rotation: number;
  floorCount: number;
}

export interface Road {
  x: number;
  y: number;
  width: number;
  length: number;
  rotation: number;
}

export interface Area {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface Blueprint {
  projectId: number;
  layoutId: number;
  site: { width: number; height: number };
  buildings: BlueprintBuilding[];
  roads: Road[];
  greenAreas: Area[];
  parkingAreas: Area[];
  entrances: Entrance[];
}
