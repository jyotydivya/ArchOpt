import type {
  Building,
  CampusRequirements,
  Constraint,
  LayoutDetail,
  LayoutSummary,
  Blueprint,
} from '../types/index.ts';
import mockLayoutsJson from './layouts.json';

export const mockProject = {
  id: 1,
  name: 'VIT Campus Expansion',
  description: 'AI-assisted architectural master plan for campus academic & residential zones.',
  status: 'DRAFT',
};

export const mockRequirements: CampusRequirements = {
  id: 1,
  projectId: 1,
  siteWidth: 300,
  siteHeight: 300,
  minGreenPercent: 25,
  minParkingPercent: 10,
  minRoadWidth: 8,
  minBuildingGap: 10,
  entrances: [
    { x: 150, y: 0, width: 12 },
    { x: 0, y: 150, width: 10 },
  ],
};

export const mockBuildings: Building[] = [
  { id: 1, projectId: 1, name: 'Academic Block A', type: 'academic', zone: 'academic', width: 60, depth: 40, height: 18, floorCount: 4, requiredCount: 1 },
  { id: 2, projectId: 1, name: 'Academic Block B', type: 'academic', zone: 'academic', width: 60, depth: 40, height: 18, floorCount: 4, requiredCount: 1 },
  { id: 3, projectId: 1, name: 'Central Library', type: 'library', zone: 'academic', width: 30, depth: 25, height: 12, floorCount: 3, requiredCount: 1 },
  { id: 4, projectId: 1, name: 'Administration Complex', type: 'admin', zone: 'admin', width: 40, depth: 30, height: 12, floorCount: 3, requiredCount: 1 },
  { id: 5, projectId: 1, name: 'Hostel Block A', type: 'hostel', zone: 'residential', width: 50, depth: 30, height: 15, floorCount: 5, requiredCount: 1 },
  { id: 6, projectId: 1, name: 'Hostel Block B', type: 'hostel', zone: 'residential', width: 50, depth: 30, height: 15, floorCount: 5, requiredCount: 1 },
  { id: 7, projectId: 1, name: 'Hostel Block C', type: 'hostel', zone: 'residential', width: 50, depth: 30, height: 15, floorCount: 5, requiredCount: 1 },
  { id: 8, projectId: 1, name: 'Indoor Sports Complex', type: 'sports', zone: 'sports', width: 80, depth: 60, height: 10, floorCount: 1, requiredCount: 1 },
];

export const mockConstraints: Constraint[] = [
  { id: 1, type: 'MIN_DISTANCE', sourceId: 1, targetId: 5, value: 80, operator: '>=', priority: 'hard' },
  { id: 2, type: 'SAME_ZONE', sourceId: 1, targetId: 2, value: 0, operator: '==', priority: 'soft' },
  { id: 3, type: 'NEAR', sourceId: 3, targetId: 1, value: 30, operator: '<=', priority: 'soft' },
];

export const mockLayoutsDetail: LayoutDetail[] = mockLayoutsJson as LayoutDetail[];

export const mockLayoutsSummary: LayoutSummary[] = mockLayoutsDetail.map((l) => ({
  id: l.id,
  rank: l.rank,
  feasible: l.feasible,
  metrics: l.metrics,
}));

export const mockBlueprint: Blueprint = {
  projectId: 1,
  layoutId: 101,
  site: { width: 300, height: 300 },
  buildings: [
    { id: 1, name: 'Academic Block A', type: 'academic', zone: 'academic', x: 45, y: 180, width: 60, depth: 40, height: 18, rotation: 0, floorCount: 4 },
    { id: 2, name: 'Academic Block B', type: 'academic', zone: 'academic', x: 135, y: 180, width: 60, depth: 40, height: 18, rotation: 0, floorCount: 4 },
    { id: 3, name: 'Central Library', type: 'library', zone: 'academic', x: 50, y: 100, width: 30, depth: 25, height: 12, rotation: 0, floorCount: 3 },
    { id: 4, name: 'Administration Complex', type: 'admin', zone: 'admin', x: 210, y: 180, width: 40, depth: 30, height: 12, rotation: 0, floorCount: 3 },
    { id: 5, name: 'Hostel Block A', type: 'hostel', zone: 'residential', x: 45, y: 25, width: 50, depth: 30, height: 15, rotation: 0, floorCount: 5 },
    { id: 6, name: 'Hostel Block B', type: 'hostel', zone: 'residential', x: 120, y: 25, width: 50, depth: 30, height: 15, rotation: 0, floorCount: 5 },
    { id: 7, name: 'Hostel Block C', type: 'hostel', zone: 'residential', x: 195, y: 25, width: 50, depth: 30, height: 15, rotation: 0, floorCount: 5 },
    { id: 8, name: 'Indoor Sports Complex', type: 'sports', zone: 'sports', x: 190, y: 95, width: 80, depth: 60, height: 10, rotation: 0, floorCount: 1 },
  ],
  roads: [
    { x: 0, y: 150, width: 10, length: 300, rotation: 0 },
    { x: 150, y: 0, width: 10, length: 300, rotation: 90 },
  ],
  greenAreas: [
    { x: 110, y: 95, width: 60, height: 50 },
  ],
  parkingAreas: [
    { x: 10, y: 10, width: 30, height: 40 },
    { x: 255, y: 10, width: 35, height: 40 },
  ],
  entrances: [
    { x: 150, y: 0, width: 12 },
    { x: 0, y: 150, width: 10 },
  ],
};
