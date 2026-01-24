import { useState, useEffect } from 'react';
import './index.css';
import { useAtlasAgent } from './hooks/useAtlasAgent';
import { TerminalHeader } from './components/TerminalHeader';
import { ChatPane } from './components/ChatPane';
import { AuditLog } from './components/AuditLog';
import { BootSequence } from './components/BootSequence';
import styles from './App.module.css';

function App() {
  const {
    messages,
    auditThreads,
    isConnected,
    isProcessing,
    sendMessage,
  } = useAtlasAgent();

  const [showBoot, setShowBoot] = useState(true);

  // Persistence: Skip boot if already seen in this session
  useEffect(() => {
    const hasSeenBoot = sessionStorage.getItem('atlas_boot_complete');
    if (hasSeenBoot) {
      setShowBoot(false);
    }
  }, []);

  const handleBootComplete = () => {
    setShowBoot(false);
    sessionStorage.setItem('atlas_boot_complete', 'true');
  };

  return (
    <>
      {showBoot && <BootSequence onComplete={handleBootComplete} />}
      
      <div className={`${styles.app} ${!showBoot ? styles.fadeIn : ''}`} style={{ visibility: showBoot ? 'hidden' : 'visible' }}>
        <TerminalHeader isConnected={isConnected} />
        
        <main className={styles.main}>
          <div className={styles.chatSection}>
            <ChatPane
              messages={messages}
              onSendMessage={sendMessage}
              isProcessing={isProcessing}
            />
          </div>
          
          <div className={styles.auditSection}>
            <AuditLog
              threads={auditThreads}
              isProcessing={isProcessing}
            />
          </div>
        </main>
        
        <footer className={styles.footer}>
          <span className={styles.footerText}>
            ATLAS-G PROTOCOL v1.0.0 | Compliance-Grade MCP Server
          </span>
          <span className={styles.footerDivider}>|</span>
          <span className={styles.footerText}>
            Powered by Google Gemini
          </span>
        </footer>
      </div>
    </>
  );
}

export default App;
