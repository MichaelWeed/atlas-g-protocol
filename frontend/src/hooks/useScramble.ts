import { useState, useEffect, useRef } from 'react';

const CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*';

/**
 * useScramble - "Decryption" text effect hook
 * Cycles through random characters before settling on the real value.
 * 
 * @param finalText - The text to reveal after scrambling
 * @param duration - Total duration of the scramble effect in ms (default: 400)
 * @param delay - Delay before starting the scramble in ms (default: 0)
 */
export function useScramble(
  finalText: string,
  duration: number = 400,
  delay: number = 0
): string {
  const [displayText, setDisplayText] = useState('');
  const frameRef = useRef<number | undefined>(undefined);
  const startTimeRef = useRef<number | undefined>(undefined);

  useEffect(() => {
    let timeoutId: ReturnType<typeof setTimeout>;
    
    const scramble = (timestamp: number) => {
      if (!startTimeRef.current) {
        startTimeRef.current = timestamp;
      }
      
      const elapsed = timestamp - startTimeRef.current;
      const progress = Math.min(elapsed / duration, 1);
      
      // Calculate how many characters should be "locked in"
      const lockedChars = Math.floor(progress * finalText.length);
      
      // Build the display string
      let result = '';
      for (let i = 0; i < finalText.length; i++) {
        if (i < lockedChars) {
          // This character is locked - show the real character
          result += finalText[i];
        } else if (finalText[i] === ' ') {
          // Preserve spaces
          result += ' ';
        } else {
          // Still scrambling - show random character
          result += CHARS[Math.floor(Math.random() * CHARS.length)];
        }
      }
      
      setDisplayText(result);
      
      if (progress < 1) {
        frameRef.current = requestAnimationFrame(scramble);
      }
    };
    
    // Start after delay
    timeoutId = setTimeout(() => {
      startTimeRef.current = undefined;
      frameRef.current = requestAnimationFrame(scramble);
    }, delay);
    
    return () => {
      clearTimeout(timeoutId);
      if (frameRef.current) {
        cancelAnimationFrame(frameRef.current);
      }
    };
  }, [finalText, duration, delay]);

  return displayText;
}
