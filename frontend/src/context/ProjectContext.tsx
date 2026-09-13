import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import type { Project } from '../types/project.ts';
import { projectsApi } from '../api/projects.ts';
import { mockProject } from '../mocks/mockData.ts';

interface ProjectContextType {
  project: Project | null;
  loading: boolean;
  error: string | null;
  refreshProject: () => Promise<void>;
  setProjectDirectly: (project: Project) => void;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

export const ProjectProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { projectId } = useParams<{ projectId?: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchProject = useCallback(async () => {
    if (!projectId) {
      setProject(null);
      return;
    }

    const id = parseInt(projectId, 10);
    if (isNaN(id)) return;

    setLoading(true);
    setError(null);

    try {
      const data = await projectsApi.getProject(id);
      setProject(data);
    } catch (err: any) {
      // If offline/demo token, fallback to mock project
      const token = localStorage.getItem('archopt_token');
      if (token && token.includes('mock-demo')) {
        setProject({ ...mockProject, id });
      } else {
        setError(err.response?.data?.detail || 'Failed to load project details');
      }
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchProject();
  }, [fetchProject]);

  return (
    <ProjectContext.Provider
      value={{
        project,
        loading,
        error,
        refreshProject: fetchProject,
        setProjectDirectly: setProject,
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
};

export const useProject = (): ProjectContextType => {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
};

export default ProjectContext;
