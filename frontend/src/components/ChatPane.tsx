import React, { useState, useRef, useEffect, type FormEvent } from 'react';
import styles from './ChatPane.module.css';
import { AudioInput } from './AudioInput';
import { useScramble } from '../hooks/useScramble';

interface Message {
  id: string;
  type: 'user' | 'agent' | 'system';
  content: string;
  timestamp: Date;
  metadata?: {
    blocked?: boolean;
    factsVerified?: number;
    claimsFiltered?: number;
    sessionTerminated?: boolean;
    contactRequested?: boolean;
  };
}

interface ChatPaneProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  isProcessing: boolean;
}

const formatTime = (date: Date): string => {
  return date.toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
  });
};

// Agent Stats for HUD Data Manifest (synced with availability.json)
const AGENT_STATS = {
  status: 'AVAILABLE',
  rate: '200 USD/HR',
  protocol: 'MCP-NATIVE',
  start: 'FEB 01 2026',
} as const;

// Transmission log sequence
const TRANSMISSION_SEQUENCE = [
  { text: '> ENCRYPTING PAYLOAD...', status: '[DONE]', delay: 0 },
  { text: '> ESTABLISHING UPLINK...', status: '[CONNECTED]', delay: 400 },
  { text: '> UPLOADING PACKET...', status: '[100%]', delay: 800 },
  { text: '> ATLAS CORE: RECEIVED.', status: '', delay: 1200 },
];

// Scramble text component for decryption effect
const ScrambleText: React.FC<{ text: string; delay?: number }> = ({ text, delay = 0 }) => {
  const scrambled = useScramble(text, 400, delay);
  return <>{scrambled}</>;
};

/**
 * Strip markdown syntax for clean terminal-style output.
 * Converts markdown to legible plain text.
 */
const stripMarkdown = (text: string): string => {
  return text
    // Remove headers (###, ##, #) globally, even mid-line
    .replace(/#{1,6}\s?/g, '')
    // Ensure any paragraph break (multiple newlines) has clear spacing
    .replace(/\n{2,}/g, '\n\n')
    // Remove horizontal rules
    .replace(/^-{3,}$/gm, '')
    // Replace markdown lists with cleaner bullets
    .replace(/^\s*[\*\+-]\s+/gm, '• ')
    // Remove bold/italic (**text**, *text*, __text__, _text_)
    .replace(/\*\*/g, '')
    .replace(/\*/g, '')
    .replace(/__/g, '')
    .replace(/_/g, '')
    // Remove inline code backticks
    .replace(/`/g, '')
    // Remove link syntax [text](url) -> text
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    // Ensure "blackspace" by having generous gaps between paragraphs
    .replace(/\n{2,}/g, '\n\n\n')
    .trim();
};

/**
 * Render message content with alternating paragraph colors for visual distinction.
 * Odd paragraphs: off-white, Even paragraphs: off-gold
 */
const renderAlternatingParagraphs = (text: string): React.ReactNode => {
  const cleaned = stripMarkdown(text);
  const paragraphs = cleaned.split(/\n\n+/).filter(p => p.trim());
  
  return paragraphs.map((para, idx) => (
    <span 
      key={idx} 
      style={{ 
        color: idx % 2 === 1 ? '#d4a853' : 'inherit',
        display: 'block',
        marginBottom: idx < paragraphs.length - 1 ? '1.5em' : 0
      }}
    >
      {para}
    </span>
  ));
};

export const ChatPane: React.FC<ChatPaneProps> = ({
  messages,
  onSendMessage,
  isProcessing,
}) => {
  const [input, setInput] = useState('');
  const [violationCount, setViolationCount] = useState(0);
  const [isJailed, setIsJailed] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const latestMessageRef = useRef<HTMLDivElement>(null);
  // Klaxon Alarm (User's custom audio file)
  const audioRef = useRef<HTMLVideoElement>(null);

  const playKlaxon = () => {
    try {
      if (audioRef.current) {
        audioRef.current.volume = 0.5;
        audioRef.current.currentTime = 0;
        audioRef.current.play().catch(e => console.warn("Audio autoplay blocked:", e));
        
        // Stop audio after 3 seconds as requested
        setTimeout(() => {
          if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.currentTime = 0;
          }
        }, 3000);
      }
    } catch (e) {
      console.error("Klaxon audio failed:", e);
    }
  };

  useEffect(() => {
    if (messages.length === 0) return;
    const lastMsg = messages[messages.length - 1];
    
    // 1. Handle New Message Actions (Scroll, Alarm, Jail)
    if (lastMsg.id !== lastProcessedMessageId.current) {
      lastProcessedMessageId.current = lastMsg.id;
      
      // Scroll to TOP of the latest message
      setTimeout(() => {
        if (latestMessageRef.current) {
          latestMessageRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }, 50);

      if (lastMsg.metadata?.blocked) {
        playKlaxon();
        setViolationCount(prev => {
          const newCount = prev + 1;
          if (newCount >= 1) setIsJailed(true);
          return newCount;
        });
      }
    }

    // 2. Handle Final Metadata Updates (HUD Trigger, Termination)
    // This runs even if ID is same, as long as metadata just arrived
    if (lastMsg.type === 'agent') {
      if (lastMsg.metadata?.contactRequested && lastTriggeredContactId.current !== lastMsg.id) {
        setShowContactForm(true);
        lastTriggeredContactId.current = lastMsg.id;
      }
      if (lastMsg.metadata?.sessionTerminated) {
        setIsTerminated(true);
      }
    }
  }, [messages]);

  const lastTriggeredContactId = useRef<string | null>(null);

  useEffect(() => {
    if (!isJailed) {
      inputRef.current?.focus();
    }
  }, [isProcessing, isJailed]);
  

  const inputRef = useRef<HTMLInputElement>(null);
  const lastProcessedMessageId = useRef<string | null>(null);

  const [showContactForm, setShowContactForm] = useState(false);
  const [contactData, setContactData] = useState({ name: '', email: '', message: '' });
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isTerminated, setIsTerminated] = useState(false);
  const [transmissionStep, setTransmissionStep] = useState(0);
  const [showCloseBtn, setShowCloseBtn] = useState(false);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isProcessing && !isJailed && !isTerminated) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  const handlePardon = () => {
    // Force reload to clear "jail" state
    window.location.reload();
  };

  const handleSuggestionClick = (q: string) => {
    if (q === "Contact Michael") {
      setShowContactForm(true);
      setIsSubmitted(false); // Reset state when opening manually
    } else {
      onSendMessage(q);
    }
  };

  const handleContactSubmit = (e: FormEvent) => {
    e.preventDefault();
    onSendMessage(`[CONTACT FORM SUBMISSION]\nName: ${contactData.name}\nEmail: ${contactData.email}\nNote: ${contactData.message}`);
    // Start transmission animation sequence
    setIsSubmitted(true);
    setTransmissionStep(0);
    setShowCloseBtn(false);
    setContactData({ name: '', email: '', message: '' });
    
    // Animate through transmission steps
    TRANSMISSION_SEQUENCE.forEach((_, idx) => {
      setTimeout(() => setTransmissionStep(idx + 1), TRANSMISSION_SEQUENCE[idx].delay + 300);
    });
    // Show close button after sequence completes
    setTimeout(() => setShowCloseBtn(true), 1600);
  };

  const suggestionPool = [
    "Atlas Engine",
    "GCP Deployment",
    "Security Protocols",
    "Contact Michael",
    "Salesforce Experience",
    "Solution Architecture",
    "Agentic Workflows",
    "Healthcare Projects",
    "Recent Projects",
    "VoiceVerdict Platform",
    "Cloud Run Expertise",
    "FinTech Compliance",
    "Service Cloud Voice",
    "Financial Compliance Auditor"
  ];

  const [currentSuggestions, setCurrentSuggestions] = useState<string[]>([]);

  useEffect(() => {
    const lastMsg = messages[messages.length - 1];
    const contactIntent = lastMsg?.type === 'agent' && lastMsg.metadata?.contactRequested;

    // Filter out restricted suggestions and shuffle the rest
    const allowedSuggestions = suggestionPool.filter(s => s !== "Contact Michael");
    const shuffled = [...allowedSuggestions].sort(() => 0.5 - Math.random());
    
    // Take 4 or 3 if we need to inject the Contact button
    const selected = shuffled.slice(0, contactIntent ? 3 : 4);
    
    // Inject Contact Michael as the primary suggestion if intent detected
    if (contactIntent) {
      selected.unshift("Contact Michael");
    }
    
    setCurrentSuggestions(selected);
  }, [messages.length, messages[messages.length - 1]?.metadata?.contactRequested]);

  const [placeholder, setPlaceholder] = useState('Enter query...');
  const questions = [
    "What is Michael Weed's experience agentics systems . . .",
    "What is Michael's work with Salesforce . . .",
    "Can Michael deploy a full-stack solution . . ."
  ];

  useEffect(() => {
    // Only animate if it's a completely new session (no user messages yet)
    const hasUserMessages = messages.some(m => m.type === 'user');
    
    if (hasUserMessages || isProcessing || isJailed || isTerminated) {
      setPlaceholder('Enter query . . . ');
      return;
    }

    let questionIndex = 0;
    let charIndex = 0;
    let isDeleting = false;
    let timeout: any;

    const baseText = "Enter query . . . ";

    const tick = () => {
      const currentQuestion = questions[questionIndex];
      
      const nextText = isDeleting 
        ? currentQuestion.substring(0, charIndex - 1)
        : currentQuestion.substring(0, charIndex + 1);
        
      setPlaceholder(baseText + nextText);
      charIndex = isDeleting ? charIndex - 1 : charIndex + 1;

      let delta = isDeleting ? 40 : 80;

      if (!isDeleting && charIndex === currentQuestion.length) {
        isDeleting = true;
        delta = 3000; // Pause at the end
      } else if (isDeleting && charIndex === 0) {
        isDeleting = false;
        questionIndex = (questionIndex + 1) % questions.length;
        delta = 800; // Pause before next
      }

      timeout = setTimeout(tick, delta);
    };

    // Delay start to allow boot sequence to fade or stabilize
    timeout = setTimeout(tick, 2000);

    return () => clearTimeout(timeout);
  }, [messages, isProcessing, isJailed, isTerminated]);

  const handleTranscript = React.useCallback((text: string) => {
    onSendMessage(text);
  }, [onSendMessage]);

  return (
    <div className={styles.container}>
      {/* Hidden Video Element for Klaxon */}
      <video 
        ref={audioRef} 
        src="/klaxon.mov" 
        style={{ display: 'none' }} 
        playsInline 
      />

      {/* Soft Jail Overlay */}
      {isJailed && (
        <>
          <div className="jail-overlay">
            <div className="jail-content">
              <div className="jail-title">⚠ SECURITY BREACH ⚠</div>
              <div className="jail-message">
                MULTIPLE VIOLATIONS DETECTED.<br/>
                SYSTEM LOCKDOWN INITIATED.<br/><br/>
                Admin intervention required to restore access.
              </div>
              <button className="jail-btn" onClick={handlePardon}>
                REQUEST SYSTEM REBOOT
              </button>
            </div>
          </div>
          <div className="jail-bars"></div>
        </>
      )}

      {showContactForm && (
        <div className={styles.contactOverlay}>
          <div className={styles.contactForm}>
            <div className={styles.contactHeader}>
              <span>SECURE UPLINK HUD</span>
              <button 
                onClick={() => {
                  setShowContactForm(false);
                  setIsSubmitted(false);
                  setTransmissionStep(0);
                  setShowCloseBtn(false);
                  setContactData({ name: '', email: '', message: '' });
                }}
              >ABORT</button>
            </div>
            
            {isSubmitted ? (
              /* Transmission Log Animation */
              <div className={styles.transmissionLog}>
                {TRANSMISSION_SEQUENCE.slice(0, transmissionStep).map((line, idx) => (
                  <div 
                    key={idx} 
                    className={`${styles.transmissionLine} ${line.status === '[DONE]' || line.status === '[CONNECTED]' || line.status === '[100%]' ? styles.done : ''}`}
                    style={{ animationDelay: `${idx * 100}ms` }}
                  >
                    {line.text}
                    {line.status && <span className={styles.status}>{line.status}</span>}
                  </div>
                ))}
                
                {showCloseBtn && (
                  <div className={styles.transmissionComplete}>
                    <h3>TRANSMISSION COMPLETE</h3>
                    <button 
                      className={styles.submitBtn}
                      onClick={() => {
                        setShowContactForm(false);
                        setIsSubmitted(false);
                        setTransmissionStep(0);
                        setShowCloseBtn(false);
                      }}
                    >
                      CLOSE CONNECTION
                    </button>
                  </div>
                )}
              </div>
            ) : (
              /* Split-Pane HUD: Data Manifest + Input Console */
              <div className={styles.hudBody}>
                {/* Left Panel: Agent Stats */}
                <div className={styles.hudDataManifest}>
                  <div className={styles.hudSectionTitle}>AGENT MANIFEST</div>
                  
                  <div className={styles.hudStatRow}>
                    <span className={styles.hudStatLabel}>STATUS</span>
                    <div className={styles.hudStatusRow}>
                      <div className={styles.hudLed} />
                      <span className={styles.hudStatusText}>
                        <ScrambleText text={AGENT_STATS.status} delay={100} />
                      </span>
                    </div>
                  </div>
                  
                  <div className={styles.hudStatRow}>
                    <span className={styles.hudStatLabel}>RATE</span>
                    <span className={styles.hudStatValue}>
                      <ScrambleText text={AGENT_STATS.rate} delay={200} />
                    </span>
                  </div>
                  
                  <div className={styles.hudStatRow}>
                    <span className={styles.hudStatLabel}>PROTOCOL</span>
                    <span className={styles.hudStatValue}>
                      <ScrambleText text={AGENT_STATS.protocol} delay={300} />
                    </span>
                  </div>
                  
                  <div className={styles.hudStatRow}>
                    <span className={styles.hudStatLabel}>AVAILABLE</span>
                    <span className={styles.hudStatValue}>
                      <ScrambleText text={AGENT_STATS.start} delay={400} />
                    </span>
                  </div>
                </div>
                
                {/* Right Panel: Input Console */}
                <div className={styles.hudInputConsole}>
                  <form onSubmit={handleContactSubmit}>
                    <div className={styles.formGroup}>
                      <label>IDENTIFIER</label>
                      <input 
                        type="text" 
                        required 
                        placeholder="ENTER NAME"
                        value={contactData.name}
                        onChange={e => setContactData({...contactData, name: e.target.value})}
                      />
                    </div>
                    <div className={styles.formGroup}>
                      <label>RETURN CHANNEL</label>
                      <input 
                        type="email" 
                        required 
                        placeholder="UPLINK@DOMAIN.COM"
                        value={contactData.email}
                        onChange={e => setContactData({...contactData, email: e.target.value})}
                      />
                    </div>
                    <div className={styles.formGroup}>
                      <label>NEGOTIATION TERMS</label>
                      <textarea 
                        required 
                        placeholder="STATE YOUR PROPOSAL..."
                        rows={4}
                        value={contactData.message}
                        onChange={e => setContactData({...contactData, message: e.target.value})}
                      /></div>
                    <button type="submit" className={styles.submitBtn}>INITIATE TRANSMISSION</button>
                  </form>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      <div className={`${styles.header} ${isJailed ? styles.jailed : ''}`}>
        <span className={`${styles.headerIcon} ${violationCount > 0 ? styles.alarmActive : ''}`}>
          {violationCount > 0 ? '⚠' : '◆'}
        </span>
        <span className={styles.headerTitle}>
          {violationCount > 0 ? `SECURITY ALERT [LEVEL ${violationCount}]` : 'PUBLIC INTERFACE'}
        </span>
      </div>

      <div className={styles.messages}>
        {!messages.some(m => m.type === 'user' || m.type === 'agent') && (
          <div className={styles.welcome}>
            <div className={styles.welcomeTitle}>
              Welcome to the Atlas-G Protocol
            </div>
            <div className={styles.welcomeText}>
              Michael's open-source portfolio agent, a compliance-grade agentic system (C-GAS).
            </div>
            <div className={styles.suggestions}>
              <span className={styles.suggestionLabel}>Operational Queries:</span>
              <div className={styles.suggestionGrid}>
                {currentSuggestions.map((q: string) => (
                  <button 
                    key={q}
                    className={styles.suggestion}
                    onClick={() => handleSuggestionClick(q)}
                    disabled={isJailed}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {messages.map((message, idx) => (
          <div 
            key={message.id}
            ref={idx === messages.length - 1 ? latestMessageRef : null}
          >
            <div
              className={`${styles.message} ${styles[message.type]} ${message.metadata?.blocked ? 'alarm-active' : ''}`}
            >
              <div className={styles.messageHeader}>
                <span className={styles.messageRole}>
                  {message.type === 'user' ? 'YOU' : message.type === 'agent' ? 'ATLAS-G' : 'SYSTEM'}
                </span>
                <span className={styles.messageTime}>{formatTime(message.timestamp)}</span>
              </div>
              
              <div className={styles.messageContent}>
                {message.metadata?.blocked && (
                  <div className={styles.blockedBanner}>
                    🔒 Response modified by governance layer
                  </div>
                )}
                {message.type === 'agent' 
                  ? renderAlternatingParagraphs(message.content)
                  : stripMarkdown(message.content)
                }
              </div>
              
              {message.metadata && message.type === 'agent' && (
                <div className={styles.messageMetadata}>
                  {message.metadata.factsVerified !== undefined && (
                    <span className={styles.metaBadge}>
                      ✓ {message.metadata.factsVerified} facts verified
                    </span>
                  )}
                  {message.metadata.claimsFiltered !== undefined && message.metadata.claimsFiltered > 0 && (
                    <span className={`${styles.metaBadge} ${styles.filtered}`}>
                      ⚠ {message.metadata.claimsFiltered} claims filtered
                    </span>
                  )}
                </div>
              )}
            </div>

            {/* Follow-up suggestions after the latest agent message */}
            {idx === messages.length - 1 && message.type === 'agent' && !isProcessing && !isJailed && !isTerminated && (
              <div className={styles.followUps}>
                {currentSuggestions.map((q: string) => (
                  <button 
                    key={q}
                    className={styles.followUpBtn}
                    onClick={() => handleSuggestionClick(q)}
                    disabled={isJailed}
                  >
                    {q}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}


        {isProcessing && (
          <div className={`${styles.message} ${styles.agent} ${styles.thinking}`}>
            <div className={styles.messageHeader}>
              <span className={styles.messageRole}>ATLAS-G</span>
            </div>
            <div className={styles.thinkingDots}>
              <span>●</span><span>●</span><span>●</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className={styles.inputArea}>
        {isJailed && (
          <div className={styles.blockedOverlay}>
            <span className={styles.blockedIcon}>✕</span>
            <span>ACCESS SUSPENDED</span>
          </div>
        )}
        <form className={styles.inputForm} onSubmit={handleSubmit}>
          <span className={styles.prompt}>&gt;</span>
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={isProcessing ? 'Processing...' : (isJailed ? 'SYSTEM LOCKED' : (isTerminated ? 'SESSION CONCLUDED' : placeholder))}
            disabled={isProcessing || isJailed || isTerminated}
            className={styles.input}
            autoComplete="off"
          />
          <AudioInput 
            onTranscript={handleTranscript} 
            disabled={isProcessing || isJailed || isTerminated} 
          />
          <button
            type="submit"
            disabled={isProcessing || !input.trim() || isJailed || isTerminated}
            className={styles.sendButton}
          >
            SEND
          </button>
        </form>
      </div>
    </div>
  );

};
