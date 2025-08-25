const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  sendOSC: (channel, args) => ipcRenderer.send(channel, args),
  on: (channel, callback) => ipcRenderer.on(channel, (_event, data) => callback(data)),
  onSample: (callback)=> ipcRenderer.on('eeg-sample',(_e,data)=>callback(data)),
  onMarker: (callback)=> ipcRenderer.on('eeg-marker',(_e,data)=>callback(data)),
  sendSystem:(cmd)=>ipcRenderer.send(`system-${cmd}`),
  onStatus:(key,cb)=>ipcRenderer.on(`status-${key}`,(_e,val)=>cb(val)),
  getSessions: ()=>ipcRenderer.invoke('list-sessions'),
}); 