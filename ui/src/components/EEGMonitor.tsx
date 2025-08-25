import React from 'react';
import { LinearProgress, Stack, Typography, Box } from '@mui/material';

export function EEGMonitor() {
  const [quality, setQuality] = React.useState([1, 1, 1, 1]);
  const buffersRef = React.useRef<number[][]>([[], [], [], []]);

  React.useEffect(() => {
    window.electronAPI.onSample((arr) => {
      const next = buffersRef.current.map((buf, idx) => {
        const copy = buf.slice();
        const v = arr[idx] ?? 0;
        copy.push(v);
        if (copy.length > 500) copy.shift();
        return copy;
      });
      buffersRef.current = next;
      const q = next.map((buf) => (buf.length ? buf.filter((x) => Math.abs(x) <= 100).length / buf.length : 1));
      setQuality(q as any);
    });
  }, []);

  return (
    <Stack spacing={1}>
      {quality.map((q, i) => (
        <Box key={i}>
          <Typography variant="caption" color="text.secondary">
            Ch{i}
          </Typography>
          <LinearProgress variant="determinate" value={Math.round(q * 100)} sx={{ height: 10, borderRadius: 5 }} />
        </Box>
      ))}
    </Stack>
  );
}


