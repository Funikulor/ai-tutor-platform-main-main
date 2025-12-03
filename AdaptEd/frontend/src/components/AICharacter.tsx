import { useState, useEffect } from 'react';
import { motion } from 'motion/react';

interface AICharacterProps {
  emotion?: 'happy' | 'thinking' | 'excited' | 'encouraging' | 'surprised';
  isSpeaking?: boolean;
  size?: 'small' | 'medium' | 'large';
}

export function AICharacter({ emotion = 'happy', isSpeaking = false, size = 'medium' }: AICharacterProps) {
  const [blinking, setBlinking] = useState(false);

  // Blink animation
  useEffect(() => {
    const blinkInterval = setInterval(() => {
      setBlinking(true);
      setTimeout(() => setBlinking(false), 200);
    }, 3000 + Math.random() * 2000);

    return () => clearInterval(blinkInterval);
  }, []);

  const sizeClasses = {
    small: 'w-16 h-16',
    medium: 'w-24 h-24',
    large: 'w-32 h-32'
  };

  const getEyeExpression = () => {
    if (blinking) return 'h-1';
    switch (emotion) {
      case 'excited':
      case 'surprised':
        return 'h-4';
      default:
        return 'h-3';
    }
  };

  const getMouthExpression = () => {
    switch (emotion) {
      case 'happy':
      case 'excited':
        return (
          <path
            d="M 15 22 Q 20 27 25 22"
            stroke="#7c3aed"
            strokeWidth="2"
            fill="none"
            strokeLinecap="round"
          />
        );
      case 'thinking':
        return (
          <ellipse cx="20" cy="24" rx="3" ry="2" fill="#7c3aed" opacity="0.6" />
        );
      case 'encouraging':
        return (
          <path
            d="M 15 23 Q 20 26 25 23"
            stroke="#7c3aed"
            strokeWidth="2"
            fill="none"
            strokeLinecap="round"
          />
        );
      case 'surprised':
        return (
          <ellipse cx="20" cy="24" rx="3" ry="4" fill="#7c3aed" opacity="0.8" />
        );
      default:
        return (
          <path
            d="M 15 22 Q 20 25 25 22"
            stroke="#7c3aed"
            strokeWidth="2"
            fill="none"
            strokeLinecap="round"
          />
        );
    }
  };

  return (
    <motion.div
      className={`${sizeClasses[size]} relative`}
      animate={{
        y: [0, -8, 0],
        rotate: [0, 2, -2, 0]
      }}
      transition={{
        duration: 3,
        repeat: Infinity,
        ease: "easeInOut"
      }}
    >
      {/* Main body - cute robot/owl hybrid */}
      <svg viewBox="0 0 40 40" className="w-full h-full drop-shadow-lg">
        {/* Body glow effect */}
        <defs>
          <linearGradient id="bodyGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#a78bfa" />
            <stop offset="100%" stopColor="#7c3aed" />
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>

        {/* Body */}
        <circle cx="20" cy="20" r="16" fill="url(#bodyGradient)" filter="url(#glow)" />
        
        {/* Ears/Antenna */}
        <motion.circle
          cx="12" cy="8" r="3"
          fill="#c4b5fd"
          animate={{ scale: [1, 1.2, 1] }}
          transition={{ duration: 2, repeat: Infinity, delay: 0 }}
        />
        <motion.circle
          cx="28" cy="8" r="3"
          fill="#c4b5fd"
          animate={{ scale: [1, 1.2, 1] }}
          transition={{ duration: 2, repeat: Infinity, delay: 0.5 }}
        />
        
        {/* Antenna tips - glowing */}
        <motion.circle
          cx="12" cy="8" r="1.5"
          fill="#fde047"
          animate={{ opacity: [0.6, 1, 0.6] }}
          transition={{ duration: 1.5, repeat: Infinity }}
        />
        <motion.circle
          cx="28" cy="8" r="1.5"
          fill="#fde047"
          animate={{ opacity: [0.6, 1, 0.6] }}
          transition={{ duration: 1.5, repeat: Infinity, delay: 0.3 }}
        />

        {/* Face background */}
        <circle cx="20" cy="18" r="11" fill="#f5f3ff" opacity="0.9" />

        {/* Eyes */}
        <g>
          {/* Left eye */}
          <ellipse cx="15" cy="16" rx="3" ry={3.5} fill="white" />
          <motion.ellipse
            cx="15"
            cy="16"
            rx="2"
            ry={blinking ? 0.3 : 2}
            fill="#7c3aed"
            animate={emotion === 'thinking' ? { x: [0, 1, -1, 0] } : {}}
            transition={{ duration: 2, repeat: emotion === 'thinking' ? Infinity : 0 }}
          />
          <ellipse cx="15" cy="15" rx="0.8" ry="1" fill="white" opacity="0.8" />

          {/* Right eye */}
          <ellipse cx="25" cy="16" rx="3" ry={3.5} fill="white" />
          <motion.ellipse
            cx="25"
            cy="16"
            rx="2"
            ry={blinking ? 0.3 : 2}
            fill="#7c3aed"
            animate={emotion === 'thinking' ? { x: [0, 1, -1, 0] } : {}}
            transition={{ duration: 2, repeat: emotion === 'thinking' ? Infinity : 0 }}
          />
          <ellipse cx="25" cy="15" rx="0.8" ry="1" fill="white" opacity="0.8" />
        </g>

        {/* Cheeks */}
        {(emotion === 'happy' || emotion === 'excited') && (
          <>
            <circle cx="10" cy="20" r="2" fill="#fca5a5" opacity="0.5" />
            <circle cx="30" cy="20" r="2" fill="#fca5a5" opacity="0.5" />
          </>
        )}

        {/* Mouth */}
        <motion.g
          animate={isSpeaking ? { scaleY: [1, 1.2, 1] } : {}}
          transition={{ duration: 0.3, repeat: isSpeaking ? Infinity : 0 }}
        >
          {getMouthExpression()}
        </motion.g>

        {/* Sparkles when excited or happy */}
        {(emotion === 'excited' || emotion === 'happy') && (
          <>
            <motion.circle
              cx="8" cy="12" r="1"
              fill="#fde047"
              animate={{ opacity: [0, 1, 0], scale: [0, 1, 0] }}
              transition={{ duration: 2, repeat: Infinity, delay: 0 }}
            />
            <motion.circle
              cx="32" cy="12" r="1"
              fill="#fde047"
              animate={{ opacity: [0, 1, 0], scale: [0, 1, 0] }}
              transition={{ duration: 2, repeat: Infinity, delay: 0.7 }}
            />
            <motion.circle
              cx="20" cy="6" r="1"
              fill="#fde047"
              animate={{ opacity: [0, 1, 0], scale: [0, 1, 0] }}
              transition={{ duration: 2, repeat: Infinity, delay: 1.4 }}
            />
          </>
        )}
      </svg>

      {/* Speech indicator */}
      {isSpeaking && (
        <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2 flex gap-1">
          <motion.div
            className="w-2 h-2 bg-purple-400 rounded-full"
            animate={{ scale: [1, 1.5, 1], opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1, repeat: Infinity, delay: 0 }}
          />
          <motion.div
            className="w-2 h-2 bg-purple-400 rounded-full"
            animate={{ scale: [1, 1.5, 1], opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1, repeat: Infinity, delay: 0.2 }}
          />
          <motion.div
            className="w-2 h-2 bg-purple-400 rounded-full"
            animate={{ scale: [1, 1.5, 1], opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1, repeat: Infinity, delay: 0.4 }}
          />
        </div>
      )}
    </motion.div>
  );
}
