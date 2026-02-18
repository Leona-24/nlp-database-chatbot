import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Home from './pages/Home';
import { toast } from 'sonner';

function App() {
  const [user, setUser] = useState<{ token: string; username: string } | null>(null);

  useEffect(() => {
    // Check for authenticated user on mount
    const savedUser = localStorage.getItem('authUser');
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (e) {
        console.error("Failed to parse saved user");
        localStorage.removeItem('authUser');
      }
    }
  }, []);

  const handleLogin = (token: string, username: string) => {
    const userData = { token, username };
    setUser(userData);
    localStorage.setItem('authUser', JSON.stringify(userData));
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('authUser');
    localStorage.removeItem('dbConfig');
    toast.info('Logged out');
  };

  return (
    <Router>
      <Routes>
        <Route
          path="/login"
          element={user ? <Navigate to="/" replace /> : <Login onLogin={handleLogin} />}
        />
        <Route
          path="/"
          element={user ? <Home user={user} onLogout={handleLogout} /> : <Navigate to="/login" replace />}
        />
        {/* Catch all route - redirect to home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
