import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, Cpu, Terminal, Calculator, ChevronDown, ChevronUp } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import './App.css';

const TraceBlock = ({ toolCall, toolResponse }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="trace-block" onClick={() => setIsOpen(!isOpen)}>
      <div className="trace-header">
        <Cpu size={16} />
        <span>Tool Call: {toolCall.name}</span>
        {isOpen ? <ChevronUp size={16} style={{ marginLeft: 'auto' }} /> : <ChevronDown size={16} style={{ marginLeft: 'auto' }} />}
      </div>
      {isOpen && (
        <div className="trace-content">
          <div className="trace-item">
            <span className="trace-label">Input</span>
            <pre className="trace-value">{JSON.stringify(toolCall.args, null, 2)}</pre>
          </div>
          <div className="trace-item">
            <span className="trace-label">Output</span>
            <pre className="trace-value">{JSON.stringify(toolResponse.response, null, 2)}</pre>
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
  const [status, setStatus] = useState('');
  const [availableTools, setAvailableTools] = useState([]);
  const scrollRef = useRef(null);

  useEffect(() => {
    // Fetch available tools on mount
    fetch('http://127.0.0.1:5000/api/tools')
      .then(res => res.json())
      .then(data => setAvailableTools(data.tools || []))
      .catch(err => console.error('Failed to fetch tools:', err));
  }, []);

  useEffect(() => {
    localStorage.setItem('agent_chat_history', JSON.stringify(messages));
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading, status]);

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
    
    // Optimistically update messages
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    
    const currentInput = input;
    setInput('');
    setIsLoading(true);
    setStatus('Thinking...');

    try {
      const response = await fetch('http://127.0.0.1:5000/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          prompt: currentInput,
          history: messages
        }),
      });

      if (!response.body) throw new Error('No response body');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              if (data.type === 'tool_call') {
                setStatus(`Calling tool: ${data.name}...`);
              } else if (data.type === 'tool_result') {
                setStatus(`Processed: ${data.name}`);
              } else if (data.type === 'model') {
                setStatus('Finalizing...');
              } else if (data.type === 'done') {
                setMessages(data.history);
                setStatus('');
              } else if (data.type === 'error') {
                setMessages(prev => [...prev, { role: 'system', parts: [{ text: `Error: ${data.error}` }] }]);
                setStatus('');
              }
            } catch (e) {
              console.error('Error parsing stream line:', e);
            }
          }
        }
      }
    } catch (err) {
      console.error('Stream error:', err);
      setMessages(prev => [...prev, { role: 'system', parts: [{ text: 'Failed to connect to agent server.' }] }]);
      setStatus('');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="main-layout">
      <nav className="nav-sidebar">
        <div className="nav-header">
          <Terminal size={16} />
          <span>Sessions</span>
        </div>
        <div className="nav-content">
          <div className="nav-item active">Current Session</div>
          <div className="nav-placeholder">History Coming Soon</div>
        </div>
      </nav>

      <div className="chat-section">
        <header className="app-header">
          <h1 className="app-title">Agent</h1>
          <button onClick={clearHistory} className="clear-btn">
            Clear
          </button>
        </header>

        <div className="chat-container" ref={scrollRef}>
          <div className="messages-wrapper">
            {messages.length === 0 && (
              <div className="empty-state">
                <Bot size={48} />
                <p>Ready to assist.</p>
              </div>
            )}

            {messages.map((msg, i) => {
              const parts = Array.isArray(msg.parts) ? msg.parts : [];
              const textPart = msg.text || parts.find(p => p.text)?.text;
              const toolCall = parts.find(p => p.function_call)?.function_call;

              // Hide tool responses from the main chat flow
              if (msg.role === 'tool') return null;

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
                  <span>{status || 'Thinking...'}</span>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="input-container">
          <form onSubmit={handleSubmit} className="input-wrapper">
            <input
              type="text"
              placeholder="Describe a task..."
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

      <aside className="tool-sidebar">
        <div className="sidebar-header">
          <Cpu size={16} />
          <span>Tools & Execution</span>
        </div>
        <div className="sidebar-content">
          <section className="available-tools">
            <h3 className="section-title">Available Tools</h3>
            <div className="tool-list">
              {availableTools.map((tool, idx) => (
                <div key={idx} className="tool-tag" title={tool.description}>
                  {tool.name === 'calculate' ? <Calculator size={12} /> : <Terminal size={12} />}
                  <span>{tool.name}</span>
                </div>
              ))}
              {availableTools.length === 0 && (
                <div className="tool-tag disabled">
                  <span>No tools connected</span>
                </div>
              )}
            </div>
          </section>

          <div className="logs-separator"></div>

          <h3 className="section-title">Execution Logs</h3>
          {messages.map((msg, i) => {
            if (msg.role === 'tool') {
              const toolResponse = msg.parts?.find(p => p.function_response)?.function_response;
              const prevMsg = messages[i - 1];
              const prevParts = Array.isArray(prevMsg?.parts) ? prevMsg.parts : [];
              const matchingCall = prevParts.find(p => p.function_call)?.function_call;

              if (matchingCall && toolResponse) {
                return <TraceBlock key={i} toolCall={matchingCall} toolResponse={toolResponse} />;
              }
            }
            return null;
          })}
          {messages.filter(m => m.role === 'tool').length === 0 && (
            <div className="sidebar-empty">
              No tool calls yet.
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}

export default App;
