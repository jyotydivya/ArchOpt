import React, { useState } from 'react';
import type { Building } from '../../types/building.ts';
import type { ConstraintCreateRequest } from '../../types/constraint.ts';
import { validateConstraint } from '../../utils/validation.ts';

interface ConstraintFormProps {
  buildings: Building[];
  onSubmit: (data: ConstraintCreateRequest) => Promise<void>;
  onCancel: () => void;
  loading: boolean;
}

export const ConstraintForm: React.FC<ConstraintFormProps> = ({
  buildings,
  onSubmit,
  onCancel,
  loading,
}) => {
  const [type, setType] = useState('MIN_DISTANCE');
  const [sourceId, setSourceId] = useState<number>(buildings[0]?.id || 0);
  const [targetId, setTargetId] = useState<number>(buildings[1]?.id || buildings[0]?.id || 0);
  const [value, setValue] = useState<number>(50);
  const [operator, setOperator] = useState('>=');
  const [priority, setPriority] = useState('hard');
  const [error, setError] = useState<string | null>(null);

  const handleTypeChange = (newType: string) => {
    setType(newType);
    if (newType === 'SAME_ZONE') {
      setOperator('==');
      setValue(0);
    } else if (newType === 'MIN_DISTANCE') {
      setOperator('>=');
      setValue(50);
    } else if (newType === 'MAX_DISTANCE' || newType === 'NEAR') {
      setOperator('<=');
      setValue(60);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const payload: ConstraintCreateRequest = {
      type,
      sourceId: Number(sourceId),
      targetId: Number(targetId),
      value: Number(value),
      operator,
      priority,
    };

    const buildingIds = buildings.map((b) => b.id);
    const validationErr = validateConstraint(payload, buildingIds);
    if (validationErr) {
      setError(validationErr);
      return;
    }

    try {
      await onSubmit(payload);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to add constraint.');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {error && <div className="alert alert-error" style={{ marginBottom: '16px' }}>{error}</div>}

      <div className="form-group">
        <label className="form-label" htmlFor="constraint-type">Constraint Type *</label>
        <select
          id="constraint-type"
          className="form-select"
          value={type}
          onChange={(e) => handleTypeChange(e.target.value)}
        >
          <option value="MIN_DISTANCE">MIN_DISTANCE (Minimum separation distance)</option>
          <option value="MAX_DISTANCE">MAX_DISTANCE (Maximum distance / adjacency)</option>
          <option value="SAME_ZONE">SAME_ZONE (Must reside in identical zoning district)</option>
          <option value="NEAR">NEAR (Pedestrian accessibility proximity)</option>
          <option value="FAR">FAR (Noise/privacy buffer separation)</option>
          <option value="ROAD_ACCESS">ROAD_ACCESS (Direct arterial road accessibility)</option>
        </select>
      </div>

      <div className="grid-2">
        <div className="form-group">
          <label className="form-label" htmlFor="source-bldg">Source Entity *</label>
          <select
            id="source-bldg"
            className="form-select"
            value={sourceId}
            onChange={(e) => setSourceId(parseInt(e.target.value, 10))}
          >
            {buildings.map((b) => (
              <option key={b.id} value={b.id}>
                #{b.id} — {b.name} ({b.zone})
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="target-bldg">Target Entity *</label>
          <select
            id="target-bldg"
            className="form-select"
            value={targetId}
            onChange={(e) => setTargetId(parseInt(e.target.value, 10))}
          >
            {buildings.map((b) => (
              <option key={b.id} value={b.id}>
                #{b.id} — {b.name} ({b.zone})
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid-3">
        <div className="form-group">
          <label className="form-label" htmlFor="constraint-op">Operator *</label>
          <select
            id="constraint-op"
            className="form-select"
            value={operator}
            onChange={(e) => setOperator(e.target.value)}
          >
            <option value=">=">&gt;= (Greater Than or Equal)</option>
            <option value="<=">&lt;= (Less Than or Equal)</option>
            <option value="==">== (Exact Equality)</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="constraint-val">Value (metres) *</label>
          <input
            id="constraint-val"
            type="number"
            min="0"
            max="1000"
            step="1"
            className="form-input"
            value={value}
            onChange={(e) => setValue(parseFloat(e.target.value) || 0)}
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="constraint-prio">Enforcement Priority *</label>
          <select
            id="constraint-prio"
            className="form-select"
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
          >
            <option value="hard">Hard (Strict feasibility requirement)</option>
            <option value="soft">Soft (Optimization objective penalty)</option>
          </select>
        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '20px' }}>
        <button type="button" onClick={onCancel} className="btn btn-secondary" disabled={loading}>
          Cancel
        </button>
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Adding Constraint...' : 'Save Constraint'}
        </button>
      </div>
    </form>
  );
};
export default ConstraintForm;
