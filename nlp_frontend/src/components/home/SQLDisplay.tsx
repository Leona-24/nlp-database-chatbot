import { useState } from 'react';
import { Code } from 'lucide-react';
import { toast } from 'sonner';

interface SQLDisplayProps {
    sql: string;
}

const SQLDisplay = ({ sql }: SQLDisplayProps) => {
    const [copied, setCopied] = useState(false);

    const copyToClipboard = () => {
        navigator.clipboard.writeText(sql);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
        toast.success('SQL copied to clipboard');
    };

    return (
        <div className="bg-slate-900 rounded-lg p-4 mt-3 relative group">
            <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-slate-400 flex items-center gap-2">
                    <Code className="w-3 h-3" />
                    Generated SQL
                </span>
                <button
                    onClick={copyToClipboard}
                    className="text-xs text-slate-400 hover:text-white transition-colors"
                >
                    {copied ? 'Copied!' : 'Copy'}
                </button>
            </div>
            <pre className="text-sm text-green-400 font-mono overflow-x-auto">
                <code>{sql}</code>
            </pre>
        </div>
    );
};

export default SQLDisplay;
