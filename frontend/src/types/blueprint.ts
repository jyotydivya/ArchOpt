import type { Entrance } from './requirements.ts';
import type { SiteDimension } from './layout.ts';

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
  site: SiteDimension;
  buildings: BlueprintBuilding[];
  roads: Road[];
  greenAreas: Area[];
  parkingAreas: Area[];
  entrances: Entrance[];
}
