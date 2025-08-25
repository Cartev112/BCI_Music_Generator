import React from 'react';
import { Typography, Box } from '@mui/material';

type LogItem = { t: number; address: string; args: any[] };

export function ConsoleLog() {
  const [logs, setLogs] = React.useState<LogItem[]>([]);
  const endRef = React.useRef<HTMLDivElement | null>(null);

  React.useEffect(() => {
    window.electronAPI.on('console-log', (item: LogItem) => {
      setLogs((prev) => {
        const next = prev.length > 500 ? prev.slice(-400) : prev.slice();
        next.push(item);
        return next;
      });
    });
  }, []);

  React.useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs.length]);

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Console Log
      </Typography>
      <Box
        sx={{
          height: 180,
          overflow: 'auto',
          background: '#0c0d11',
          border: '1px solid #2a2f3a',
          p: 1,
          fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, Liberation Mono, monospace',
          fontSize: 12,
          color: '#d6dde8',
        }}
      >
        {logs.map((l, i) => (
          <div key={i}>
            {new Date(l.t).toLocaleTimeString()} {l.address} {JSON.stringify(l.args)}
          </div>
        ))}
        <div ref={endRef} />
      </Box>
    </Box>
  );
}


