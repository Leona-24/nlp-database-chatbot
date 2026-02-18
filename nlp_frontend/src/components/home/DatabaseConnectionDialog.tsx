import { useState } from 'react';
import { CheckCircle, RefreshCw } from 'lucide-react';
import { DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';
import type { DatabaseConfig } from '../../types';

import config from '../../config/env';

const API_URL = config.apiUrl;

interface DatabaseConnectionDialogProps {
    config: DatabaseConfig;
    setConfig: (c: DatabaseConfig) => void;
    connected: boolean;
    setConnected: (v: boolean) => void;
    setSchema: (s: any[]) => void;
}

const DatabaseConnectionDialog = ({
    config,
    setConfig,
    connected,
    setConnected,
    setSchema
}: DatabaseConnectionDialogProps) => {
    const [testing, setTesting] = useState(false);
    const [createReadOnly, setCreateReadOnly] = useState(true);

    const testConnection = async () => {
        setTesting(true);
        try {
            const res = await fetch(`${API_URL}/api/connect`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });

            const data = await res.json();

            if (res.ok) {
                toast.success('Connection Successful', {
                    description: `Backend is reachable. DB Type: ${data.details.type}`
                });
            } else {
                toast.error('Connection Failed', { description: data.detail || 'Unknown error' });
            }
        } catch (e) {
            toast.error('Connection failed. Is the backend running?');
        } finally {
            setTesting(false);
        }
    };

    const connectDatabase = async () => {
        try {
            const res = await fetch(`${API_URL}/api/connect`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });

            const data = await res.json();

            if (res.ok) {
                setConnected(true);
                setSchema(data.schema || []);

                const safeConfig = { ...config, password: '' };
                localStorage.setItem('dbConfig', JSON.stringify(safeConfig));

                toast.success('Database Connected', {
                    description: `Successfully connected to ${config.database}`
                });
            } else {
                toast.error('Connection Failed', { description: data.detail || 'check your credentials' });
            }
        } catch (e) {
            toast.error('Failed to connect');
        }
    };

    const disconnect = () => {
        setConnected(false);
        localStorage.removeItem('dbConfig');
        toast.info('Database disconnected');
    };

    return (
        <DialogContent className="max-w-md">
            <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                    Connect Your Database
                </DialogTitle>
            </DialogHeader>

            <Separator className="my-2" />

            <div className="space-y-4 py-2">
                {connected ? (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center space-y-4">
                        <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto">
                            <CheckCircle className="w-6 h-6 text-green-600" />
                        </div>
                        <div>
                            <h3 className="font-medium text-green-900">Successfully Connected</h3>
                            <p className="text-sm text-green-700 mt-1">
                                {config.type === 'postgresql' ? 'PostgreSQL' : config.type} • {config.host}
                            </p>
                        </div>
                        <Button
                            variant="outline"
                            className="w-full border-green-200 text-green-700 hover:bg-green-100 hover:text-green-800"
                            onClick={disconnect}
                        >
                            Disconnect
                        </Button>
                    </div>
                ) : (
                    <div className="space-y-4">
                        <div className="space-y-2">
                            <Label className="text-xs uppercase text-slate-500 font-semibold tracking-wider">Database Type</Label>
                            <Select
                                value={config.type}
                                onValueChange={(v) => setConfig({ ...config, type: v })}
                            >
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="postgresql">PostgreSQL</SelectItem>
                                    <SelectItem value="mysql">MySQL</SelectItem>
                                    <SelectItem value="sqlite">SQLite</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="space-y-3">
                            <div className="grid grid-cols-4 items-center gap-4">
                                <Label htmlFor="host" className="text-right text-sm">Host</Label>
                                <Input
                                    id="host"
                                    value={config.host}
                                    onChange={(e) => setConfig({ ...config, host: e.target.value })}
                                    className="col-span-3 h-8"
                                    placeholder="db.company.com"
                                />
                            </div>
                            <div className="grid grid-cols-4 items-center gap-4">
                                <Label htmlFor="port" className="text-right text-sm">Port</Label>
                                <Input
                                    id="port"
                                    value={config.port}
                                    onChange={(e) => setConfig({ ...config, port: e.target.value })}
                                    className="col-span-3 h-8"
                                    placeholder="5432"
                                />
                            </div>
                            <div className="grid grid-cols-4 items-center gap-4">
                                <Label htmlFor="dbname" className="text-right text-sm">Database</Label>
                                <Input
                                    id="dbname"
                                    value={config.database}
                                    onChange={(e) => setConfig({ ...config, database: e.target.value })}
                                    className="col-span-3 h-8"
                                    placeholder="sales_data"
                                />
                            </div>
                            <div className="grid grid-cols-4 items-center gap-4">
                                <Label htmlFor="username" className="text-right text-sm">Username</Label>
                                <Input
                                    id="username"
                                    value={config.username}
                                    onChange={(e) => setConfig({ ...config, username: e.target.value })}
                                    autoComplete="off"
                                    className="col-span-3 h-8"
                                    placeholder="read_only_user"
                                />
                            </div>
                            <div className="grid grid-cols-4 items-center gap-4">
                                <Label htmlFor="password" className="text-right text-sm">Password</Label>
                                <Input
                                    id="password"
                                    type="password"
                                    value={config.password}
                                    onChange={(e) => setConfig({ ...config, password: e.target.value })}
                                    autoComplete="new-password"
                                    className="col-span-3 h-8"
                                    placeholder="********"
                                />
                            </div>
                        </div>

                        <div className="pt-2 flex justify-between items-center">
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={testConnection}
                                disabled={testing || !config.host}
                                className="text-slate-500 hover:text-slate-900 px-0 h-auto font-normal flex items-center gap-2"
                            >
                                {testing ? (
                                    <RefreshCw className="w-3 h-3 animate-spin" />
                                ) : (
                                    <div className="w-4 h-4 border border-slate-400 rounded-sm" />
                                )}
                                Test Connection
                            </Button>

                            <Button
                                variant="link"
                                size="sm"
                                className="text-xs text-purple-600 h-auto p-0"
                                onClick={() => setConfig({
                                    type: 'sqlite',
                                    host: 'localhost',
                                    port: '',
                                    database: 'data/app.db',
                                    username: '',
                                    password: ''
                                })}
                            >
                                Load Demo Data
                            </Button>
                        </div>

                        <div className="pt-4 space-y-4">
                            <div className="flex items-center space-x-2">
                                <Checkbox
                                    id="readonly"
                                    checked={createReadOnly}
                                    onCheckedChange={(c) => setCreateReadOnly(!!c)}
                                />
                                <Label htmlFor="readonly" className="text-sm font-normal">Create read-only user for me</Label>
                            </div>

                            <Button
                                className="w-full bg-slate-900 hover:bg-slate-800 text-white"
                                onClick={connectDatabase}
                                disabled={!config.type || (!config.host && config.type !== 'sqlite')}
                            >
                                Connect
                            </Button>
                        </div>
                    </div>
                )}
            </div>
        </DialogContent>
    );
};

export default DatabaseConnectionDialog;
