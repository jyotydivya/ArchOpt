import React from 'react';
import { Link } from 'react-router-dom';

export const NotFoundPage: React.FC = () => {
  return (
    <div style={{ textAlign: 'center', padding: '80px 20px' }}>
      <h1 style={{ fontSize: '3rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>404</h1>
      <h2 style={{ fontSize: '1.5rem', marginBottom: '12px' }}>Page Not Found</h2>
      <p style={{ color: 'var(--text-muted)', marginBottom: '24px' }}>
        The campus planning resource or layout you are looking for does not exist.
      </p>
      <Link to="/projects" className="btn btn-primary">
        Back to Dashboard
      </Link>
    </div>
  );
};
export default NotFoundPage;
