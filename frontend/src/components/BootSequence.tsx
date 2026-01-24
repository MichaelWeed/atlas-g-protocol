import React, { useState, useEffect, useRef } from 'react';
import styles from './BootSequence.module.css';

interface BootSequenceProps {
  onComplete: () => void;
}

const BOOT_LINES = [
  { text: "ATLAS-G PROTOCOL [Version 1.0.0.42]", delay: 200 },
  { text: "(C) 2026 Michael Weed / Agentic Architecture Group", delay: 100 },
  { text: " ", delay: 100 },
  { text: "UPLINK INITIALIZED...", delay: 800 },
  { text: "[OK] COMPLIANCE ENGINE LOADED", delay: 300, type: 'success' },
  { text: "[OK] GOVERNANCE LAYER L1/L2 ACTIVE", delay: 200, type: 'success' },
  { text: "[OK] RESUME KNOWLEDGE GRAPH MAPPED", delay: 400, type: 'success' },
  { text: "[OK] SECURE WEBSOCKET HANDSHAKE READY", delay: 200, type: 'success' },
  { text: " ", delay: 100 },
  { text: "ESTABLISHING TRUST-CERTIFICATE...", delay: 1200 },
  { text: "ACCESS GRANTED: LEVEL 4 AUDIT", delay: 500, type: 'alert' },
  { text: " ", delay: 100 },
  { text: "SYSTEM ADVISORY:", delay: 100 },
  { text: "Queries are monitored for policy compliance.", delay: 300 },
  { text: "Unauthorized probing will trigger Protocol Lockdown.", delay: 300 },
  { text: " ", delay: 100 },
  { text: "BOOT SEQUENCE COMPLETE.", delay: 1000 },
  { text: "DECRYPTING CORE CONSOLE...", delay: 800 },
];

export const BootSequence: React.FC<BootSequenceProps> = ({ onComplete }) => {
  const [visibleLines, setVisibleLines] = useState<number>(0);
  const [isFading, setIsFading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (visibleLines < BOOT_LINES.length) {
      const timer = setTimeout(() => {
        setVisibleLines(prev => prev + 1);
        if (scrollRef.current) {
          scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
      }, BOOT_LINES[visibleLines].delay);
      return () => clearTimeout(timer);
    } else {
      // Sequence complete, wait then fade
      const fadeTimer = setTimeout(() => {
        setIsFading(true);
        // Wait for fade animation before finishing
        setTimeout(onComplete, 1000);
      }, 1500);
      return () => clearTimeout(fadeTimer);
    }
  }, [visibleLines, onComplete]);

  return (
    <div className={`${styles.bootOverlay} ${isFading ? styles.fadeOut : ''}`}>
      <div className={styles.scanline}></div>
      <div className={styles.crtEffect}></div>
      
      <div className={styles.terminalContainer} ref={scrollRef}>
        <div className={styles.terminalContent}>
          {BOOT_LINES.slice(0, visibleLines).map((line, idx) => (
            <div 
              key={idx} 
              className={`
                ${styles.line} 
                ${line.type === 'success' ? styles.success : ''} 
                ${line.type === 'alert' ? styles.alert : ''}
              `}
            >
              <span className={styles.prompt}>{"> "}</span>
              {line.text}
            </div>
          ))}
          {visibleLines < BOOT_LINES.length && (
            <div className={styles.cursorLine}>
              <span className={styles.prompt}>{"> "}</span>
              <span className={styles.cursor}>█</span>
            </div>
          )}
        </div>
      </div>

      <div className={styles.skipPrompt} onClick={onComplete}>
        [ CLICK TO BYPASS UPLINK ]
      </div>
    </div>
  );
};
