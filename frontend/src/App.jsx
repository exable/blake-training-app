import React, { useEffect, useState } from 'react';
import { Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { isAuthed } from './lib/api.js';
import Layout from './components/Layout.jsx';
import Login from './pages/Login.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Workout from './pages/Workout.jsx';
import Nutrition from './pages/Nutrition.jsx';
import Checkins from './pages/Checkins.jsx';
import Progress from './pages/Progress.jsx';
import Chat from './pages/Chat.jsx';
import Settings from './pages/Settings.jsx';

function Protected({ children }) {
  const loc = useLocation();
  if (!isAuthed()) return <Navigate to="/login" state={{ from: loc }} replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <Protected>
            <Layout />
          </Protected>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="workout" element={<Workout />} />
        <Route path="nutrition" element={<Nutrition />} />
        <Route path="checkins" element={<Checkins />} />
        <Route path="progress" element={<Progress />} />
        <Route path="chat" element={<Chat />} />
        <Route path="settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
