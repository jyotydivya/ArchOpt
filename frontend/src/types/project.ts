export interface Project {
  id: number;
  name: string;
  description?: string | null;
  status: string; // "DRAFT" | "SELECTED"
}

export interface ProjectCreateRequest {
  name: string;
  description?: string | null;
}

export interface ProjectUpdateRequest {
  name: string;
  description?: string | null;
}
