export interface Message {
    id: string;
    type: 'user' | 'bot';
    content: string;
    sql?: string;
    results?: QueryResult;
    processingSteps?: ProcessingStep[];
    thought?: string;
    confidence?: number;
    timestamp: Date;
}

export interface QueryResult {
    columns: string[];
    rows: any[];
    executionTime: number;
    rowCount: number;
}

export interface ProcessingStep {
    name: string;
    status: 'pending' | 'processing' | 'completed' | 'error';
    details?: string;
}

export interface DatabaseConfig {
    type: string;
    host: string;
    port: string;
    database: string;
    username: string;
    password: string;
}
