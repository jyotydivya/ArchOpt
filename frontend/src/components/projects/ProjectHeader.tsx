import React from 'react';
import type { Project } from '../../types/project.ts';

interface ProjectHeaderProps {
  project: Project | null;
  activeStepTitle?: string;
  children?: React.ReactNode;
}

export const ProjectHeader: React.FC<ProjectHeaderProps> = ({
  project,
  activeStepTitle,
  children,
}) => {
  if (!project) return null;

  const isSelected = project.status === 'SELECTED';

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: '24px',
        paddingBottom: '16px',
        borderBottom: '1px solid var(--border-color)',
      }}
    >
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '4px' }}>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0 }}>
            {project.name}
          </h1>
          <span className={`badge ${isSelected ? 'badge-selected' : 'badge-draft'}`}>
            {isSelected ? 'PLAN SELECTED' : 'DRAFT'}
          </span>
          <span style={{ fontSize: '0.8125rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
            ID: #{project.id}
          </span>
        </div>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', maxWidth: '650px' }}>
          {project.description || 'No description provided'}
        </p>
        {activeStepTitle && (
          <div style={{ marginTop: '8px', fontSize: '0.8125rem', color: 'var(--accent-cyan)', fontWeight: 600 }}>
            Workflow Stage: {activeStepTitle}
          </div>
        )}
      </div>

      {children && <div>{children}</div>}
    </div>
  );
};
export default ProjectHeader;
