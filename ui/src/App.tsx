import React from 'react';
import { TopBar } from './components/TopBar';
import { ClassifierGauge } from './components/ClassifierGauge';
import { EEGMonitor } from './components/EEGMonitor';
import { EEGPlot } from './components/EEGPlot';
import { PSDPanel } from './components/PSDPanel';
import { DesignControls } from './components/DesignControls';
import { ConsoleLog } from './components/ConsoleLog';
import { Box, Container, Grid, Paper, Stack, Typography } from '@mui/material';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { HomePage } from './pages/Home';
import { SetupPage } from './pages/Setup';
import { SessionPage } from './pages/Session';
import { HistoryPage } from './pages/History';
import { SettingsPage } from './pages/Settings';
import ControlRoom from './pages/ControlRoom';


export function App() {
  const [prob, setProb] = React.useState(0);
  React.useEffect(() => {
    // Only set up electronAPI listeners if running in Electron context
    if (window.electronAPI && window.electronAPI.on) {
      window.electronAPI.on('bci-prob', (v) => setProb(Number(v) || 0));
    }
  }, []);

  const location = useLocation();
  const showTopBar = location.pathname.startsWith('/home');

  return (
    <Box display="flex" flexDirection="column" height="100%">
      
      <Routes>
        <Route path="/" element={<Navigate to="/home" replace />} />
        <Route path="/home" element={<HomePage />} />
        <Route path="/setup" element={<SetupPage />} />
        <Route path="/session" element={
          <Container maxWidth={false} sx={{ flex: 1, py: 2 }}>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, md: 8, lg: 9 }}>
                <Stack spacing={2}>
                  <Paper sx={{ p: 2 }}>
                    <Typography variant="h6" gutterBottom>
                      Classifier Probability
                    </Typography>
                    <ClassifierGauge value={prob} />
                  </Paper>
                  <Paper sx={{ p: 2 }}>
                    <Typography variant="h6" gutterBottom>
                      EEG Signal Quality
                    </Typography>
                    <EEGMonitor />
                  </Paper>
                  <Paper sx={{ p: 2 }}>
                    <Typography variant="h6" gutterBottom>
                      EEG Waveforms
                    </Typography>
                    <EEGPlot />
                  </Paper>
                  <Paper sx={{ p: 2 }}>
                    <PSDPanel />
                  </Paper>
                  <Paper sx={{ p: 2 }}>
                    <ConsoleLog />
                  </Paper>
                </Stack>
              </Grid>
              <Grid size={{ xs: 12, md: 4, lg: 3 }}>
                <Stack spacing={2}>
                  <Paper sx={{ p: 2 }}>
                    <DesignControls />
                  </Paper>
                </Stack>
              </Grid>
            </Grid>
          </Container>
        } />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/control" element={<ControlRoom />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Box>
  );
}