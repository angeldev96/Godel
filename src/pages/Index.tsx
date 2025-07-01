
import { useAuth } from '@/hooks/useAuth';
import Auth from '@/components/Auth';
import Dashboard from '@/components/Dashboard';

function Index() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="flex items-center space-x-2 text-gray-500">
          <div className="w-5 h-5 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin" />
          <span>Loading...</span>
        </div>
      </div>
    );
  }

  return user ? <Dashboard /> : <Auth />;
}

export default Index;
