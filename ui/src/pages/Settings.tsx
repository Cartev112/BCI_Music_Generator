import React from 'react';
import { Container, Paper, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';

export function SettingsPage() {
  const navigate = useNavigate();
  return (
    <Container maxWidth="sm" sx={{ py: 3 }}>
      <Paper sx={{ p: 2 }}>
        <Typography variant="h5" gutterBottom>
          Settings
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Placeholder for UI preferences and connection options.
        </Typography>
      </Paper>
    </Container>
  );
}






