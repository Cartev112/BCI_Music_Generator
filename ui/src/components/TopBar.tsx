import React from 'react';
import { AppBar, Toolbar, Typography, IconButton, Stack, Chip } from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import PauseIcon from '@mui/icons-material/Pause';
import StopIcon from '@mui/icons-material/Stop';

function LED({ on, label }: { on: boolean; label: string }) {
  return <Chip size="small" color={on ? 'success' : 'default'} label={label} sx={{ mr: 1 }} />;
}

export function TopBar() {
  const [running, setRunning] = React.useState(false);
  const [elapsed, setElapsed] = React.useState(0);
  const [status, setStatus] = React.useState({ board: false, classifier: false, osc: false });

  React.useEffect(() => {
    const id = setInterval(() => {
      if (running) setElapsed((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(id);
  }, [running]);

  React.useEffect(() => {
    ['board', 'classifier', 'osc'].forEach((k) =>
      window.electronAPI.onStatus(k as any, (v) => setStatus((s) => ({ ...s, [k]: v })))
    );
  }, []);

  function start() {
    window.electronAPI.sendSystem('start');
    setRunning(true);
    setElapsed(0);
  }
  function stop() {
    window.electronAPI.sendSystem('stop');
    setRunning(false);
  }
  function pause() {
    window.electronAPI.sendSystem('pause');
    setRunning(false);
  }

  const mm = Math.floor(elapsed / 60)
    .toString()
    .padStart(2, '0');
  const ss = (elapsed % 60).toString().padStart(2, '0');

  return (
    <AppBar position="static" color="default" elevation={0}>
      <Toolbar>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          BCI Music System
        </Typography>
        <Typography sx={{ ml: 2 }}>{mm}:{ss}</Typography>
        <Stack direction="row" spacing={1} sx={{ ml: 2 }}>
          <IconButton color="primary" onClick={start} size="small">
            <PlayArrowIcon />
          </IconButton>
          <IconButton color="primary" onClick={pause} size="small">
            <PauseIcon />
          </IconButton>
          <IconButton color="primary" onClick={stop} size="small">
            <StopIcon />
          </IconButton>
        </Stack>
        <Stack direction="row" sx={{ ml: 'auto' }}>
          <LED on={status.board} label="Board" />
          <LED on={status.classifier} label="Cls" />
          <LED on={status.osc} label="OSC" />
        </Stack>
      </Toolbar>
    </AppBar>
  );
}


