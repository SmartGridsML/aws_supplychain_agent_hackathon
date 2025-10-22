// src/App.tsx - The winning, type-safe frontend
import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';
import { FiSend, FiZap, FiTrendingUp, FiAlertTriangle, FiTarget, FiClock, FiActivity } from 'react-icons/fi';

//const API_GATEWAY_URL = 'https://qhzq4okx30.execute-api.us-east-1.amazonaws.com/prod/query';
const API_GATEWAY_URL = 'https://qib5nbuglb.execute-api.us-east-1.amazonaws.com/prod';

interface ToolCall {
  tool_name: string;
  input?: any;
  timestamp?: string;
}

interface AutonomousAction {
  action_id?: string;
  action_type: string;
  status: string;
  description?: string;
  timestamp?: string;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  isStreaming?: boolean;
  // Backend metadata
  traceId?: string;
  toolsCalled?: ToolCall[];
  autonomousActions?: AutonomousAction[];
  duration?: number;
  agentType?: string;
  agentId?: string;
}

interface ApiResponse {
  response: string;
  trace_id: string;
  agent_type?: string;
  agent_id?: string;
  tools_called?: ToolCall[];
  autonomous_actions?: AutonomousAction[];
  duration_ms?: number;
  timestamp: string;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputQuery, setInputQuery] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [conversationId] = useState<string>(`conv-${Date.now()}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setMessages([{
      role: 'assistant',
      content: 'Hello! I\'m your AI-powered supply chain assistant. I can help you analyze risks, simulate crisis scenarios, and predict future disruptions. What would you like to explore?',
      timestamp: new Date().toISOString()
    }]);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const quickPrompts = [
    {
      icon: <FiAlertTriangle />,
      title: 'Risk Analysis',
      description: 'Analyze current supply chain risks',
      query: 'Perform a comprehensive analysis of current supply chain risks'
    },
    {
      icon: <FiTrendingUp />,
      title: 'Predictive Analytics',
      description: 'View predictive insights',
      query: 'Show me the predictive analytics dashboard'
    },
    {
      icon: <FiTarget />,
      title: 'Crisis Simulation',
      description: 'Simulate a crisis scenario',
      query: 'Simulate a severe typhoon hitting Southeast Asia'
    }
  ];

  const handleSubmit = async (query: string) => {
    if (!query.trim() || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      content: query,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputQuery('');
    setIsLoading(true);

    const startTime = Date.now();

    try {
      const response = await axios.post<ApiResponse>(API_GATEWAY_URL, {
        query,
        conversation_id: conversationId
      }, { 
        headers: { 'Content-Type': 'application/json' },
        timeout: 60000 
      });

      const duration = Date.now() - startTime;

      // Capture ALL metadata from backend response
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date().toISOString(),
        // Backend metadata - THIS IS CRITICAL
        traceId: response.data.trace_id,
        toolsCalled: response.data.tools_called || [],
        autonomousActions: response.data.autonomous_actions || [],
        duration: response.data.duration_ms || duration,
        agentType: response.data.agent_type,
        agentId: response.data.agent_id
      };

      setMessages(prev => [...prev, assistantMessage]);

    } catch (error: any) {
      const errorMessage: Message = {
        role: 'assistant',
        content: `I apologize, but I encountered an error: ${error.response?.data?.error || error.message || 'Unable to connect to the service'}. Please try again.`,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const formatMessage = (content: string) => {
    const lines = content.split('\n');
    
    return lines.map((line, i) => {
      if (line.startsWith('###')) {
        return <h3 key={i} className="message-header">{line.replace(/^###\s*/, '')}</h3>;
      }
      if (line.startsWith('##')) {
        return <h2 key={i} className="message-header">{line.replace(/^##\s*/, '')}</h2>;
      }
      
      let formatted = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      
      if (line.trim().startsWith('•') || line.trim().startsWith('-')) {
        return <li key={i} dangerouslySetInnerHTML={{ __html: formatted.replace(/^[•-]\s*/, '') }} />;
      }
      
      if (line.trim()) {
        return <p key={i} dangerouslySetInnerHTML={{ __html: formatted }} />;
      }
      
      return <br key={i} />;
    });
  };

  const renderMetadata = (msg: Message) => {
    const hasMetadata = msg.toolsCalled?.length || msg.autonomousActions?.length || msg.duration || msg.traceId;
    
    if (!hasMetadata) return null;

    return (
      <div className="message-metadata-footer">
        {msg.toolsCalled && msg.toolsCalled.length > 0 && (
          <div className="metadata-item tool-used" title={msg.toolsCalled.map(t => t.tool_name).join(', ')}>
            <FiActivity className="metadata-icon" />
            <span>{msg.toolsCalled.length} Tool{msg.toolsCalled.length !== 1 ? 's' : ''} Used</span>
            <div className="metadata-tooltip">
              {msg.toolsCalled.map((tool, idx) => (
                <div key={idx} className="tooltip-item">• {tool.tool_name}</div>
              ))}
            </div>
          </div>
        )}
        
        {msg.autonomousActions && msg.autonomousActions.length > 0 && (
          <div className="metadata-item action-taken" title={msg.autonomousActions.map(a => a.action_type).join(', ')}>
            <FiZap className="metadata-icon" />
            <span>{msg.autonomousActions.length} Autonomous Action{msg.autonomousActions.length !== 1 ? 's' : ''}</span>
            <div className="metadata-tooltip">
              {msg.autonomousActions.map((action, idx) => (
                <div key={idx} className="tooltip-item">
                  • {action.action_type} ({action.status})
                </div>
              ))}
            </div>
          </div>
        )}
        
        {msg.duration && (
          <div className="metadata-item duration">
            <FiClock className="metadata-icon" />
            <span>{msg.duration}ms</span>
          </div>
        )}
        
        {msg.traceId && (
          <div className="metadata-item trace-id" title={`Trace ID: ${msg.traceId}`}>
            <span className="trace-icon">🔍</span>
            <span className="trace-text">{msg.traceId.substring(0, 8)}...</span>
          </div>
        )}
        
        {msg.agentType && (
          <div className="metadata-item agent-info">
            <span className="agent-badge">{msg.agentType}</span>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="logo-container">
            <FiZap className="logo-icon" />
            <div>
              <h1>Supply Chain AI</h1>
              <p className="subtitle">Powered by Claude on AWS Bedrock</p>
            </div>
          </div>
          <div className="status-badge">
            <span className="status-dot"></span>
            Online
          </div>
        </div>
      </header>

      {/* Main Chat Area */}
      <main className="main-container">
        <div className="chat-container">
          <div className="messages-area">
            {messages.map((msg, index) => (
              <div key={index} className={`message-wrapper ${msg.role}`}>
                <div className="message-bubble">
                  <div className="message-icon">
                    {msg.role === 'assistant' ? <FiZap /> : null}
                  </div>
                  <div className="message-content-wrapper">
                    <div className="message-text">
                      {formatMessage(msg.content)}
                    </div>
                    {msg.role === 'assistant' && renderMetadata(msg)}
                  </div>
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="message-wrapper assistant">
                <div className="message-bubble">
                  <div className="message-icon">
                    <FiZap />
                  </div>
                  <div className="message-content-wrapper">
                    <div className="message-text">
                      <div className="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                      <p className="loading-text">Analyzing supply chain data...</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Quick Prompts */}
          {messages.length === 1 && !isLoading && (
            <div className="quick-prompts">
              <h2 className="prompts-title">Quick Actions</h2>
              <div className="prompts-grid">
                {quickPrompts.map((prompt, index) => (
                  <button
                    key={index}
                    className="prompt-card"
                    onClick={() => handleSubmit(prompt.query)}
                  >
                    <div className="prompt-icon">{prompt.icon}</div>
                    <h3>{prompt.title}</h3>
                    <p>{prompt.description}</p>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input Area */}
          <div className="input-container">
            <form 
              className="input-form" 
              onSubmit={(e) => {
                e.preventDefault();
                handleSubmit(inputQuery);
              }}
            >
              <input
                ref={inputRef}
                type="text"
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                placeholder="Ask about supply chain risks, simulations, or predictions..."
                disabled={isLoading}
                className="input-field"
              />
              <button 
                type="submit" 
                disabled={isLoading || !inputQuery.trim()}
                className="send-button"
              >
                <FiSend />
              </button>
            </form>
            <p className="input-hint">
              Powered by Claude 3 Sonnet • Real-time supply chain intelligence
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;