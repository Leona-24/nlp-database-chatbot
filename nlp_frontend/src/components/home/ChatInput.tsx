import { Send, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

interface ChatInputProps {
    input: string;
    setInput: (input: string) => void;
    sendMessage: () => void;
    connected: boolean;
    loading: boolean;
}

const ChatInput = ({ input, setInput, sendMessage, connected, loading }: ChatInputProps) => {
    return (
        <div className="bg-white border-t p-4">
            <div className="max-w-4xl mx-auto flex gap-3">
                <div className="flex-1 relative">
                    <Input
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                        placeholder={connected ? "Ask a question about your data..." : "Connect database to start..."}
                        disabled={!connected || loading}
                        className="pr-12 py-6 text-base"
                    />
                    {loading && (
                        <div className="absolute right-3 top-1/2 -translate-y-1/2">
                            <RefreshCw className="w-5 h-5 text-slate-400 animate-spin" />
                        </div>
                    )}
                </div>
                <Button
                    onClick={sendMessage}
                    disabled={!connected || loading || !input.trim()}
                    className="px-6"
                >
                    <Send className="w-5 h-5" />
                </Button>
            </div>
            <p className="text-xs text-center text-slate-400 mt-2">
                Powered by NLP • Converts natural language to SQL automatically
            </p>
        </div>
    );
};

export default ChatInput;
