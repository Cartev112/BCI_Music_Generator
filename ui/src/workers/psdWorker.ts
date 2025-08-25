// Web Worker for PSD computation. Uses simple window and real FFT via naive DFT fallback to avoid heavy deps initially.

export type PSDRequest = {
  type: 'psd';
  sampleRate: number;
  channel: number[];
};

export type PSDResponse = {
  type: 'psd';
  alpha: number;
  beta: number;
};

function hammingWindow(n: number, i: number): number {
  return 0.54 - 0.46 * Math.cos((2 * Math.PI * i) / (n - 1));
}

// Naive DFT (O(N^2)) for N ~ 512 is acceptable in worker; can swap to proper FFT later.
function dftRealMag2(signal: number[], sampleRate: number): { freqs: number[]; mags: number[] } {
  const N = signal.length;
  const mags: number[] = [];
  const freqs: number[] = [];
  for (let k = 0; k < N / 2; k++) {
    let re = 0;
    let im = 0;
    for (let n = 0; n < N; n++) {
      const angle = (-2 * Math.PI * k * n) / N;
      re += signal[n] * Math.cos(angle);
      im += signal[n] * Math.sin(angle);
    }
    mags.push(re * re + im * im);
    freqs.push((k * sampleRate) / N);
  }
  return { freqs, mags };
}

function bandPower(freqs: number[], mags: number[], lo: number, hi: number): number {
  let sum = 0;
  let count = 0;
  for (let i = 0; i < freqs.length; i++) {
    if (freqs[i] >= lo && freqs[i] <= hi) {
      sum += mags[i];
      count++;
    }
  }
  return count ? sum / count : 0;
}

self.onmessage = (ev: MessageEvent<PSDRequest>) => {
  const msg = ev.data;
  if (msg.type === 'psd') {
    const N = msg.channel.length;
    if (N < 64) return; // need enough samples
    const windowed = new Array(N);
    for (let i = 0; i < N; i++) windowed[i] = msg.channel[i] * hammingWindow(N, i);
    const { freqs, mags } = dftRealMag2(windowed, msg.sampleRate);
    const alpha = bandPower(freqs, mags, 8, 13);
    const beta = bandPower(freqs, mags, 13, 30);
    const res: PSDResponse = { type: 'psd', alpha, beta };
    (self as any).postMessage(res);
  }
};









