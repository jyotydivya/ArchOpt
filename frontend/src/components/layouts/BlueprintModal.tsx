import React, { useState } from 'react';
import type { Blueprint } from '../../types/blueprint.ts';
import { Modal } from '../common/Modal.tsx';

interface BlueprintModalProps {
  isOpen: boolean;
  onClose: () => void;
  blueprint: Blueprint | null;
  loading: boolean;
}

export const BlueprintModal: React.FC<BlueprintModalProps> = ({
  isOpen,
  onClose,
  blueprint,
  loading,
}) => {
  const [copied, setCopied] = useState<boolean>(false);

  const jsonString = blueprint ? JSON.stringify(blueprint, null, 2) : '';

  const handleCopy = () => {
    if (!jsonString) return;
    navigator.clipboard.writeText(jsonString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    if (!blueprint) return;
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `blueprint-layout-${blueprint.layoutId}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Contract 9 Blender Blueprint — Layout #${blueprint?.layoutId || ''}`}
      maxWidth="780px"
      footer={
        <>
          <button type="button" onClick={onClose} className="btn btn-secondary">
            Close
          </button>
          <button
            type="button"
            onClick={handleCopy}
            className="btn btn-secondary"
            disabled={!blueprint}
          >
            {copied ? '✓ Copied!' : 'Copy JSON'}
          </button>
          <button
            type="button"
            onClick={handleDownload}
            className="btn btn-primary"
            disabled={!blueprint}
          >
            Download Blueprint (.json)
          </button>
        </>
      }
    >
      <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: '16px' }}>
        This Contract 9 Blueprint JSON feeds directly into Person 6's Blender 3D procedural script (<code>blender/generator.py</code>) to extrude buildings, carve road meshes, and render architectural presentations.
      </p>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px' }}>Synthesizing 3D Blueprint...</div>
      ) : (
        <pre
          style={{
            backgroundColor: '#080c14',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-md)',
            padding: '16px',
            fontSize: '0.75rem',
            fontFamily: 'var(--font-mono)',
            maxHeight: '400px',
            overflowY: 'auto',
            color: '#a5f3fc',
          }}
        >
          {jsonString}
        </pre>
      )}
    </Modal>
  );
};
export default BlueprintModal;
