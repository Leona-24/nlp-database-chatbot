import { useState } from 'react';
import { Sparkles, ChevronUp, ChevronDown, CheckCircle, RefreshCw } from 'lucide-react';
import type { ProcessingStep } from '../../types';

interface ProcessingStepsProps {
    steps: ProcessingStep[];
}

const ProcessingSteps = ({ steps }: ProcessingStepsProps) => {
    const [expanded, setExpanded] = useState(false);

    return (
        <div className="bg-slate-50 rounded-lg p-3 mt-2">
            <button
                onClick={() => setExpanded(!expanded)}
                className="flex items-center justify-between w-full text-sm font-medium text-slate-700"
            >
                <span className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-purple-500" />
                    NLP Processing Pipeline
                </span>
                {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>

            {expanded && (
                <div className="mt-3 space-y-2">
                    {steps.map((step, idx) => (
                        <div key={idx} className="flex items-center gap-3 text-sm">
                            {step.status === 'completed' ? (
                                <CheckCircle className="w-4 h-4 text-green-500" />
                            ) : step.status === 'processing' ? (
                                <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />
                            ) : (
                                <div className="w-4 h-4 rounded-full border-2 border-slate-300" />
                            )}
                            <span className={step.status === 'completed' ? 'text-slate-700' : 'text-slate-400'}>
                                {step.name}
                            </span>
                            {step.details && step.status !== 'pending' && (
                                <span className="text-xs text-slate-500">{step.details}</span>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default ProcessingSteps;
