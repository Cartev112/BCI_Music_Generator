import React, { useEffect, useRef } from 'react';

interface EEGSimulatorProps {
  enabled: boolean;
  buffersRef: React.MutableRefObject<number[][]>;
  sampleCounterRef: React.MutableRefObject<number>;
  maxPoints: number;
}

export function EEGSimulator({ enabled, buffersRef, sampleCounterRef, maxPoints }: EEGSimulatorProps) {
  const enabledRef = useRef(false);

  // Keep ref in sync
  useEffect(() => { 
    enabledRef.current = enabled; 
  }, [enabled]);

  // EEG simulator
  useEffect(() => {
    if (!enabled) return;
    
    let t = 0;
    const dt = 1 / 50; // 50 Hz
    const id = setInterval(() => {
      t += dt;
      const ch1 = Math.sin(2 * Math.PI * 8 * t) * 8 + (Math.random() - 0.5) * 1.0;
      const ch2 = Math.sin(2 * Math.PI * 12 * t + 0.4) * 6 + (Math.random() - 0.5) * 1.0;
      const ch3 = Math.sin(2 * Math.PI * 18 * t + 1.2) * 5 + (Math.random() - 0.5) * 1.0;
      const ch4 = Math.sin(2 * Math.PI * 24 * t + 2.1) * 4 + (Math.random() - 0.5) * 1.0;
      const arr = [ch1, ch2, ch3, ch4];
      const b = buffersRef.current;
      for (let i = 0; i < 4; i++) {
        b[i].push(arr[i]);
        if (b[i].length > maxPoints) b[i].shift();
      }
      sampleCounterRef.current += 1;
    }, 20);
    
    return () => clearInterval(id);
  }, [enabled, buffersRef, sampleCounterRef, maxPoints]);

  // This component doesn't render anything - it's just logic
  return null;
}

