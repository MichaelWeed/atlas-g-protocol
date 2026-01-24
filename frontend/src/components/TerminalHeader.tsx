import React from 'react';
import styles from './TerminalHeader.module.css';

interface TerminalHeaderProps {
  isConnected: boolean;
}

export const TerminalHeader: React.FC<TerminalHeaderProps> = ({ isConnected }) => {
  return (
    <header className={styles.header}>
      <div className={styles.titleSection}>
        <div className={styles.logo}>
          <span className={styles.bracket}>[</span>
          <span className={styles.title}>ATLAS-G</span>
          <span className={styles.bracket}>]</span>
        </div>
        <span className={styles.subtitle}>PROTOCOL</span>
      </div>
      
      <div className={styles.statusSection}>
        <div className={styles.statusIndicator}>
          <span 
            className={`${styles.statusDot} ${isConnected ? styles.connected : styles.disconnected}`}
          />
          <span className={styles.statusText}>
            {isConnected ? 'SECURE CHANNEL' : 'CONNECTING...'}
          </span>
        </div>
        
        <div className={styles.classification}>
          <span className={styles.classificationBadge}>
            COMPLIANCE-GRADE MCP
          </span>
        </div>
      </div>
    </header>
  );
};
