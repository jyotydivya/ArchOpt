export interface Building {
  id: number;
  projectId: number;
  name: string;
  type: string;
  zone: string;
  width: number;
  depth: number;
  height: number;
  floorCount: number;
  requiredCount: number;
}

export interface BuildingCreateRequest {
  name: string;
  type: string;
  zone: string;
  width: number;
  depth: number;
  height: number;
  floorCount: number;
  requiredCount: number;
}

export interface BuildingResponse extends Building {}

export interface BuildingListResponse {
  buildings: Building[];
}
