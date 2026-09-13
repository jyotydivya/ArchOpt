export interface Entrance {
  x: number;
  y: number;
  width: number;
}

export interface CampusRequirements {
  id?: number;
  projectId: number;
  siteWidth: number;
  siteHeight: number;
  minGreenPercent: number;
  minParkingPercent: number;
  minRoadWidth: number;
  minBuildingGap: number;
  entrances: Entrance[];
}

export interface RequirementsSaveRequest {
  siteWidth: number;
  siteHeight: number;
  minGreenPercent: number;
  minParkingPercent: number;
  minRoadWidth: number;
  minBuildingGap: number;
  entrances: Entrance[];
}

export interface RequirementsResponse extends CampusRequirements {}
