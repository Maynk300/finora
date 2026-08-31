import { useState, useRef, useEffect } from 'react'
import { api } from '../services/api'

const sampleQuestions = [
  'How much did I spend on food this month?',
  'What is my savings rate?',
  'Show me my budget vs actual spending',
  'Give me tips to reduce expenses',
  'What are my top spending categories?',
  'Compare my finances this month vs last month',
  'How did I do this month compared to last month?',
]

export default function AIAssistant() {
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant'; content: string }>>([
    { role: 'assistant', content: 'Hello! I\'m your AI Financial Assistant. I can help you analyze your spending, budgets, and provide personalized financial insights. What would you like to know?' }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage = input.trim()
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setInput('')
    setIsLoading(true)

    try {
      const data = await api.post<{ response: string }>('/ai/chat/', { message: userMessage })
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }])
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: err instanceof Error ? err.message : 'Failed to get response from AI assistant' }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSuggestionClick = (question: string) => {
    setInput(question)
    textareaRef.current?.focus()
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e as unknown as React.FormEvent)
    }
  }

  return (
    <div className="space-y-6">
      <div className="page-header animate-slide-up">
        <h1>AI Assistant</h1>
        <p>Ask questions about your finances and get personalized insights</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 animate-slide-up" style={{ animationDelay: '100ms' }}>
          <div className="card-elevated flex flex-col h-[700px]">
            <div className="p-4 border-b border-border flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl gradient-primary flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
                <div>
                  <h2 className="font-semibold text-text-primary">Finance Assistant</h2>
                  <p className="text-xs text-text-secondary">Powered by Nemotron</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${!isLoading ? 'bg-success animate-pulse-glow-success' : 'bg-warning animate-pulse-glow-warning'}`} />
                <span className="text-xs text-text-secondary">{isLoading ? 'Thinking...' : 'Ready'}</span>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {messages.map((message, index) => (
                <div key={index} className={`flex gap-3 animate-slide-up ${message.role === 'user' ? 'justify-end' : ''}`} style={{ animationDelay: `${index * 50}ms` }}>
                  {message.role === 'assistant' && (
                    <div className="w-8 h-8 rounded-xl gradient-primary flex items-center justify-center flex-shrink-0">
                      <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                    </div>
                  )}
                  <div
                    className={`max-w-[85%] px-5 py-4 rounded-2xl ${
                      message.role === 'user'
                        ? 'gradient-primary text-white rounded-br-md shadow-lg'
                        : 'bg-surface border border-border rounded-bl-md prose prose-sm dark:prose-invert shadow-md'
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{message.content}</div>
                  </div>
                  {message.role === 'user' && (
                    <div className="w-8 h-8 rounded-xl bg-primary flex items-center justify-center flex-shrink-0">
                      <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                    </div>
                  )}
                </div>
              ))}
              {isLoading && (
                <div className="flex gap-3 justify-start animate-slide-up">
                  <div className="w-8 h-8 rounded-xl gradient-primary flex items-center justify-center flex-shrink-0">
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <div className="max-w-[85%] px-5 py-4 bg-surface border border-border rounded-2xl rounded-bl-md">
                    <div className="animate-typing flex gap-1">
                      <span className="w-2 h-2 rounded-full bg-text-muted"></span>
                      <span className="w-2 h-2 rounded-full bg-text-muted"></span>
                      <span className="w-2 h-2 rounded-full bg-text-muted"></span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="border-t border-border p-4">
              <form onSubmit={handleSubmit} className="flex gap-3">
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={isLoading ? 'AI is thinking...' : 'Ask me about your finances...'}
                  rows={1}
                  className="flex-1 px-4 py-3 bg-surface border border-border rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent resize-none max-h-32 transition-all"
                  disabled={isLoading}
                  aria-label="Ask a question"
                />
                <button
                  type="submit"
                  disabled={!input.trim() || isLoading}
                  className="btn-primary px-6 py-3 group"
                >
                  <span className="flex items-center gap-2">
                    {isLoading ? (
                      <>
                        <svg className="w-5 h-5 animate-rotate" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                        Thinking...
                      </>
                    ) : (
                      <>
                        <svg className="w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                        </svg>
                        Send
                      </>
                    )}
                  </span>
                </button>
              </form>
            </div>
          </div>
        </div>

        <div className="lg:col-span-1 space-y-6">
          <div className="card-elevated p-6 animate-slide-up" style={{ animationDelay: '100ms' }}>
            <h3 className="text-lg font-semibold text-text-primary mb-4 flex items-center gap-2">
              <svg className="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
              Suggested Questions
            </h3>
            <ul className="space-y-2" role="list">
              {sampleQuestions.map((question) => (
                <li key={question}>
                  <button
                    onClick={() => handleSuggestionClick(question)}
                    className="w-full text-left px-4 py-3 bg-surface/50 hover:bg-surface border border-border rounded-xl text-sm text-text-secondary transition-all hover:border-primary hover:text-text-primary"
                  >
                    {question}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          <div className="card-elevated p-6 animate-slide-up" style={{ animationDelay: '200ms' }}>
            <h3 className="text-lg font-semibold text-text-primary mb-4 flex items-center gap-2">
              <svg className="w-5 h-5 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Capabilities
            </h3>
            <ul className="space-y-3 text-sm text-text-secondary">
              <li className="flex items-center gap-3 p-3 bg-surface/50 rounded-xl hover:border-primary hover:border transition-all">
                <div className="w-8 h-8 rounded-lg gradient-success flex items-center justify-center flex-shrink-0">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <span>Spending analysis by category</span>
              </li>
              <li className="flex items-center gap-3 p-3 bg-surface/50 rounded-xl hover:border-primary hover:border transition-all">
                <div className="w-8 h-8 rounded-lg gradient-warning flex items-center justify-center flex-shrink-0">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <span>Budget vs actual tracking</span>
              </li>
              <li className="flex items-center gap-3 p-3 bg-surface/50 rounded-xl hover:border-primary hover:border transition-all">
                <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center flex-shrink-0">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                </div>
                <span>Savings rate calculation</span>
              </li>
              <li className="flex items-center gap-3 p-3 bg-surface/50 rounded-xl hover:border-primary hover:border transition-all">
                <div className="w-8 h-8 rounded-lg gradient-danger flex items-center justify-center flex-shrink-0">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
                <span>Personalized saving tips</span>
              </li>
              <li className="flex items-center gap-3 p-3 bg-surface/50 rounded-xl hover:border-primary hover:border transition-all">
                <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center flex-shrink-0">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <span>Financial insights & trends</span>
              </li>
              <li className="flex items-center gap-3 p-3 bg-surface/50 rounded-xl hover:border-primary hover:border transition-all">
                <div className="w-8 h-8 rounded-lg gradient-secondary flex items-center justify-center flex-shrink-0">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <span>Month-to-month comparisons</span>
              </li>
            </ul>
          </div>

          <div className="card-elevated p-6 animate-slide-up" style={{ animationDelay: '300ms' }}>
            <div className="p-4 bg-surface/50 rounded-xl border border-border">
              <p className="text-sm text-text-secondary">
                <strong className="text-text-primary">Tip:</strong> Try asking "How did I do this month compared to last month?" or "Which categories am I overspending on?"
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}