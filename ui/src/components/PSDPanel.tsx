import React from 'react';

export function PSDPanel() {
  const [alpha, setAlpha] = React.useState(0);
  const [beta, setBeta] = React.useState(0);
  const buffersRef = React.useRef<number[]>([]);
  const workerRef = React.useRef<Worker | null>(null);

  React.useEffect(() => {
    workerRef.current = new Worker(new URL('../workers/psdWorker.ts', import.meta.url), { type: 'module' });
    workerRef.current.onmessage = (ev: MessageEvent<{ type: 'psd'; alpha: number; beta: number }>) => {
      const { alpha, beta } = ev.data;
      setAlpha(alpha);
      setBeta(beta);
    };

    const onSample = (arr: number[]) => {
      const ch0 = arr[0] ?? 0;
      buffersRef.current.push(ch0);
      if (buffersRef.current.length > 512) buffersRef.current.shift();
    };
    window.electronAPI.onSample(onSample);

    const id = setInterval(() => {
      if (buffersRef.current.length >= 256 && workerRef.current) {
        workerRef.current.postMessage({ type: 'psd', sampleRate: 250, channel: buffersRef.current.slice(-512) });
      }
    }, 1000);

    return () => {
      clearInterval(id);
      workerRef.current?.terminate();
      workerRef.current = null;
    };
  }, []);

  return (
    <div>
      <h4>PSD (Ch0)</h4>
      <div style={{ display: 'flex', gap: 12 }}>
        <div>
          <div style={{ color: '#aaa' }}>Alpha</div>
          <div>{alpha.toFixed(2)}</div>
        </div>
        <div>
          <div style={{ color: '#aaa' }}>Beta</div>
          <div>{beta.toFixed(2)}</div>
        </div>
      </div>
    </div>
  );
}






