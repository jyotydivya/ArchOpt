export interface Constraint {
  id: number;
  type: string;
  sourceId?: number | null;
  targetId?: number | null;
  value?: number | null;
  operator?: string | null;
  priority?: string | null; // "hard" | "soft"
}

export interface ConstraintCreateRequest {
  type: string;
  sourceId?: number | null;
  targetId?: number | null;
  value?: number | null;
  operator?: string | null;
  priority?: string | null;
}

export interface ConstraintResponse extends Constraint {}

export interface ConstraintListResponse {
  constraints: Constraint[];
}
