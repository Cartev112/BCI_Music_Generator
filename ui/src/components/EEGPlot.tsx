import React from 'react';
import uPlot from 'uplot';
import 'uplot/dist/uPlot.min.css';

type EEGPlotProps = {
  numChannels?: number;
  maxPoints?: number;
};

export function EEGPlot({ numChannels = 4, maxPoints = 500 }: EEGPlotProps) {
  const containerRef = React.useRef<HTMLDivElement | null>(null);
  const plotRef = React.useRef<uPlot | null>(null);
  const seriesRef = React.useRef<number[][]>([]);
  const xRef = React.useRef<number[]>([]);

  React.useEffect(() => {
    // Initialize data arrays
    xRef.current = Array.from({ length: maxPoints }, (_, i) => i);
    seriesRef.current = Array.from({ length: numChannels }, () => Array(maxPoints).fill(0));

    const opts: uPlot.Options = {
      width: 650,
      height: 280,
      scales: { y: { auto: true } },
      axes: [
        { show: false },
        { show: true, label: 'µV' },
      ],
      legend: { show: true },
      series: [
        {},
        { label: 'Ch0', stroke: '#4caf50' },
        { label: 'Ch1', stroke: '#2196f3' },
        { label: 'Ch2', stroke: '#ff9800' },
        { label: 'Ch3', stroke: '#e91e63' },
      ].slice(0, numChannels + 1),
    };

    if (containerRef.current) {
      const initialAligned = [
        Float64Array.from(xRef.current),
        ...seriesRef.current.map((s) => Float64Array.from(s)),
      ] as uPlot.AlignedData;
      plotRef.current = new uPlot(opts, initialAligned, containerRef.current);
    }

    let rafId = 0;
    const onSample = (arr: number[]) => {
      for (let ch = 0; ch < numChannels; ch += 1) {
        const s = seriesRef.current[ch];
        s.push(arr[ch] ?? 0);
        if (s.length > maxPoints) s.shift();
      }
      // request animation frame to update
      if (!rafId) {
        rafId = requestAnimationFrame(() => {
          rafId = 0;
          if (plotRef.current) {
            const aligned = [
              Float64Array.from(xRef.current),
              ...seriesRef.current.map((s) => Float64Array.from(s)),
            ] as uPlot.AlignedData;
            plotRef.current.setData(aligned);
          }
        });
      }
    };

    window.electronAPI.onSample(onSample);

    return () => {
      if (plotRef.current) {
        plotRef.current.destroy();
        plotRef.current = null;
      }
    };
  }, [numChannels, maxPoints]);

  return (
    <div>
      <div style={{ marginBottom: 6 }}>EEG Waveforms</div>
      <div ref={containerRef} />
    </div>
  );
}


