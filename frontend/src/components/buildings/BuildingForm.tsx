import React, { useState } from 'react';
import type { BuildingCreateRequest } from '../../types/building.ts';
import { validateBuilding } from '../../utils/validation.ts';

interface BuildingFormProps {
  onSubmit: (data: BuildingCreateRequest) => Promise<void>;
  onCancel: () => void;
  loading: boolean;
}

export const BuildingForm: React.FC<BuildingFormProps> = ({ onSubmit, onCancel, loading }) => {
  const [name, setName] = useState('');
  const [type, setType] = useState('academic');
  const [zone, setZone] = useState('academic');
  const [width, setWidth] = useState<number>(60);
  const [depth, setDepth] = useState<number>(40);
  const [height, setHeight] = useState<number>(18);
  const [floorCount, setFloorCount] = useState<number>(4);
  const [requiredCount, setRequiredCount] = useState<number>(1);
  const [error, setError] = useState<string | null>(null);

  // Auto-align default zone when type changes
  const handleTypeChange = (newType: string) => {
    setType(newType);
    if (newType === 'academic' || newType === 'library') {
      setZone('academic');
    } else if (newType === 'hostel') {
      setZone('residential');
    } else if (newType === 'admin') {
      setZone('admin');
    } else if (newType === 'sports') {
      setZone('sports');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const payload: BuildingCreateRequest = {
      name: name.trim(),
      type,
      zone,
      width: Number(width),
      depth: Number(depth),
      height: Number(height),
      floorCount: Number(floorCount),
      requiredCount: Number(requiredCount),
    };

    const validationErr = validateBuilding(payload);
    if (validationErr) {
      setError(validationErr);
      return;
    }

    try {
      await onSubmit(payload);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to add building.');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {error && <div className="alert alert-error" style={{ marginBottom: '16px' }}>{error}</div>}

      <div className="form-group">
        <label className="form-label" htmlFor="building-name">Building Name *</label>
        <input
          id="building-name"
          type="text"
          className="form-input"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Academic Block A"
          required
          autoFocus
        />
      </div>

      <div className="grid-2">
        <div className="form-group">
          <label className="form-label" htmlFor="building-type">Building Type *</label>
          <select
            id="building-type"
            className="form-select"
            value={type}
            onChange={(e) => handleTypeChange(e.target.value)}
          >
            <option value="academic">Academic Block</option>
            <option value="library">Central Library</option>
            <option value="hostel">Residential Hostel</option>
            <option value="admin">Administration Building</option>
            <option value="sports">Sports Complex</option>
            <option value="parking">Structured Parking</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="building-zone">Zoning District *</label>
          <select
            id="building-zone"
            className="form-select"
            value={zone}
            onChange={(e) => setZone(e.target.value)}
          >
            <option value="academic">Academic Zone</option>
            <option value="residential">Residential Zone</option>
            <option value="sports">Sports Zone</option>
            <option value="admin">Administrative Zone</option>
          </select>
        </div>
      </div>

      <div className="grid-3">
        <div className="form-group">
          <label className="form-label" htmlFor="building-width">Width (m) *</label>
          <input
            id="building-width"
            type="number"
            min="5"
            max="300"
            step="1"
            className="form-input"
            value={width}
            onChange={(e) => setWidth(parseFloat(e.target.value) || 0)}
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="building-depth">Depth (m) *</label>
          <input
            id="building-depth"
            type="number"
            min="5"
            max="300"
            step="1"
            className="form-input"
            value={depth}
            onChange={(e) => setDepth(parseFloat(e.target.value) || 0)}
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="building-height">Height (m) *</label>
          <input
            id="building-height"
            type="number"
            min="3"
            max="120"
            step="0.5"
            className="form-input"
            value={height}
            onChange={(e) => setHeight(parseFloat(e.target.value) || 0)}
            required
          />
        </div>
      </div>

      <div className="grid-2">
        <div className="form-group">
          <label className="form-label" htmlFor="building-floors">Floor Count *</label>
          <input
            id="building-floors"
            type="number"
            min="1"
            max="40"
            step="1"
            className="form-input"
            value={floorCount}
            onChange={(e) => setFloorCount(parseInt(e.target.value, 10) || 1)}
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="building-count">Required Count *</label>
          <input
            id="building-count"
            type="number"
            min="1"
            max="20"
            step="1"
            className="form-input"
            value={requiredCount}
            onChange={(e) => setRequiredCount(parseInt(e.target.value, 10) || 1)}
            required
          />
        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '20px' }}>
        <button type="button" onClick={onCancel} className="btn btn-secondary" disabled={loading}>
          Cancel
        </button>
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Adding Building...' : 'Add to Inventory'}
        </button>
      </div>
    </form>
  );
};
export default BuildingForm;
