import React, { useState, useRef, useEffect } from 'react';
import type { AuditThread } from '../hooks/useAtlasAgent';
import styles from './AuditLog.module.css';

interface AuditLogProps {
  threads: AuditThread[];
  isProcessing: boolean;
}

const getStatusIcon = (status: string): string => {
  switch (status) {
    case 'PASS': return '✓';
    case 'WARN': return '⚠';
    case 'BLOCK': return '✗';
    case 'PENDING': return '○';
    default: return '•';
  }
};

const getStatusClass = (status: string): string => {
  switch (status) {
    case 'PASS': return styles.statusPass;
    case 'WARN': return styles.statusWarn;
    case 'BLOCK': return styles.statusBlock;
    case 'PENDING': return styles.statusPending;
    default: return '';
  }
};

const AuditThreadItem: React.FC<{
  thread: AuditThread;
  isLatest: boolean;
  defaultExpanded?: boolean;
}> = ({ thread, isLatest, defaultExpanded = false }) => {
  const [isExpanded, setIsExpanded] = useState(isLatest || defaultExpanded);

  useEffect(() => {
    if (isLatest) {
      setIsExpanded(true);
    } else {
      setIsExpanded(false);
    }
  }, [isLatest]);

  return (
    <div className={`${styles.thread} ${isLatest ? styles.latestThread : ''}`}>
      <div 
        className={styles.threadHeader} 
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <span className={styles.expandIcon}>{isExpanded ? '▼' : '▶'}</span>
        <span className={styles.queryText}>&gt; {thread.query}</span>
        <span className={styles.entryCount}>[{thread.entries.length} units]</span>
      </div>
      
      {isExpanded && (
        <div className={styles.threadContent}>
          {thread.entries.map((entry, index) => (
            <div key={index} className={styles.entry}>
              <span className={styles.timestamp}>
                {new Date(entry.timestamp).toLocaleTimeString('en-US', { 
                  hour12: false,
                  hour: '2-digit',
                  minute: '2-digit',
                  second: '2-digit'
                })}
              </span>
              <span className={styles.action}>
                &gt; {entry.action}...
              </span>
              <span className={`${styles.status} ${getStatusClass(entry.status)}`}>
                {getStatusIcon(entry.status)} {entry.status}
              </span>
              {entry.details && (
                <span className={styles.details}>{entry.details}</span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export const AuditLog: React.FC<AuditLogProps> = ({ threads, isProcessing }) => {
  const logRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [threads, isProcessing]);

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <span className={styles.headerIcon}>◉</span>
        <span className={styles.headerTitle}>SYSTEM INTERNALS</span>
        <span className={styles.headerBadge}>LIVE</span>
      </div>
      
      <div className={styles.log} ref={logRef}>
        {threads.length === 0 && !isProcessing && (
          <div className={styles.empty}>
            <span className={styles.emptyIcon}>⌘</span>
            <span>Awaiting query...</span>
          </div>
        )}
        
        {threads.map((thread, index) => (
          <AuditThreadItem 
            key={thread.id} 
            thread={thread} 
            isLatest={index === threads.length - 1} 
          />
        ))}
        
        {isProcessing && threads[threads.length - 1]?.entries.length === 0 && (
          <div className={`${styles.entry} ${styles.processing}`}>
            <span className={styles.processingIcon}>▶</span>
            <span>Initializing Engine</span>
            <span className={styles.dots}>...</span>
          </div>
        )}
      </div>
    </div>
  );
};
