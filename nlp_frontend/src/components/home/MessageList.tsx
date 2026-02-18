import { MessageSquare, AlertTriangle, Sparkles } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import ProcessingSteps from './ProcessingSteps';
import SQLDisplay from './SQLDisplay';
import ResultsTable from './ResultsTable';
import type { Message } from '../../types';

import config from '../../config/env';

interface MessageListProps {
    messages: Message[];
    connected: boolean;
    suggestions: string[];
    onSuggestionClick: (suggestion: string) => void;
    messagesEndRef: React.RefObject<HTMLDivElement | null>;
}

const MessageList = ({
    messages,
    connected,
    suggestions,
    onSuggestionClick,
    messagesEndRef
}: MessageListProps) => {
    return (
        <ScrollArea className="flex-1 p-6">
            {messages.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto">
                    <div className="w-20 h-20 bg-gradient-to-br from-purple-100 to-blue-100 rounded-2xl flex items-center justify-center mb-6">
                        <MessageSquare className="w-10 h-10 text-purple-600" />
                    </div>
                    <h3 className="text-xl font-semibold text-slate-800 mb-2">
                        Welcome to {config.appName}
                    </h3>
                    <p className="text-slate-500 mb-6">
                        Connect your database and start asking questions in plain English.
                        No SQL knowledge required!
                    </p>

                    {!connected && (
                        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
                            <div className="flex items-center gap-2 text-amber-700">
                                <AlertTriangle className="w-5 h-5" />
                                <span className="font-medium">Database Not Connected</span>
                            </div>
                            <p className="text-sm text-amber-600 mt-1">
                                Please connect a database to start querying
                            </p>
                        </div>
                    )}

                    <div className="w-full">
                        <p className="text-sm text-slate-500 mb-3">Try asking:</p>
                        <div className="flex flex-wrap gap-2 justify-center">
                            {suggestions.map((suggestion, idx) => (
                                <button
                                    key={idx}
                                    onClick={() => onSuggestionClick(suggestion)}
                                    className="px-3 py-1.5 bg-white border rounded-full text-sm text-slate-600 hover:border-purple-400 hover:text-purple-600 transition-colors"
                                    disabled={!connected}
                                >
                                    {suggestion}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            ) : (
                <div className="space-y-6 max-w-4xl mx-auto">
                    {messages.map((message) => (
                        <div
                            key={message.id}
                            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            <div className={`max-w-3xl ${message.type === 'user' ? 'bg-purple-600 text-white' : 'bg-white border'} rounded-2xl px-5 py-4 shadow-sm`}>
                                {message.type === 'bot' && (
                                    <div className="flex items-center gap-2 mb-2">
                                        <div className="w-6 h-6 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full flex items-center justify-center">
                                            <Sparkles className="w-3 h-3 text-white" />
                                        </div>
                                        <span className="text-sm font-medium text-slate-700">NLP Bot</span>
                                        {message.confidence !== undefined && (
                                            <Badge
                                                variant="secondary"
                                                className={`text-[10px] h-4 px-1 ${message.confidence > 0.8 ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}`}
                                            >
                                                {Math.round(message.confidence * 100)}% Match
                                            </Badge>
                                        )}
                                    </div>
                                )}

                                <p className={message.type === 'user' ? 'text-white' : 'text-slate-700'}>
                                    {message.content}
                                </p>

                                {message.processingSteps && (
                                    <ProcessingSteps steps={message.processingSteps} />
                                )}

                                {message.sql && (
                                    <SQLDisplay sql={message.sql} />
                                )}

                                {message.results && (
                                    <ResultsTable result={message.results} />
                                )}
                            </div>
                        </div>
                    ))}
                    <div ref={messagesEndRef} />
                </div>
            )}
        </ScrollArea>
    );
};

export default MessageList;
