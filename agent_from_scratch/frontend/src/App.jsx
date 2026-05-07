import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Bot, Cpu, Terminal, Calculator, ChevronDown, ChevronUp, Paperclip, X, Plus } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import oneDark from 'react-syntax-highlighter/dist/esm/styles/prism/one-dark';
import oneLight from 'react-syntax-highlighter/dist/esm/styles/prism/one-light';
import 'katex/dist/katex.min.css';
import './App.css';

const TraceBlock = ({ toolCall, toolResponse }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="trace-block" onClick={() => setIsOpen(!isOpen)}>
      <div className="trace-header">
        <Cpu size={16} />
        <span>Action: {toolCall.name}</span>
        {isOpen ? <ChevronUp size={16} style={{ marginLeft: 'auto' }} /> : <ChevronDown size={16} style={{ marginLeft: 'auto' }} />}
      </div>
      {isOpen && (
        <div className="trace-content">
          <div className="trace-item">
            <span className="trace-label">Arguments</span>
            <pre className="trace-value">{JSON.stringify(toolCall.args, null, 2)}</pre>
          </div>
          <div className="trace-item">
            <span className="trace-label">Observation</span>
            <pre className="trace-value">{JSON.stringify(toolResponse.response, null, 2)}</pre>
          </div>
        </div>
      )}
    </div>
  );
};

const API_BASE = 'http://127.0.0.1:5000';

function getOrCreateUserId() {
  let id = localStorage.getItem('agent_user_id');
  if (!id) {
    id = (crypto?.randomUUID && crypto.randomUUID()) || `u_${Date.now()}_${Math.random().toString(36).slice(2)}`;
    localStorage.setItem('agent_user_id', id);
  }
  return id;
}

function App() {
  const [userId] = useState(getOrCreateUserId);
  const [messages, setMessages] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState('');
  const [availableTools, setAvailableTools] = useState([]);
  const [dailyUsage, setDailyUsage] = useState({ total_tokens: 0, total_cost: 0 });
  const [attachedFile, setAttachedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const scrollRef = useRef(null);
  const fileInputRef = useRef(null);

  const apiHeaders = useCallback((sessionId = null) => {
    const h = { 'X-User-Id': userId };
    if (sessionId) h['X-Session-Id'] = sessionId;
    return h;
  }, [userId]);

  const refreshSessions = useCallback(async () => {
    const res = await fetch(`${API_BASE}/api/sessions`, { headers: apiHeaders() });
    const data = await res.json();
    const list = data.sessions || [];
    setSessions(list);
    return list;
  }, [apiHeaders]);

  const switchToSession = useCallback(async (sessionId) => {
    const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`, { headers: apiHeaders() });
    if (!res.ok) {
      console.error('Failed to load session', sessionId);
      return;
    }
    const record = await res.json();
    setMessages(record.messages || []);
    setCurrentSessionId(sessionId);
  }, [apiHeaders]);

  const startNewSession = useCallback(async () => {
    const res = await fetch(`${API_BASE}/api/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...apiHeaders() },
      body: JSON.stringify({ title: '' }),
    });
    const record = await res.json();
    setMessages([]);
    setCurrentSessionId(record.session_id);
    await refreshSessions();
  }, [apiHeaders, refreshSessions]);

  const removeSession = useCallback(async (sessionId) => {
    await fetch(`${API_BASE}/api/sessions/${sessionId}`, {
      method: 'DELETE',
      headers: apiHeaders(),
    });
    const remaining = await refreshSessions();
    if (sessionId === currentSessionId) {
      if (remaining.length > 0) {
        await switchToSession(remaining[0].session_id);
      } else {
        await startNewSession();
      }
    }
  }, [apiHeaders, currentSessionId, refreshSessions, switchToSession, startNewSession]);

  useEffect(() => {
    fetch(`${API_BASE}/api/tools`)
      .then(res => res.json())
      .then(data => setAvailableTools(data.tools || []))
      .catch(err => console.error('Failed to fetch tools:', err));

    fetch(`${API_BASE}/api/usage`, { headers: { 'X-User-Id': userId } })
      .then(res => res.json())
      .then(setDailyUsage)
      .catch(err => console.error('Failed to fetch usage:', err));

    (async () => {
      try {
        const list = await refreshSessions();
        if (list.length > 0) {
          await switchToSession(list[0].session_id);
        } else {
          await startNewSession();
        }
      } catch (err) {
        console.error('Failed to bootstrap sessions:', err);
      }
    })();
  }, [userId, refreshSessions, switchToSession, startNewSession]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading, status]);

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsUploading(true);
    setAttachedFile({ name: file.name, status: 'uploading' });

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE}/api/upload`, {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();

      if (data.status === 'success') {
        setAttachedFile({
          name: file.name,
          serverName: data.filename,
          path: data.path,
          status: 'success'
        });
      } else {
        throw new Error(data.error || 'Upload failed');
      }
    } catch (err) {
      console.error('Upload error:', err);
      setAttachedFile({ name: file.name, status: 'error' });
    } finally {
      setIsUploading(false);
    }
  };

  const removeFile = () => {
    setAttachedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if ((!input.trim() && !attachedFile) || isLoading || isUploading) return;
    if (!currentSessionId) return;

    let uploadedFileName = attachedFile?.status === 'success' ? attachedFile.serverName : '';
    const finalPrompt = input + (uploadedFileName ? `\n\n[Attached File: ${uploadedFileName}]` : '');

    const userMessage = {
      role: 'user',
      parts: [{ text: finalPrompt }]
    };

    setMessages([...messages, userMessage]);

    setInput('');
    setAttachedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    setIsLoading(true);
    setStatus('Thinking...');

    try {
      const response = await fetch(`${API_BASE}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...apiHeaders(currentSessionId) },
        body: JSON.stringify({ prompt: finalPrompt }),
      });

      if (!response.body) throw new Error('No response body');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // Keep the partial line in buffer

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith('data: ')) {
            try {
              const data = JSON.parse(trimmed.slice(6));

              if (data.type === 'tool_call') {
                setStatus(`Action: ${data.name}...`);
              } else if (data.type === 'tool_result') {
                setStatus(`Observation: ${data.name}`);
              } else if (data.type === 'model') {
                setStatus('Finalizing...');
              } else if (data.type === 'done') {
                const history = data.history || [];
                if (data.usage && history.length > 0) {
                  history[history.length - 1].usage = data.usage;
                }
                setMessages(history);
                setStatus('');

                fetch(`${API_BASE}/api/usage`, { headers: { 'X-User-Id': userId } })
                  .then(r => r.json())
                  .then(setDailyUsage)
                  .catch(err => console.error('usage refresh failed:', err));

                refreshSessions().catch(err => console.error('sessions refresh failed:', err));
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
          <button onClick={startNewSession} className="new-chat-btn" disabled={isLoading}>
            <Plus size={14} />
            <span>New Chat</span>
          </button>
          <div className="sessions-list">
            {sessions.map(s => (
              <div
                key={s.session_id}
                className={`session-item ${s.session_id === currentSessionId ? 'active' : ''}`}
                onClick={() => !isLoading && switchToSession(s.session_id)}
              >
                <span className="session-title">{s.title || 'Untitled'}</span>
                <button
                  type="button"
                  className="session-delete"
                  onClick={(e) => { e.stopPropagation(); removeSession(s.session_id); }}
                  aria-label="Delete session"
                >
                  <X size={12} />
                </button>
              </div>
            ))}
            {sessions.length === 0 && (
              <div className="nav-placeholder">No sessions yet</div>
            )}
          </div>
        </div>
        
        <div className="logs-separator"></div>

        <div className="nav-header">
          <Cpu size={16} />
          <span>Quota</span>
        </div>
        <div className="nav-content usage-sidebar">
          <div className="usage-item">
            <span className="usage-label">Prompt</span>
            <span className="usage-value">{dailyUsage.prompt_tokens?.toLocaleString() || 0}</span>
          </div>
          <div className="usage-item">
            <span className="usage-label">Completion</span>
            <span className="usage-value">{dailyUsage.completion_tokens?.toLocaleString() || 0}</span>
          </div>
          <div className="usage-item">
            <span className="usage-label">Requests</span>
            <span className="usage-value">{dailyUsage.requests || 0}</span>
          </div>
          <div className="usage-item">
            <span className="usage-label">Total Tokens</span>
            <span className="usage-value">{dailyUsage.total_tokens?.toLocaleString() || 0}</span>
          </div>
        </div>
      </nav>

      <div className="chat-section">
        <header className="app-header">
          <h1 className="app-title">Agent</h1>
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
              const isAgent = msg.role === 'assistant';

              return (
                <div key={i} className={`message ${msg.role === 'user' ? 'user' : 'agent'}`}>
                  {textPart && (
                    <div className="bubble">
                      {msg.role === 'user' ? (
                        textPart
                      ) : (
                        <ReactMarkdown 
                          remarkPlugins={[remarkGfm, remarkMath]}
                          rehypePlugins={[rehypeKatex]}
                          components={{
                            code({node, inline, className, children, ...props}) {
                              const match = /language-(\w+)/.exec(className || '')
                              const language = match ? match[1] : ''
                              return !inline && language ? (
                                <SyntaxHighlighter
                                  children={String(children).replace(/\n$/, '')}
                                  style={oneDark}
                                  language={language}
                                  PreTag="div"
                                  {...props}
                                />
                              ) : (
                                <code className={className} {...props}>
                                  {children}
                                </code>
                              )
                            }
                          }}
                        >
                          {textPart}
                        </ReactMarkdown>
                      )}
                      {isAgent && msg.usage && (
                        <div className="message-usage">
                          {msg.usage.total_tokens} tokens
                        </div>
                      )}
                    </div>
                  )}
                  {toolCall && !textPart && isLastMessage && isLoading && (
                    <div className="thinking">
                      <div className="spinner"></div>
                      <span>Action: {toolCall.name}...</span>
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
          {attachedFile && (
            <div className={`file-preview ${attachedFile.status}`}>
              {attachedFile.status === 'uploading' ? (
                <div className="spinner sm"></div>
              ) : (
                <Paperclip size={14} />
              )}
              <span>{attachedFile.name}</span>
              {attachedFile.status !== 'uploading' && (
                <button onClick={removeFile} className="remove-file">
                  <X size={14} />
                </button>
              )}
            </div>
          )}
          <form onSubmit={handleSubmit} className="input-wrapper">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              style={{ display: 'none' }}
            />
            <button 
              type="button" 
              className="attach-button" 
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading || isUploading}
            >
              <Paperclip size={20} />
            </button>
            <input
              type="text"
              placeholder={isUploading ? "Uploading file..." : "Describe a task..."}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading}
            />
            <button type="submit" className="send-button" disabled={isLoading || isUploading || (!input.trim() && !attachedFile)}>
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
