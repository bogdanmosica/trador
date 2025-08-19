import { RouterProvider } from '@tanstack/react-router';
import { router } from '../router'; // Import the router

// This component will be used in main.tsx
export function AppRouter() {
  return <RouterProvider router={router} />;
}

