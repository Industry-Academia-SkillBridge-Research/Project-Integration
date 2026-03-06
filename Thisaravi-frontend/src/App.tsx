import { Toaster } from '@/components/ui/sonner';
import { TooltipProvider } from '@/components/ui/tooltip';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from '@/context/AuthContext';
import AppLayout from '@/components/layout/AppLayout';
import ProtectedRoute from '@/components/ProtectedRoute';
import RoleProtectedRoute from '@/components/RoleProtectedRoute';
import AnalysisPage from '@/pages/AnalysisPage';
import FeedbackPage from '@/pages/FeedbackPage';
import EvolutionPage from '@/pages/EvolutionPage';
import SettingsPage from '@/pages/SettingsPage';
import NotFoundPage from '@/pages/NotFoundPage';
import LoginPage from '@/pages/LoginPage';
import RegisterPage from '@/pages/RegisterPage';
import ProfilePage from '@/pages/ProfilePage';
import HistoryPage from '@/pages/HistoryPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1 },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <BrowserRouter>
          <AuthProvider>
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />

              {/* Protected routes wrapped in AppLayout */}
              <Route
                element={
                  <ProtectedRoute>
                    <AppLayout />
                  </ProtectedRoute>
                }
              >
                <Route path="/" element={<RoleProtectedRoute allowedRoles={['student']}><AnalysisPage /></RoleProtectedRoute>} />
                <Route path="/history" element={<RoleProtectedRoute allowedRoles={['student']}><HistoryPage /></RoleProtectedRoute>} />
                <Route path="/feedback" element={<RoleProtectedRoute allowedRoles={['expert']}><FeedbackPage /></RoleProtectedRoute>} />
                <Route path="/evolution" element={<RoleProtectedRoute allowedRoles={['expert']}><EvolutionPage /></RoleProtectedRoute>} />
                <Route path="/settings" element={<RoleProtectedRoute allowedRoles={['expert']}><SettingsPage /></RoleProtectedRoute>} />
                <Route path="/profile" element={<ProfilePage />} />
                <Route path="*" element={<NotFoundPage />} />
              </Route>
            </Routes>
          </AuthProvider>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
