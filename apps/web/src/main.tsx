import React from 'react';
import {createRoot} from 'react-dom/client';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {BrowserRouter} from 'react-router-dom';
import {App} from './App';
import './styles.css';
import {initAppearance} from './theme/store';
initAppearance();
const DevTools = import.meta.env.DEV && import.meta.env.VITE_ENABLE_AGENTATION === 'true'
  ? React.lazy(() => import('./dev/DevTools')) : null;
createRoot(document.getElementById('root')!).render(<React.StrictMode><QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><BrowserRouter><App/></BrowserRouter></QueryClientProvider>{DevTools && <React.Suspense fallback={null}><DevTools/></React.Suspense>}</React.StrictMode>);
