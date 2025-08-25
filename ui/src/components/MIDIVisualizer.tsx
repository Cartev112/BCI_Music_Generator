import React, { useRef, useEffect, useState, useCallback } from 'react';
import { Music2 } from 'lucide-react';
import { startMIDIDemo } from './MIDIDemoData';

interface MIDINote {
  id: string;
  pitch: number; // MIDI note number (0-127)
  velocity: number; // 0-127
  startTime: number; // in milliseconds
  duration: number; // in milliseconds
  channel: number; // MIDI channel
}

interface MIDIVisualizerProps {
  width?: number;
  height?: number;
}

export function MIDIVisualizer({ width = 800, height = 200 }: MIDIVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();
  const [notes, setNotes] = useState<MIDINote[]>([]);
  const [currentTime, setCurrentTime] = useState(0);
  
  // Visual configuration
  const config = {
    scrollSpeed: 100, // pixels per second
    noteHeight: 8, // height of each note bar (increased for visibility)
    pitchRange: { min: 36, max: 96 }, // C2 to C7 (60 notes)
    timeWindow: 5000, // 5 seconds visible (reduced for better note visibility)
    colors: {
      background: '#0a0a0a',
      grid: '#1a1a1a',
      notes: ['#ffffff', '#34d399', '#60a5fa', '#ef4444'], // white, green, blue, red
      text: '#9a9a9a'
    }
  };

  // Convert MIDI pitch to Y coordinate
  const pitchToY = useCallback((pitch: number) => {
    const { min, max } = config.pitchRange;
    const normalizedPitch = Math.max(0, Math.min(1, (pitch - min) / (max - min)));
    return height - (normalizedPitch * (height - 40)) - 20; // 20px padding top/bottom
  }, [height, config.pitchRange]);

  // Convert time to X coordinate
  const timeToX = useCallback((time: number) => {
    const now = Date.now();
    const timeSinceNote = now - time; // How long ago was this note created
    const pixelsFromRight = (timeSinceNote / config.timeWindow) * width;
    return width - pixelsFromRight;
  }, [width, config.timeWindow]);

  // Draw the visualizer
  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.fillStyle = config.colors.background;
    ctx.fillRect(0, 0, width, height);

    // Draw grid lines (pitch lines)
    ctx.strokeStyle = config.colors.grid;
    ctx.lineWidth = 0.5;
    for (let pitch = config.pitchRange.min; pitch <= config.pitchRange.max; pitch += 12) {
      const y = pitchToY(pitch);
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    // Draw time grid (vertical lines every second)
    const now = Date.now();
    for (let t = 0; t <= config.timeWindow; t += 1000) {
      const x = timeToX(now - t);
      if (x >= 0 && x <= width) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
    }

    // Draw notes
    notes.forEach((note, index) => {
      const startX = timeToX(note.startTime);
      const endX = timeToX(note.startTime + note.duration);
      const y = pitchToY(note.pitch);

      // Calculate proper note bounds
      const noteLeft = Math.min(startX, endX);
      const noteRight = Math.max(startX, endX);
      const noteWidth = noteRight - noteLeft;
      
      // Only draw if note is visible (any part of note intersects canvas)
      if (noteRight > 0 && noteLeft < width && noteWidth > 1) {
        const colorIndex = note.channel % config.colors.notes.length;
        const alpha = Math.max(0.6, note.velocity / 127);
        
        // Calculate drawing bounds - allow notes to extend beyond canvas edges
        let drawX = noteLeft;
        let drawWidth = noteWidth;
        const drawY = y - config.noteHeight / 2;
        
        // Clip to canvas bounds only for drawing, not for positioning
        const clippedX = Math.max(0, drawX);
        const clippedWidth = Math.min(drawX + drawWidth, width) - clippedX;
        
        if (clippedWidth > 0 && drawY >= 0 && drawY < height) {
          // Save context for clipping
          ctx.save();
          
          // Clip to canvas bounds
          ctx.beginPath();
          ctx.rect(0, 0, width, height);
          ctx.clip();
          
          // Draw note rectangle (full size, let clipping handle edges)
          ctx.fillStyle = config.colors.notes[colorIndex];
          ctx.globalAlpha = alpha;
          ctx.fillRect(drawX, drawY, drawWidth, config.noteHeight);
          ctx.globalAlpha = 1;

          // Draw note border for definition
          ctx.strokeStyle = config.colors.notes[colorIndex];
          ctx.lineWidth = 1;
          ctx.strokeRect(drawX, drawY, drawWidth, config.noteHeight);
          
          // Restore context
          ctx.restore();
        }
      }
    });

    // Draw pitch labels (C notes)
    ctx.fillStyle = config.colors.text;
    ctx.font = '10px var(--font-mono)';
    ctx.textAlign = 'right';
    for (let pitch = config.pitchRange.min; pitch <= config.pitchRange.max; pitch += 12) {
      const y = pitchToY(pitch);
      const octave = Math.floor(pitch / 12) - 1;
      ctx.fillText(`C${octave}`, width - 5, y + 3);
    }

    // Draw current time indicator
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(width - 1, 0);
    ctx.lineTo(width - 1, height);
    ctx.stroke();

  }, [notes, currentTime, width, height, config, pitchToY, timeToX]);

  // Animation loop
  const animate = useCallback(() => {
    setCurrentTime(prev => prev + 16.67); // ~60fps
    draw();
    animationRef.current = requestAnimationFrame(animate);
  }, [draw]);

  // Start animation
  useEffect(() => {
    animationRef.current = requestAnimationFrame(animate);
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [animate]);

  // Clean up old notes that have scrolled off screen (less frequent)
  useEffect(() => {
    const cleanup = () => {
      setNotes(prev => prev.filter(note => {
        const noteEndX = timeToX(note.startTime + note.duration);
        return noteEndX > -100; // Keep notes until they're 100px off screen
      }));
    };
    
    const interval = setInterval(cleanup, 500); // Clean up every 500ms instead of every frame
    return () => clearInterval(interval);
  }, [timeToX]);

  // Function to add a new note (will be called by MIDI input)
  const addNote = useCallback((note: Omit<MIDINote, 'id'>) => {
    const newNote: MIDINote = {
      ...note,
      id: `${note.startTime}-${note.pitch}-${Math.random()}`
    };
    setNotes(prev => [...prev, newNote]);
  }, []);

  // Expose addNote function for external use and start demo
  useEffect(() => {
    // Store reference for external access
    (window as any).addMIDINote = addNote;
    
    // Start demo after a short delay
    const timeout = setTimeout(() => {
      const cleanup = startMIDIDemo();
      return cleanup;
    }, 1000);

    return () => {
      clearTimeout(timeout);
      delete (window as any).addMIDINote;
    };
  }, [addNote]);

  return (
    <div style={panelStyle}>
      <div style={panelHeaderStyle}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Music2 width={16} height={16} />
          <span style={panelTitleStyle}>MIDI Visualizer</span>
        </div>
        <div style={panelMetaStyle}>real-time • notes</div>
      </div>
      <div style={{ padding: 16 }}>
        <canvas
          ref={canvasRef}
          width={width}
          height={height}
          style={{
            width: '100%',
            height: `${height}px`,
            border: '1px solid var(--line)',
            borderRadius: 6,
            background: config.colors.background
          }}
        />
        <div style={{ marginTop: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={infoTextStyle}>
            Notes: {notes.length}
          </div>
          <div style={infoTextStyle}>
            Time: {(currentTime / 1000).toFixed(1)}s
          </div>
        </div>
      </div>
    </div>
  );
}

// Styles matching ControlRoom aesthetic
const panelStyle: React.CSSProperties = { 
  borderRadius: 12, 
  border: '1px solid var(--line)', 
  background: 'color-mix(in oklab, var(--panel) 90%, transparent)', 
  overflow: 'hidden' 
};

const panelHeaderStyle: React.CSSProperties = { 
  display: 'flex', 
  alignItems: 'center', 
  justifyContent: 'space-between', 
  padding: '12px 16px', 
  borderBottom: '1px solid var(--line)' 
};

const panelTitleStyle: React.CSSProperties = { 
  fontSize: 12, 
  letterSpacing: '0.16em', 
  textTransform: 'uppercase' 
};

const panelMetaStyle: React.CSSProperties = { 
  fontSize: 10, 
  color: 'var(--muted)', 
  letterSpacing: '0.2em', 
  textTransform: 'uppercase' 
};

const infoTextStyle: React.CSSProperties = {
  fontSize: 10,
  color: 'var(--muted)',
  fontFamily: 'var(--font-mono)',
  letterSpacing: '0.1em',
  textTransform: 'uppercase'
};
