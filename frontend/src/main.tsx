import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import RouterConfig from './RouterConfig.tsx';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <RouterConfig />
  </React.StrictMode>
);