import { useState } from 'react';
import { ThumbsUp, ThumbsDown, Send, CheckCircle2, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/utils';
import config from '@/config/env';

interface FeedbackProps {
    messageId: string;
}

const Feedback = ({ messageId }: FeedbackProps) => {
    const [status, setStatus] = useState<'none' | 'good' | 'bad'>('none');
    const [how, setHow] = useState('');
    const [loading, setLoading] = useState(false);
    const [submitted, setSubmitted] = useState(false);

    const handleSubmit = async () => {
        if (status === 'none') return;

        setLoading(true);
        try {
            const response = await fetch(`${config.apiUrl}/api/feedback`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message_id: messageId,
                    status: status,
                    how: how
                }),
            });

            if (response.ok) {
                setSubmitted(true);
            }
        } catch (error) {
            console.error('Error submitting feedback:', error);
        } finally {
            setLoading(false);
        }
    };

    if (submitted) {
        return (
            <div className="mt-4 flex items-center gap-2 text-xs text-green-600 bg-green-50/50 p-2 rounded-lg border border-green-100 animate-in fade-in zoom-in duration-300">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Thank you for your feedback!</span>
            </div>
        );
    }

    return (
        <div className="mt-4 pt-4 border-t border-slate-100">
            <p className="text-[10px] font-bold text-slate-400 mb-3 uppercase tracking-widest">
                Was this response helpful?
            </p>
            <div className="flex gap-2 mb-4">
                <Button
                    variant="outline"
                    size="sm"
                    className={cn(
                        "h-8 gap-2 px-3 border-slate-200 text-slate-600 transition-all duration-200 hover:border-green-200 hover:bg-green-50/50 hover:text-green-600",
                        status === 'good' && "bg-green-50/80 border-green-200 text-green-600 shadow-sm"
                    )}
                    onClick={() => setStatus('good')}
                >
                    <ThumbsUp className={cn("w-3 h-3", status === 'good' && "fill-current")} />
                    <span className="text-xs font-medium">Yes</span>
                </Button>
                <Button
                    variant="outline"
                    size="sm"
                    className={cn(
                        "h-8 gap-2 px-3 border-slate-200 text-slate-600 transition-all duration-200 hover:border-amber-200 hover:bg-amber-50/50 hover:text-amber-600",
                        status === 'bad' && "bg-amber-50/80 border-amber-200 text-amber-600 shadow-sm"
                    )}
                    onClick={() => setStatus('bad')}
                >
                    <ThumbsDown className={cn("w-3 h-3", status === 'bad' && "fill-current")} />
                    <span className="text-xs font-medium">No</span>
                </Button>
            </div>

            {status !== 'none' && (
                <div className="space-y-2 animate-in fade-in slide-in-from-top-1 duration-300">
                    <label className="text-[11px] font-semibold text-slate-500 ml-1">
                        {status === 'good' ? 'What did you like?' : 'How can we improve?'}
                    </label>
                    <div className="flex gap-2 items-start">
                        <Textarea
                            placeholder="Optional: Tell us more..."
                            className="text-xs min-h-[60px] py-2 resize-none border-slate-200 bg-slate-50/30 focus:bg-white focus:ring-1 focus:ring-purple-100 transition-all"
                            value={how}
                            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setHow(e.target.value)}
                        />
                        <Button
                            size="icon"
                            disabled={loading}
                            className="h-10 w-10 shrink-0 bg-purple-600 hover:bg-purple-700 text-white shadow-md transition-all active:scale-95"
                            onClick={handleSubmit}
                        >
                            {loading ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                                <Send className="w-4 h-4" />
                            )}
                        </Button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Feedback;
