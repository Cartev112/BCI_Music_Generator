import React from 'react';

// Demo MIDI data generator for MIDIVisualizer
export function startMIDIDemo() {
  let startTime = Date.now();
  
  // Demo song: Simple chord progression with melody
  const chordProgression = [
    // C Major chord
    { pitches: [60, 64, 67], startTime: 0, duration: 2000 }, // C, E, G
    // A minor chord  
    { pitches: [57, 60, 64], startTime: 2000, duration: 2000 }, // A, C, E
    // F Major chord
    { pitches: [53, 57, 60], startTime: 4000, duration: 2000 }, // F, A, C
    // G Major chord
    { pitches: [55, 59, 62], startTime: 6000, duration: 2000 }, // G, B, D
  ];

  // Melody line
  const melody = [
    { pitch: 72, startTime: 500, duration: 500 },   // C5
    { pitch: 74, startTime: 1000, duration: 500 },  // D5
    { pitch: 76, startTime: 1500, duration: 500 },  // E5
    { pitch: 74, startTime: 2500, duration: 500 },  // D5
    { pitch: 72, startTime: 3000, duration: 500 },  // C5
    { pitch: 69, startTime: 3500, duration: 500 },  // A4
    { pitch: 65, startTime: 4500, duration: 500 },  // F4
    { pitch: 67, startTime: 5000, duration: 500 },  // G4
    { pitch: 69, startTime: 5500, duration: 500 },  // A4
    { pitch: 67, startTime: 6500, duration: 500 },  // G4
    { pitch: 65, startTime: 7000, duration: 500 },  // F4
    { pitch: 64, startTime: 7500, duration: 500 },  // E4
  ];

  // Bass line
  const bassLine = [
    { pitch: 36, startTime: 0, duration: 2000 },    // C2
    { pitch: 33, startTime: 2000, duration: 2000 }, // A1
    { pitch: 29, startTime: 4000, duration: 2000 }, // F1
    { pitch: 31, startTime: 6000, duration: 2000 }, // G1
  ];

  function addNote(pitch: number, startTime: number, duration: number, channel: number = 0, velocity: number = 100) {
    if ((window as any).addMIDINote) {
      (window as any).addMIDINote({
        pitch,
        velocity,
        startTime: Date.now(), // Use current time
        duration,
        channel
      });
    }
  }

  function playPattern() {
    const currentTime = Date.now() - startTime;
    const loopTime = currentTime % 8000; // 8-second loop

    // Play chords (channel 0 - white)
    chordProgression.forEach(chord => {
      if (Math.abs(loopTime - chord.startTime) < 50) { // 50ms tolerance
        chord.pitches.forEach(pitch => {
          addNote(pitch, chord.startTime, chord.duration, 0, 80);
        });
      }
    });

    // Play melody (channel 1 - green)
    melody.forEach(note => {
      if (Math.abs(loopTime - note.startTime) < 50) {
        addNote(note.pitch, note.startTime, note.duration, 1, 100);
      }
    });

    // Play bass (channel 2 - blue)
    bassLine.forEach(note => {
      if (Math.abs(loopTime - note.startTime) < 50) {
        addNote(note.pitch, note.startTime, note.duration, 2, 90);
      }
    });

    // Add some random percussion/effects (channel 3 - red)
    if (Math.random() < 0.1) { // 10% chance each frame
      const pitch = 80 + Math.floor(Math.random() * 20); // High pitched effects
      addNote(pitch, 0, 200, 3, 60 + Math.random() * 40);
    }
  }

  // Start the demo
  const interval = setInterval(playPattern, 50); // Check every 50ms

  // Return cleanup function
  return () => {
    clearInterval(interval);
  };
}

// Auto-start demo when component loads (for demonstration)
export function useMIDIDemo() {
  React.useEffect(() => {
    // Wait a bit for the component to initialize
    const timeout = setTimeout(() => {
      const cleanup = startMIDIDemo();
      return cleanup;
    }, 1000);

    return () => clearTimeout(timeout);
  }, []);
}
