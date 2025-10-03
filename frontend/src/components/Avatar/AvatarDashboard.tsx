import React, { useState, useEffect, useRef } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera } from '@react-three/drei';
import { motion, AnimatePresence } from 'framer-motion';
import Webcam from 'react-webcam';
import * as faceapi from 'face-api.js';
import { useSpeechSynthesis } from 'react-speech-kit';
import Avatar3D from './Avatar3D';
import EmotionAnalyzer from './EmotionAnalyzer';
import VoiceController from './VoiceController';
import StyleCustomizer from './StyleCustomizer';
import AIPersonalityEngine from './AIPersonalityEngine';
import MetricsPanel from './MetricsPanel';
import { useAvatarStore } from '../../hooks/useAvatarStore';
import { AvatarService } from '../../services/avatarService';
import './AvatarDashboard.css';

interface AvatarDashboardProps {
  userId: string;
  brandProfile: any;
}

const AvatarDashboard: React.FC<AvatarDashboardProps> = ({ userId, brandProfile }) => {
  const [avatarMode, setAvatarMode] = useState<'fashion' | 'assistant' | 'mirror'>('assistant');
  const [isListening, setIsListening] = useState(false);
  const [emotion, setEmotion] = useState('neutral');
  const [avatarStyle, setAvatarStyle] = useState({
    skinTone: '#F5DEB3',
    hairColor: '#2C1810',
    eyeColor: '#4A90E2',
    outfit: 'luxury_suit',
    accessories: []
  });
  
  const webcamRef = useRef<Webcam>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { speak, speaking } = useSpeechSynthesis();
  const avatarStore = useAvatarStore();
  const avatarService = new AvatarService();

  // Initialize face detection
  useEffect(() => {
    const loadModels = async () => {
      await Promise.all([
        faceapi.nets.tinyFaceDetector.loadFromUri('/models'),
        faceapi.nets.faceLandmark68Net.loadFromUri('/models'),
        faceapi.nets.faceRecognitionNet.loadFromUri('/models'),
        faceapi.nets.faceExpressionNet.loadFromUri('/models')
      ]);
    };
    loadModels();
  }, []);

  // Real-time emotion detection from webcam
  const detectEmotion = async () => {
    if (webcamRef.current?.video) {
      const detections = await faceapi
        .detectAllFaces(webcamRef.current.video as HTMLVideoElement, 
          new faceapi.TinyFaceDetectorOptions())
        .withFaceLandmarks()
        .withFaceExpressions();

      if (detections.length > 0) {
        const expressions = detections[0].expressions;
        const dominantEmotion = Object.keys(expressions).reduce((a, b) => 
          expressions[a as keyof typeof expressions] > expressions[b as keyof typeof expressions] ? a : b
        );
        setEmotion(dominantEmotion);
      }
    }
  };

  // Fashion Mode - Virtual Try-On
  const FashionMode = () => (
    <div className="fashion-mode">
      <div className="virtual-mirror">
        <Canvas>
          <PerspectiveCamera makeDefault position={[0, 0, 5]} />
          <OrbitControls enablePan={false} enableZoom={true} />
          <ambientLight intensity={0.5} />
          <directionalLight position={[10, 10, 5]} intensity={1} />
          <Avatar3D 
            style={avatarStyle}
            emotion={emotion}
            animation="pose"
            outfit={avatarStore.selectedOutfit}
          />
        </Canvas>
      </div>
      <div className="outfit-selector">
        <h3>Try On Collection</h3>
        {brandProfile.collections.map((item: any) => (
          <motion.div 
            key={item.id}
            className="outfit-card"
            whileHover={{ scale: 1.05 }}
            onClick={() => avatarStore.setSelectedOutfit(item)}
          >
            <img src={item.thumbnail} alt={item.name} />
            <p>{item.name}</p>
            <span>${item.price}</span>
          </motion.div>
        ))}
      </div>
    </div>
  );

  // Assistant Mode - AI Personal Stylist
  const AssistantMode = () => (
    <div className="assistant-mode">
      <div className="avatar-container">
        <Canvas>
          <PerspectiveCamera makeDefault position={[0, 1, 3]} />
          <OrbitControls enablePan={false} enableZoom={false} />
          <ambientLight intensity={0.6} />
          <directionalLight position={[5, 5, 5]} intensity={1} />
          <Avatar3D 
            style={avatarStyle}
            emotion={emotion}
            animation={speaking ? "talking" : "idle"}
            lipSync={avatarStore.currentPhoneme}
          />
        </Canvas>
      </div>
      <AIPersonalityEngine 
        onResponse={(text) => {
          speak({ text, voice: avatarStore.voice });
        }}
        personality="luxury_fashion_expert"
        context={brandProfile}
      />
      <VoiceController 
        isListening={isListening}
        onToggle={() => setIsListening(!isListening)}
        onTranscript={(text) => avatarStore.processUserInput(text)}
      />
    </div>
  );

  // Mirror Mode - Real-time Expression Mirroring
  const MirrorMode = () => (
    <div className="mirror-mode">
      <div className="webcam-feed">
        <Webcam
          ref={webcamRef}
          audio={false}
          mirrored={true}
          onUserMedia={() => {
            setInterval(detectEmotion, 100);
          }}
        />
      </div>
      <div className="avatar-mirror">
        <Canvas>
          <PerspectiveCamera makeDefault position={[0, 0, 4]} />
          <ambientLight intensity={0.7} />
          <directionalLight position={[5, 5, 5]} intensity={1} />
          <Avatar3D 
            style={avatarStyle}
            emotion={emotion}
            animation="mirroring"
            facialTracking={avatarStore.facialLandmarks}
          />
        </Canvas>
      </div>
    </div>
  );

  return (
    <motion.div 
      className="avatar-dashboard"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      {/* Mode Selector */}
      <div className="mode-selector">
        <motion.button
          className={avatarMode === 'fashion' ? 'active' : ''}
          onClick={() => setAvatarMode('fashion')}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
        >
          <span className="icon">👗</span>
          Fashion Try-On
        </motion.button>
        <motion.button
          className={avatarMode === 'assistant' ? 'active' : ''}
          onClick={() => setAvatarMode('assistant')}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
        >
          <span className="icon">🤖</span>
          AI Stylist
        </motion.button>
        <motion.button
          className={avatarMode === 'mirror' ? 'active' : ''}
          onClick={() => setAvatarMode('mirror')}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
        >
          <span className="icon">🪞</span>
          Expression Mirror
        </motion.button>
      </div>

      {/* Main Content Area */}
      <div className="dashboard-content">
        <AnimatePresence mode="wait">
          {avatarMode === 'fashion' && <FashionMode />}
          {avatarMode === 'assistant' && <AssistantMode />}
          {avatarMode === 'mirror' && <MirrorMode />}
        </AnimatePresence>
      </div>

      {/* Customization Panel */}
      <StyleCustomizer 
        currentStyle={avatarStyle}
        onStyleChange={setAvatarStyle}
        premiumFeatures={avatarStore.premiumFeatures}
      />

      {/* Emotion Display */}
      <EmotionAnalyzer 
        currentEmotion={emotion}
        emotionHistory={avatarStore.emotionHistory}
      />

      {/* Metrics Panel */}
      <MetricsPanel 
        interactions={avatarStore.interactions}
        engagementScore={avatarStore.engagementScore}
        recommendations={avatarStore.styleRecommendations}
      />

      {/* Floating Action Buttons */}
      <div className="floating-actions">
        <motion.button
          className="fab screenshot"
          onClick={() => avatarService.captureAvatar(canvasRef.current)}
          whileHover={{ scale: 1.2 }}
          whileTap={{ scale: 0.9 }}
        >
          📸
        </motion.button>
        <motion.button
          className="fab share"
          onClick={() => avatarService.shareToSocial()}
          whileHover={{ scale: 1.2 }}
          whileTap={{ scale: 0.9 }}
        >
          🔗
        </motion.button>
        <motion.button
          className="fab reset"
          onClick={() => avatarStore.resetAvatar()}
          whileHover={{ scale: 1.2 }}
          whileTap={{ scale: 0.9 }}
        >
          🔄
        </motion.button>
      </div>
    </motion.div>
  );
};

export default AvatarDashboard;
