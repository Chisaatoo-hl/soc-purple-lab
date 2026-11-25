import React from 'react'
import ReactDOM from 'react-dom/client'
import { RouterProvider, createBrowserRouter, Navigate } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from './lib/queryClient'
import Layout from './routes/Layout'
import AlertsPage from './routes/AlertsPage'
import AlertDetailPage from './routes/AlertDetailPage'
import StatsPage from './routes/StatsPage'
import './index.css'

const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <Navigate to="/alerts" replace /> },
      { path: 'alerts', element: <AlertsPage /> },
      { path: 'alerts/:id', element: <AlertDetailPage /> },
      { path: 'stats', element: <StatsPage /> },
    ],
  },
])

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </React.StrictMode>,
)
