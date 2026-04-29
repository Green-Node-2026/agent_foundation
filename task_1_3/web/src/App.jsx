import React, { useState, useRef, useEffect } from 'react';
import { Send, Calculator, Terminal, ChevronDown, ChevronUp } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import './App.css';

const TraceBlock = ({ toolCall, toolResponse }) => {
  const [isOpen, setIsOpen] = useState(false);
  
  return (
    <div className="trace-block" onClick={() => setIsOpen(!isOpen)}>
      <div className="trace-header">
        <Calculator size={16} />
        <span>Tool Call: {toolCall.name}</span>
        {isOpen ? <ChevronUp size={16} style={{ marginLeft: 'auto' }} /> : <ChevronDown size={16} style={{ marginLeft: 'auto' }} />}
      </div>
      {isOpen && (
        <div className="trace-content">
          <div style={{ marginBottom: '0.5rem' }}>
            <span style={{ color: 'var(--accent-color)', fontWeight: 'bold' }}>Input:</span>
            <pre style={{ margin: '0.25rem 0' }}>{JSON.stringify(toolCall.args, null, 2)}</pre>
          </div>
          <div>
            <span style={{ color: 'var(--accent-color)', fontWeight: 'bold' }}>Output:</span>
            <pre style={{ margin: '0.25rem 0' }}>{JSON.stringify(toolResponse.response, null, 2)}</pre>
          </div>
        </div>
      )}
    </div>
  );
};

function App() {
  const [messages, setMessages] = useState(() => {
    const saved = localStorage.getItem('agent_chat_history');
    return saved ? JSON.parse(saved) : [];
  });
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    localStorage.setItem('agent_chat_history', JSON.stringify(messages));
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const clearHistory = () => {
    setMessages([]);
    localStorage.removeItem('agent_chat_history');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = { 
      role: 'user', 
      parts: [{ text: input }] 
    };
    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:5000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: currentInput }),
      });
      
      const data = await response.json();
      if (data.history) {
        setMessages(data.history);
      } else if (data.error) {
        setMessages(prev => [...prev, { role: 'system', parts: [{ text: `Error: ${data.error}` }] }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'system', parts: [{ text: 'Failed to connect to agent server.' }] }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <header style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ flex: 1 }}></div>
        <div style={{ textAlign: 'center' }}>
          <h1 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 600 }}>Calculator Agent</h1>
        </div>
        <div style={{ flex: 1, display: 'flex', justifyContent: 'flex-end' }}>
          <button 
            onClick={clearHistory}
            style={{ 
              background: 'transparent', 
              border: '1px solid var(--border-color)', 
              color: 'var(--text-color)',
              padding: '0.5rem 0.75rem',
              borderRadius: '0.5rem',
              fontSize: '0.75rem',
              cursor: 'pointer',
              opacity: 0.7
            }}
          >
            Clear History
          </button>
        </div>
      </header>

      <div className="chat-container" ref={scrollRef}>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', marginTop: '4rem', opacity: 0.5 }}>
            <Calculator size={48} style={{ marginBottom: '1rem' }} />
            <p>Ask me to calculate something, like "(45 * 2) / 5"</p>
          </div>
        )}
        
        {messages.map((msg, i) => {
          // Process Gemini style history
          const parts = Array.isArray(msg.parts) ? msg.parts : [];
          const textPart = msg.text || parts.find(p => p.text)?.text;
          const toolCall = parts.find(p => p.function_call)?.function_call;
          const toolResponse = parts.find(p => p.function_response)?.function_response;

          if (msg.role === 'tool') {
            // Find the corresponding function_call in the previous model message
            const prevMsg = messages[i-1];
            const prevParts = Array.isArray(prevMsg?.parts) ? prevMsg.parts : [];
            const matchingCall = prevParts.find(p => p.function_call)?.function_call;
            if (matchingCall && toolResponse) {
               return <TraceBlock key={i} toolCall={matchingCall} toolResponse={toolResponse} />;
            }
            return null;
          }

          if (!textPart && !toolCall) return null;

          const isLastMessage = i === messages.length - 1;

          return (
            <div key={i} className={`message ${msg.role === 'user' ? 'user' : 'agent'}`}>
              {textPart && (
                <div className="bubble">
                  {msg.role === 'user' ? textPart : <ReactMarkdown>{textPart}</ReactMarkdown>}
                </div>
              )}
              {toolCall && !textPart && isLastMessage && isLoading && (
                <div className="thinking">
                  <div className="spinner"></div>
                  <span>Calling tool: {toolCall.name}...</span>
                </div>
              )}
            </div>
          );
        })}

        {isLoading && (
          <div className="message agent">
            <div className="thinking">
              <div className="spinner"></div>
              <span>Agent is thinking...</span>
            </div>
          </div>
        )}
      </div>

      <div className="input-container">
        <form onSubmit={handleSubmit} className="input-wrapper">
          <input
            type="text"
            placeholder="Enter a prompt with a math expression..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
          />
          <button type="submit" className="send-button" disabled={isLoading || !input.trim()}>
            <Send size={20} />
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;
