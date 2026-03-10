import { useState, useEffect, useRef } from 'react';
import { toast } from 'sonner';
import type { Message, ProcessingStep, DatabaseConfig } from '../types';

import config from '../config/env';

const API_URL = config.apiUrl;

export const useChat = (onLogout: () => void) => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [connected, setConnected] = useState(false);
    const [schema, setSchema] = useState<any[]>([]);
    const [dbConfig, setDbConfig] = useState<DatabaseConfig>({
        type: 'postgresql',
        host: '',
        port: '',
        database: '',
        username: '',
        password: ''
    });
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
        const savedConfig = localStorage.getItem('dbConfig');
        if (savedConfig) {
            try {
                const parsed = JSON.parse(savedConfig);
                setDbConfig({ ...parsed, password: '' });
            } catch (e) {
                console.error("Failed to parse saved config");
            }
        }
    }, []);

    const sendMessage = async () => {
        if (!input.trim() || !connected) {
            if (!connected) {
                toast.error('Please connect to a database first');
            }
            return;
        }

        const userMessage: Message = {
            id: Date.now().toString(),
            type: 'user',
            content: input,
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setLoading(true);

        try {
            const response = await fetch(`${API_URL}/api/query`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: userMessage.content,
                    history: messages.slice(-5).map(m => ({
                        type: m.type,
                        content: m.content,
                        sql: m.sql
                    }))
                })
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Failed to fetch');
            }

            const data = await response.json();

            let columns: string[] = [];
            let rows: any[] = [];

            if (data.results && data.results.length > 0) {
                columns = Object.keys(data.results[0]);
                rows = data.results.map((r: any) => columns.map(c => r[c]));
            }

            const steps: ProcessingStep[] = (data.thought || "").split('. ').filter(Boolean).map((s: string) => ({
                name: s.length > 30 ? s.substring(0, 30) + '...' : s,
                status: 'completed',
                details: s
            }));

            // Never show LLM "thought" explanations as bot content
            let botContent = data.message || `Found ${rows.length} results.`;

            // Generate a better natural language answer for single value results
            if (rows.length === 1 && columns.length === 1) {
                let val = rows[0][0];
                const colLower = columns[0].toLowerCase();
                if (typeof val === 'number') {
                    if (colLower.includes('oee') || colLower.includes('%') || colLower.includes('rate') || colLower.includes('percentage') || colLower.includes('availability') || colLower.includes('quality')) {
                        val = `${val.toFixed(2)}%`;
                    } else if (!Number.isInteger(val)) {
                        val = val.toFixed(2);
                    }
                }
                botContent = `**${columns[0].replace(/_/g, ' ')}** is **${val}**.`;
            } else if (rows.length === 1 && columns.length > 1) {
                // Single row, multiple columns - show as key-value pairs
                const parts = columns.map((col, i) => {
                    let val = rows[0][i];
                    const colLower = col.toLowerCase();
                    if (typeof val === 'number' && !Number.isInteger(val)) {
                        if (colLower.includes('oee') || colLower.includes('%') || colLower.includes('rate') || colLower.includes('percentage') || colLower.includes('availability') || colLower.includes('quality')) {
                            val = `${val.toFixed(2)}%`;
                        } else {
                            val = val.toFixed(2);
                        }
                    }
                    return `**${col.replace(/_/g, ' ')}**: ${val}`;
                });
                botContent = parts.join(' | ');
            } else if (rows.length === 0) {
                botContent = data.message || 'No results found for this query.';
            } else {
                botContent = `Found **${rows.length}** results.`;
            }

            const botMessage: Message = {
                id: (Date.now() + 1).toString(),
                type: 'bot',
                content: botContent,
                sql: data.sql_query,
                results: {
                    columns,
                    rows,
                    executionTime: data.execution_time || 0.1,
                    rowCount: rows.length
                },
                chartImage: data.chart_image || undefined,
                chartSpec: data.chart_spec || undefined,
                thought: data.thought,
                confidence: data.confidence,
                processingSteps: steps.length > 0 ? steps : [
                    { name: 'Intent Recognition', status: 'completed', details: 'Processed by Backend' },
                    { name: 'SQL Generation', status: 'completed' },
                    { name: 'Query Execution', status: 'completed' }
                ],
                timestamp: new Date()
            };

            setMessages(prev => [...prev, botMessage]);

        } catch (error) {
            if (error instanceof Error && error.message.includes('token')) {
                onLogout();
            }
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                type: 'bot',
                content: `Error: ${error}`,
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setLoading(false);
        }
    };

    const clearMessages = () => {
        setMessages([]);
        toast.success('Chat history cleared');
    };

    return {
        messages,
        input,
        setInput,
        loading,
        connected,
        setConnected,
        schema,
        setSchema,
        dbConfig,
        setDbConfig,
        messagesEndRef,
        sendMessage,
        clearMessages
    };
};
