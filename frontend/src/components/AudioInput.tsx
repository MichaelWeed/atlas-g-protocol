import React, { useState, useEffect, useRef } from 'react';
import styles from './AudioInput.module.css';

interface AudioInputProps {
  onTranscript: (text: string) => void;
  disabled?: boolean;
}

export const AudioInput: React.FC<AudioInputProps> = ({ onTranscript, disabled }) => {
  const [isListening, setIsListening] = useState(false);
  const [permissionDenied, setPermissionDenied] = useState(false);
  const recognitionRef = useRef<any>(null);
  const transcriptCallbackRef = useRef(onTranscript);

  // Sync callback ref to avoid re-initializing the singleton logic
  useEffect(() => {
    transcriptCallbackRef.current = onTranscript;
  }, [onTranscript]);

  useEffect(() => {
    // Check for SpeechRecognition support
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    
    if (SpeechRecognition && !recognitionRef.current) {
      console.log('🎤 Initializing SpeechRecognition singleton...');
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';

      recognition.onstart = () => {
        console.log('🎤 SpeechRecognition: onstart');
        setIsListening(true);
        setPermissionDenied(false);
      };

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        console.log('🎤 SpeechRecognition: onresult', transcript);
        transcriptCallbackRef.current(transcript);
        setIsListening(false);
      };

      recognition.onerror = (event: any) => {
        console.error('🎤 SpeechRecognition: onerror', event.error, event.message);
        if (event.error === 'not-allowed') {
          setPermissionDenied(true);
        } else if (event.error === 'network') {
          setPermissionDenied(true); 
        }
        setIsListening(false);
      };

      recognition.onend = () => {
        console.log('🎤 SpeechRecognition: onend');
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    }

    return () => {
      // NOTE: We do NOT null handlers here. The singleton instance in recognitionRef 
      // stays active and its handlers continue to use transcriptCallbackRef.current.
      // We only stop it if it's currently active to prevent background leaks.
      if (recognitionRef.current && isListening) {
        try {
          recognitionRef.current.stop();
        } catch (e) { }
      }
    };
  }, [isListening]); // Only depend on lifecycle state, not the callback

  const toggleListening = async () => {
    if (isListening) {
      console.log('🎤 Manual stop requested');
      try {
        recognitionRef.current?.stop();
      } catch (e) {
        setIsListening(false);
      }
    } else {
      try {
        // Reset state for new attempt
        setPermissionDenied(false);
        
        console.log('🎤 Attempting to start SpeechRecognition...');
        recognitionRef.current?.start();
      } catch (err) {
        console.error('🎤 Start failed:', err);
        setPermissionDenied(true);
        setIsListening(false);
      }
    }
  };

  if (!recognitionRef.current && typeof window !== 'undefined') {
    return null; // Don't show if not supported
  }

  return (
    <button
      type="button"
      className={`${styles.micBtn} ${isListening ? styles.listening : ''} ${permissionDenied ? styles.denied : ''}`}
      onClick={toggleListening}
      disabled={disabled}
      title={permissionDenied ? "Voice service unavailable. Note: Brave/Brave-like browsers may disable this service by default. Please check site settings or try Chrome/Safari." : "Voice Input (VoiceVerdict Integration)"}
    >
      <span className={styles.icon}>{permissionDenied ? '🚫' : isListening ? '●' : '🎤'}</span>
      {isListening && <span className={styles.pulse}></span>}
    </button>
  );
};
