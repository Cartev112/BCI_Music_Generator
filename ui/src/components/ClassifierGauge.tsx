import React from 'react';
import { LinearProgress, Typography, Box } from '@mui/material';

export function ClassifierGauge({ value }: { value: number }) {
  const clamped = Math.max(0, Math.min(1, isFinite(value) ? value : 0));
  const pct = Math.round(clamped * 100);
  return (
    <Box>
      <LinearProgress variant="determinate" value={pct} sx={{ height: 12, borderRadius: 6 }} />
      <Typography variant="body2" sx={{ mt: 1, color: 'text.secondary' }}>
        {clamped.toFixed(2)}
      </Typography>
    </Box>
  );
}


