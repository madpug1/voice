import { useState, useRef, useEffect } from 'react';
import './index.css';

const API_BASE = 'http://localhost:8000';

function App() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const synthRef = useRef(window.speechSynthesis);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initialize speech recognition
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onstart = () => {
        setIsListening(true);
      };

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        handleVoiceInput(transcript);
      };

      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
        if (event.error === 'no-speech') {
          showToast('No speech detected. Please try again.', 'error');
        } else if (event.error === 'not-allowed') {
          showToast('Microphone access denied. Please enable it in browser settings.', 'error');
        } else {
          showToast(`Error: ${event.error}`, 'error');
        }
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    } else {
      showToast('Speech recognition not supported in this browser. Please use Chrome or Edge.', 'error');
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const startListening = () => {
    if (recognitionRef.current && !isListening && !loading) {
      // Stop any ongoing speech
      if (isSpeaking) {
        synthRef.current.cancel();
        setIsSpeaking(false);
      }
      recognitionRef.current.start();
    }
  };

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
    }
  };

  const speakText = (text) => {
    if ('speechSynthesis' in window) {
      // Cancel any ongoing speech
      synthRef.current.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      utterance.volume = 1.0;

      utterance.onstart = () => {
        setIsSpeaking(true);
      };

      utterance.onend = () => {
        setIsSpeaking(false);
      };

      utterance.onerror = (event) => {
        console.error('Speech synthesis error:', event);
        setIsSpeaking(false);
      };

      synthRef.current.speak(utterance);
    }
  };

  const handleVoiceInput = async (transcript) => {
    if (!transcript.trim() || loading) return;

    const userMessage = { role: 'user', content: transcript };
    setMessages(prev => [...prev, userMessage]);
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: transcript }),
      });

      if (!response.ok) {
        throw new Error('Query failed');
      }

      const data = await response.json();
      const aiMessage = {
        role: 'ai',
        content: data.answer,
        sources: data.num_sources,
      };
      setMessages(prev => [...prev, aiMessage]);

      // Automatically speak the response
      speakText(data.answer);
    } catch (error) {
      const errorMessage = {
        role: 'ai',
        content: 'Sorry, I encountered an error. Please make sure the backend is running.',
      };
      setMessages(prev => [...prev, errorMessage]);
      showToast('Query failed. Check backend connection.', 'error');
      speakText('Sorry, I encountered an error processing your request.');
    } finally {
      setLoading(false);
    }
  };

  const stopSpeaking = () => {
    if (isSpeaking) {
      synthRef.current.cancel();
      setIsSpeaking(false);
    }
  };

  return (
    <div className="app">
      <div className="header">
        <h1>🎤 Voice Assistant</h1>
        <p>Speak to ask questions about your documents</p>
      </div>

      <div className="chat-container">
        <div className="status-bar">
          <div className="status-indicator">
            <div className="status-dot"></div>
            <span>Ready - PDFs auto-loaded</span>
          </div>
          {isSpeaking && (
            <button
              className="stop-button"
              onClick={stopSpeaking}
            >
              🔇 Stop Speaking
            </button>
          )}
        </div>

        <div className="messages">
          {messages.length === 0 ? (
            <div className="empty-state">
              <h2>👋 Welcome!</h2>
              <p>Your PDFs have been automatically loaded.</p>
              <p>Click the microphone button below and speak your question!</p>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div key={idx} className={`message ${msg.role}`}>
                <div className="message-avatar">
                  {msg.role === 'user' ? '👤' : '🤖'}
                </div>
                <div className="message-content">
                  {msg.content}
                  {msg.sources && (
                    <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', opacity: 0.7 }}>
                      📄 {msg.sources} source{msg.sources > 1 ? 's' : ''} found
                    </div>
                  )}
                </div>
              </div>
            ))
          )}

          {loading && (
            <div className="message ai">
              <div className="message-avatar">🤖</div>
              <div className="message-content">
                <div className="loading-dots">
                  <div className="loading-dot"></div>
                  <div className="loading-dot"></div>
                  <div className="loading-dot"></div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="voice-controls">
          <button
            className={`mic-button ${isListening ? 'listening' : ''}`}
            onClick={isListening ? stopListening : startListening}
            disabled={loading || isSpeaking}
          >
            <div className="mic-icon">
              {isListening ? '🔴' : '🎤'}
            </div>
            <div className="mic-text">
              {isListening ? 'Listening...' : isSpeaking ? 'Speaking...' : 'Tap to Speak'}
            </div>
          </button>
        </div>
      </div>

      {toast && (
        <div className={`toast ${toast.type}`}>
          {toast.message}
        </div>
      )}
    </div>
  );
}

export default App;
