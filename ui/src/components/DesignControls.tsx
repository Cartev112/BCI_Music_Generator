import React from 'react';
import { Checkbox, FormControl, FormControlLabel, FormGroup, InputLabel, MenuItem, Select, Slider, Stack, Typography } from '@mui/material';

export function DesignControls() {
  const [adaptive, setAdaptive] = React.useState(false);
  const [key, setKey] = React.useState('C');
  const [arpRate, setArpRate] = React.useState(1);
  const [density, setDensity] = React.useState(0.5);
  const [layers, setLayers] = React.useState({ pad: true, arp: true, drums: false });

  function sendAdaptive(v: boolean) {
    setAdaptive(v);
    window.electronAPI.sendOSC('music-adaptive', v ? 1 : 0);
  }
  function sendKey(v: string) {
    setKey(v);
    window.electronAPI.sendOSC('music-key', v);
  }
  function sendArpRate(v: number) {
    setArpRate(v);
    window.electronAPI.sendOSC('rhythm-arp_rate', v);
  }
  function sendDensity(v: number) {
    setDensity(v);
    window.electronAPI.sendOSC('rhythm-density', v);
  }
  function sendLayer(name: 'pad' | 'arp' | 'drums', v: boolean) {
    setLayers((s) => ({ ...s, [name]: v }));
    window.electronAPI.sendOSC(`layer-${name}`, v ? 1 : 0);
  }

  const keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];

  return (
    <Stack spacing={2}>
      <Typography variant="h6">Additional Controls</Typography>
      <FormControlLabel control={<Checkbox checked={adaptive} onChange={(e) => sendAdaptive(e.target.checked)} />} label="Adaptive" />
      <FormControl size="small">
        <InputLabel id="key-label">Key</InputLabel>
        <Select labelId="key-label" label="Key" value={key} onChange={(e) => sendKey(e.target.value)}>
          {keys.map((k) => (
            <MenuItem key={k} value={k}>
              {k}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      <div>
        <Typography gutterBottom>Arp Rate: {arpRate.toFixed(2)} beats</Typography>
        <Slider min={0.25} max={2} step={0.01} value={arpRate} onChange={(_, v) => sendArpRate(v as number)} />
      </div>
      <div>
        <Typography gutterBottom>Density: {density.toFixed(2)}</Typography>
        <Slider min={0} max={1} step={0.01} value={density} onChange={(_, v) => sendDensity(v as number)} />
      </div>
      <FormGroup row>
        {(['pad', 'arp', 'drums'] as const).map((name) => (
          <FormControlLabel
            key={name}
            control={<Checkbox checked={layers[name]} onChange={(e) => sendLayer(name, e.target.checked)} />}
            label={name}
          />
        ))}
      </FormGroup>
    </Stack>
  );
}


