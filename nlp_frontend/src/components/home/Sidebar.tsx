import { Sparkles, Shield } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogTrigger } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import SchemaViewer from './SchemaViewer';
import DatabaseConnectionDialog from './DatabaseConnectionDialog';
import type { DatabaseConfig } from '../../types';

import config from '../../config/env';

interface SidebarProps {
    connected: boolean;
    dbConfig: DatabaseConfig;
    setDbConfig: (config: DatabaseConfig) => void;
    setConnected: (connected: boolean) => void;
    schema: any[];
    setSchema: (schema: any[]) => void;
}

const Sidebar = ({
    connected,
    dbConfig,
    setDbConfig,
    setConnected,
    schema,
    setSchema
}: SidebarProps) => {
    return (
        <div className="w-80 bg-white border-r flex flex-col">
            <div className="p-4 border-b">
                <div className="flex items-center gap-2 mb-4">
                    <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-blue-500 rounded-xl flex items-center justify-center">
                        <Sparkles className="w-5 h-5 text-white" />
                    </div>
                    <div>
                        <h1 className="font-bold text-slate-800">{config.appName}</h1>
                        <p className="text-xs text-slate-500">Chatbot Interface</p>
                    </div>
                </div>

                <Dialog>
                    <DialogTrigger asChild>
                        <Button
                            className={`w-full justify-start gap-2 h-10 px-4 py-2 rounded-md ${connected ? "bg-slate-900 text-white" : "bg-white border text-slate-900"}`}
                        >
                            {connected ? (
                                <>
                                    <div className="w-4 h-4 mr-2 border border-slate-400 rounded-sm" />
                                    Test Connection
                                </>
                            ) : 'Connect Database'}
                            {connected && <Badge variant="secondary" className="ml-auto bg-green-100 text-green-700 hover:bg-green-100">Connected</Badge>}
                        </Button>
                    </DialogTrigger>
                    <DatabaseConnectionDialog
                        config={dbConfig}
                        setConfig={setDbConfig}
                        connected={connected}
                        setConnected={setConnected}
                        setSchema={setSchema}
                    />
                </Dialog>
            </div>

            <ScrollArea className="flex-1 p-4">
                <SchemaViewer schema={schema} />
            </ScrollArea>

            <div className="p-4 border-t">
                <div className="flex items-center gap-2 text-xs text-slate-500">
                    <Shield className="w-4 h-4" />
                    <span>Secure Connection</span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                    All queries are validated for SQL injection
                </p>
            </div>
        </div>
    );
};

export default Sidebar;
