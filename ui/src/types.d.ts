export {};

declare global {
  interface Window {
    electronAPI?: {
      sendOSC: (channel: string, args: any) => void;
      on: (channel: string, cb: (data: any) => void) => void;
      onSample: (cb: (arr: number[]) => void) => void;
      onMarker: (cb: (label: string) => void) => void;
      sendSystem: (cmd: 'start' | 'stop' | 'pause') => void;
      onStatus: (key: 'board' | 'classifier' | 'osc', cb: (val: boolean) => void) => void;
      getSessions: () => Promise<any[]>;
    };
  }
}




