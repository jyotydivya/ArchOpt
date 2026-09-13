import React from 'react';
import { Outlet, useParams } from 'react-router-dom';
import { Navbar } from './Navbar.tsx';
import { Sidebar } from './Sidebar.tsx';
import { ProjectProvider } from '../../context/ProjectContext.tsx';

export const LayoutWrapper: React.FC = () => {
  const { projectId } = useParams<{ projectId?: string }>();

  return (
    <ProjectProvider>
      <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', backgroundColor: 'var(--bg-darker)' }}>
        <Navbar />
        <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
          {projectId && <Sidebar />}
          <main style={{ flex: 1, overflowY: 'auto', padding: '24px', position: 'relative' }}>
            <Outlet />
          </main>
        </div>
      </div>
    </ProjectProvider>
  );
};
export default LayoutWrapper;
