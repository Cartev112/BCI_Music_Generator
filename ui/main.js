const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const osc = require('osc');

// ------------------ OSC Setup ------------------
const IN_PORT = 9000;  // from classifier/controller
const OUT_PORT = 9001; // to controller (music)
const OUT_ADDR = '127.0.0.1';

const udpIn = new osc.UDPPort({ localAddress: '0.0.0.0', localPort: IN_PORT });
const udpOut = new osc.UDPPort({ remoteAddress: OUT_ADDR, remotePort: OUT_PORT });

udpIn.open();
udpOut.open();

let mainWin = null;

// ------------------ Session Logging ------------------
const sessionsFile = () => path.join(app.getPath('userData'), 'sessions.json');
function loadSessions() {
  try {
    const p = sessionsFile();
    if (fs.existsSync(p)) {
      return JSON.parse(fs.readFileSync(p, 'utf-8'));
    }
  } catch {}
  return [];
}
function saveSessions(arr) {
  try {
    fs.mkdirSync(app.getPath('userData'), { recursive: true });
    fs.writeFileSync(sessionsFile(), JSON.stringify(arr, null, 2), 'utf-8');
  } catch {}
}
let sessions = loadSessions();
let currentSettings = { preset: 'consonant', key: 'C', bpm: 100, beatsPerChord: 2, arpMode: 'off', arpRate: 1, density: 0.5, adaptive: false };
let activeSession = null;

udpIn.on('message', (msg) => {
  if (!mainWin) return;
  if (msg.address === '/bci/prob_img' && msg.args.length) {
    mainWin.webContents.send('bci-prob', msg.args[0]);
  }
  else if (msg.address === '/bci/state' && msg.args.length) {
    mainWin.webContents.send('bci-state', msg.args[0]);
  }
  else if(msg.address === '/eeg' && msg.args.length>=4){
    mainWin.webContents.send('eeg-sample', msg.args.slice(0,4));
  }
  else if(msg.address === '/marker' && msg.args.length){
    mainWin.webContents.send('eeg-marker', msg.args[0]);
  }
  else if(msg.address.startsWith('/status/')){
    const key=msg.address.split('/')[2];
    if(['board','classifier','osc'].includes(key))
      mainWin.webContents.send('status-'+key, !!msg.args[0]);
  }
  // Forward all incoming OSC messages to console log pane (throttled by renderer if needed)
  const ts = Date.now();
  try {
    mainWin.webContents.send('console-log', { t: ts, address: msg.address, args: msg.args || [] });
  } catch (_) {}
  // Forward other messages as needed
});

function createWindow() {
  mainWin = new BrowserWindow({
    width: 1280,
    height: 720,
    show: false, // Don't show until ready
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  // Maximize window when ready
  mainWin.once('ready-to-show', () => {
    mainWin.maximize();
    mainWin.show();
  });

  const devServer = process.env.UI_DEV_SERVER;
  if (devServer) {
    mainWin.loadURL(devServer);
  } else {
    // Load built renderer (Vite output)
    const distIndex = path.join(__dirname, 'dist', 'index.html');
    mainWin.loadFile(distIndex);
  }
}

app.whenReady().then(() => {
  createWindow();

  // IPC from renderer to send OSC
  ipcMain.on('music-preset', (_evt, preset) => {
    udpOut.send({ address: '/music/preset', args: [preset] });
  });

  ipcMain.on('rhythm-arp_mode', (_evt, mode) => {
    udpOut.send({ address: '/rhythm/arp_mode', args: [mode] });
  });

  ipcMain.on('music-tempo', (_e,v)=>{ currentSettings.bpm = v; udpOut.send({address:'/music/tempo',args:[v]}); });
  ipcMain.on('music-beats_per_chord', (_e,v)=>{ currentSettings.beatsPerChord = v; udpOut.send({address:'/music/beats_per_chord',args:[v]}); });
  ipcMain.on('music-adaptive', (_e,v)=>{ currentSettings.adaptive = !!v; udpOut.send({address:'/music/adaptive',args:[v]}); });
  ipcMain.on('music-key', (_e,v)=>{ currentSettings.key = v; udpOut.send({address:'/music/key',args:[v]}); });
  ipcMain.on('rhythm-arp_rate', (_e,v)=>{ currentSettings.arpRate = v; udpOut.send({address:'/rhythm/arp_rate',args:[v]}); });
  ipcMain.on('rhythm-density', (_e,v)=>{ currentSettings.density = v; udpOut.send({address:'/rhythm/density',args:[v]}); });
  ipcMain.on('layer-pad', (_e,v)=>udpOut.send({address:'/layer/pad',args:[v]}));
  ipcMain.on('layer-arp', (_e,v)=>udpOut.send({address:'/layer/arp',args:[v]}));
  ipcMain.on('layer-drums', (_e,v)=>udpOut.send({address:'/layer/drums',args:[v]}));

  ipcMain.on('system-start', ()=>{
    udpOut.send({address:'/system/start',args:[]});
    activeSession = {
      id: Date.now().toString(36),
      start: Math.floor(Date.now()/1000),
      end: null,
      ...currentSettings,
    };
  });
  ipcMain.on('system-stop', ()=>{
    udpOut.send({address:'/system/stop',args:[]});
    if (activeSession) {
      activeSession.end = Math.floor(Date.now()/1000);
      sessions.push(activeSession);
      saveSessions(sessions);
      activeSession = null;
    }
  });
  ipcMain.on('system-pause', ()=>udpOut.send({address:'/system/pause',args:[]}));

  ipcMain.handle('list-sessions', () => {
    return sessions;
  });

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
}); 