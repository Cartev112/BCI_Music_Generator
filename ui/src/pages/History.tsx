import React from 'react';
import { Container, Paper, Typography, Table, TableHead, TableRow, TableCell, TableBody, Button, Box } from '@mui/material';
import { useNavigate } from 'react-router-dom';

export function HistoryPage() {
  const navigate = useNavigate();
  const [sessions, setSessions] = React.useState<any[]>([]);
  React.useEffect(() => {
    window.electronAPI.getSessions().then(setSessions).catch(() => setSessions([]));
  }, []);
  return (
    <Container maxWidth="md" sx={{ py: 3 }}>
      <Paper sx={{ p: 2 }}>
        <Typography variant="h5" gutterBottom>
          Session History
        </Typography>
        <Table size="small">
          <TableHead>
            <TableRow>
              {['ID', 'Start', 'End', 'Preset', 'Key', 'BPM', 'Beats/Chord', 'Arp Mode', 'Arp Rate', 'Density', 'Adaptive'].map((h) => (
                <TableCell key={h}>{h}</TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {sessions.map((s, idx) => (
              <TableRow key={idx}>
                <TableCell>{s.id}</TableCell>
                <TableCell>{new Date(s.start * 1000).toLocaleString()}</TableCell>
                <TableCell>{s.end ? new Date(s.end * 1000).toLocaleString() : '-'}</TableCell>
                <TableCell>{s.preset}</TableCell>
                <TableCell>{s.key}</TableCell>
                <TableCell>{s.bpm}</TableCell>
                <TableCell>{s.beatsPerChord}</TableCell>
                <TableCell>{s.arpMode}</TableCell>
                <TableCell>{s.arpRate}</TableCell>
                <TableCell>{s.density}</TableCell>
                <TableCell>{s.adaptive ? 'Yes' : 'No'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <Box mt={2} display="flex" justifyContent="flex-end">
          <Button onClick={() => navigate('/')}>Back</Button>
        </Box>
      </Paper>
    </Container>
  );
}


