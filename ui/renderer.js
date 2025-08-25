// Temporary shim: the Electron app will soon load a Vite-built React app from ui/dist
// Keep this file minimal to avoid confusion; the new renderer lives in src/ and is built by Vite.
const e = React.createElement;

function EEGMonitor(){
  const NUM_CH=4;
  const MAX_POINTS=500;
  const canvasRefs=React.useRef([...Array(NUM_CH)].map(()=>React.createRef()));
  const chartsRef=React.useRef([]);
  const buffers=React.useRef([...Array(NUM_CH)].map(()=>[]));
  const [quality,setQuality]=React.useState([1,1,1,1]);
  const [markers,setMarkers]=React.useState([]);
  const psdCanvasRef=React.useRef(null);
  const psdChartRef=React.useRef(null);

  React.useEffect(()=>{
    // init charts
    chartsRef.current=canvasRefs.current.map((ref,i)=>{
      const ctx=ref.current.getContext('2d');
      return new Chart(ctx,{type:'line',data:{labels:Array(MAX_POINTS).fill(''),datasets:[{data:[],borderColor:'#4caf50',borderWidth:1,pointRadius:0}]},options:{animation:false,responsive:false,plugins:{legend:{display:false}},scales:{x:{display:false},y:{display:false}}}});
    });
    window.electronAPI.onSample((arr)=>{
      arr.slice(0,NUM_CH).forEach((v,ch)=>{
        const buf=buffers.current[ch];
        buf.push(v);
        if(buf.length>MAX_POINTS) buf.shift();
        // quality calc
        const within=buf.filter(x=>Math.abs(x)<=100).length;
        quality[ch]=within/buf.length;
      });
      setQuality([...quality]);
      chartsRef.current.forEach((chart,ch)=>{
        chart.data.datasets[0].data=[...buffers.current[ch]];
        chart.update('none');
      });
    });
    window.electronAPI.onMarker(m=>setMarkers(ms=>[m,...ms].slice(0,20)));
  },[]);

  React.useEffect(()=>{
    if(psdCanvasRef.current){
      const ctx=psdCanvasRef.current.getContext('2d');
      psdChartRef.current=new Chart(ctx,{type:'bar',data:{labels:['Alpha','Beta'],datasets:[{label:'Power',data:[0,0],backgroundColor:['#2196f3','#ff9800']}]},options:{responsive:false,plugins:{legend:{display:false}}}});
    }
  },[]);

  React.useEffect(()=>{
    const SAMPLE_RATE=250;
    const calcPSD=()=>{
      const ch0=buffers.current[0];
      if(ch0.length<512) return;
      const slice=ch0.slice(-512);
      const windowed=slice.map((v,i)=>v*Math.hypot(0.54-0.46*Math.cos(2*Math.PI*i/511))); // hamming
       // Placeholder PSD calc (to be moved to Web Worker in Vite-based app)
       const mags=new Array(512).fill(0);
      const freqRes=SAMPLE_RATE/512;
      const bandPower=(low,high)=>{
        let sum=0, count=0;
        for(let i=Math.floor(low/freqRes);i<=Math.ceil(high/freqRes);i++){ sum+=mags[i]; count++; }
        return sum/count;
      };
      const alpha=bandPower(8,13);
      const beta=bandPower(13,30);
      if(psdChartRef.current){
        psdChartRef.current.data.datasets[0].data=[alpha,beta];
        psdChartRef.current.update('none');
      }
    };
    const id=setInterval(calcPSD,1000);
    return ()=>clearInterval(id);
  },[]);

  return e('div',null,
    canvasRefs.current.map((ref,i)=>
      e('div',{key:i,style:{display:'flex',alignItems:'center'}},
        e('canvas',{ref:ref,width:400,height:50}),
        e('div',{style:{width:40,marginLeft:4,color:'#ccc'}},Math.round(quality[i]*100)+'%')
      )
    ),
    e('div',null, `Markers:`),
    e('h4',null,'PSD (Ch0'),
    e('canvas',{ref:psdCanvasRef,width:400,height:100})
  );
}

function LED({on,label}){return e('div',{style:{display:'flex',alignItems:'center',marginRight:8}},e('div',{style:{width:12,height:12,borderRadius:6,background:on?'#4caf50':'#555',marginRight:4}}),label);}

function TopBar(){
  const [running,setRun]=React.useState(false);
  const [elapsed,setElapsed]=React.useState(0);
  const [status,setStatus]=React.useState({board:false,classifier:false,osc:false});
  React.useEffect(()=>{
    const id=setInterval(()=>{ if(running) setElapsed(prev=>prev+1); },1000); return ()=>clearInterval(id);
  },[running]);
  React.useEffect(()=>{
    ['board','classifier','osc'].forEach(k=>window.electronAPI.onStatus(k,v=>setStatus(s=>({...s,[k]:v}))));
  },[]);
  function start(){ window.electronAPI.sendSystem('start'); setRun(true); setElapsed(0); }
  function stop(){ window.electronAPI.sendSystem('stop'); setRun(false); }
  function pause(){ window.electronAPI.sendSystem('pause'); setRun(false); }
  const mm=Math.floor(elapsed/60).toString().padStart(2,'0');
  const ss=(elapsed%60).toString().padStart(2,'0');
  return e('div',{style:{display:'flex',alignItems:'center',padding:'4px 8px',background:'#222',color:'#ddd'}},
    e('strong',null,'BCI Music System'),
    e('div',{style:{marginLeft:20}},`${mm}:${ss}`),
    e('div',{style:{marginLeft:20}},
      e('button',{onClick:start},'⏵'),
      e('button',{onClick:pause,style:{marginLeft:4}},'⏸'),
      e('button',{onClick:stop,style:{marginLeft:4}},'◼')
    ),
    e('div',{style:{marginLeft:'auto',display:'flex'}},
      e(LED,{on:status.board,label:'Board'}),
      e(LED,{on:status.classifier,label:'Cls'}),
      e(LED,{on:status.osc,label:'OSC'})
    )
  );
}

function App() {
  const [prob, setProb] = React.useState(0);
  const [view,setView]=React.useState('home');
  const [preset, setPreset] = React.useState('consonant');
  const [arpMode, setArp] = React.useState('off');
  const [tempo,setTempo]=React.useState(100);
  const [beatsChord,setBeats]=React.useState(2);
  const chartRef=React.useRef(null);
  const canvasRef=React.useRef(null);

  React.useEffect(() => {
    window.electronAPI.on('bci-prob', setProb);
  }, []);

  React.useEffect(()=>{
    // initialise chart once canvas available
    if(canvasRef.current){
      const ctx=canvasRef.current.getContext('2d');
      chartRef.current=new Chart(ctx,{type:'doughnut',data:{labels:['Prob',''],datasets:[{data:[0,1],backgroundColor:['#4caf50','#333'],borderWidth:0}]},options:{rotation:-Math.PI, circumference:Math.PI, cutout:'70%', plugins:{tooltip:{enabled:false},legend:{display:false}}}});
    }
  },[]);

  React.useEffect(()=>{ if(chartRef.current){ chartRef.current.data.datasets[0].data=[prob,1-prob]; chartRef.current.update(); } },[prob]);

  function handlePresetChange(ev) {
    const p = ev.target.value;
    setPreset(p);
    window.electronAPI.sendOSC('music-preset', p);
  }

  function handleArp(mode){
    setArp(mode);
    window.electronAPI.sendOSC('rhythm-arp_mode', mode);
  }

  function handleTempo(ev){ const v=parseInt(ev.target.value); setTempo(v); window.electronAPI.sendOSC('music-tempo',v); }
  function handleBeats(ev){ const v=parseInt(ev.target.value); setBeats(v); window.electronAPI.sendOSC('music-beats_per_chord',v); }

  if(view==='home'){
    return e('div',{style:{height:'100%',display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',background:'#111',color:'#eee'}},
      e('h1',null,'BCI Music Generator'),
      e('button',{style:{padding:'10px 20px',margin:10},onClick:()=>setView('setup')},'Start New Session'),
      e('button',{style:{padding:'10px 20px',margin:10},onClick:()=>setView('history')},'Session History')
    );
  }

  if(view==='history'){
    const [sessions,setSessions]=React.useState([]);
    React.useEffect(()=>{ window.electronAPI.getSessions().then(setSessions); },[]);
    return e('div',{style:{padding:20,color:'#eee',background:'#000',height:'100%',overflow:'auto'}},
      e('h2',null,'Session History'),
      e('button',{onClick:()=>setView('home')},'Back'),
      e('table',null,
        e('thead',null,e('tr',null,['ID','Start','End','Preset','Key','BPM'].map(h=>e('th',{key:h,style:{padding:4}},h)))),
        e('tbody',null,
          sessions.map(s=>e('tr',{key:s[0]},s.map((v,i)=>e('td',{key:i,style:{padding:4}},i==1||i==2?new Date(v*1000).toLocaleString():v))) )
        )
      )
    );
  }

  if(view==='setup'){
    // simple hardware check page using status LEDs
    return e('div',{style:{height:'100%',display:'flex',flexDirection:'column'}},
      e(TopBar),
      e('div',{style:{flex:1,display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',color:'#eee',background:'#000'}},
        e('h2',null,'Hardware Setup'),
        e('p',null,'Ensure the BCI board is connected. Status LEDs should turn green.'),
        e(LED,{on:false,label:'Board'}), // actual LED updates below
        e(LED,{on:false,label:'OSC'}),
        e('button',{style:{marginTop:20,padding:'10px 20px'},onClick:()=>setView('main')},'Continue')
      )
    );
  }

  // main view
  return e('div',{style:{height:'100%',display:'flex',flexDirection:'column'}},
    e(TopBar),
    e('div',{style:{flex:1,display:'flex'}},
      e('div', { style: { flex: 1, padding: 10, overflow:'auto'} },
        e('h3', null, 'Classifier Probability'),
        e('div', null, `Prob: ${prob.toFixed(2)}`),
        e('canvas',{ref:canvasRef,width:200,height:100}),
         e(EEGMonitor)
      ),
      e('div', { style: { width: 300, padding: 10, background:'#2b2b2b' } },
        e('h3', null, 'Music Controls'),
        e('label', null, 'Preset:'),
        e('select', { value: preset, onChange: handlePresetChange },
          ['consonant','jazzy','chromatic'].map(n=>e('option',{key:n,value:n},n))
        ),
        e('div', {style:{marginTop:8}},
          ['off','up','down','updown','random'].map(m=>
            e('button',{key:m,style:{margin:2,background:arpMode===m?'#555':'#444',color:'#eee'},onClick:()=>handleArp(m)},m))
        ),
        e('div', {style:{marginTop:8}},
          e('label', null, `Tempo: ${tempo}`),
          e('input', { type: 'range', min: 60, max: 200, value: tempo, onChange: handleTempo })
        ),
        e('div', {style:{marginTop:8}},
          e('label', null, `Beats/Chord: ${beatsChord}`),
          e('input', { type: 'range', min: 1, max: 10, value: beatsChord, onChange: handleBeats })
        )
      )
    )
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(e(App)); 