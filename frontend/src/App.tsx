import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import Dashboard from './components/Dashboard';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-black">
        <Dashboard />
        <Toaster position="top-right" />
      </div>
    </QueryClientProvider>
  );
}

export default App;
