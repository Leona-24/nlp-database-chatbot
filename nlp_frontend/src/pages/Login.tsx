import { useState } from 'react';
import { Sparkles, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';

import config from '../config/env';

// API Config
const API_URL = config.apiUrl;

interface LoginProps {
    onLogin: (token: string, username: string) => void;
}

const Login = ({ onLogin }: LoginProps) => {
    const [isLogin, setIsLogin] = useState(true);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (password.length > 72) {
            toast.error('Password must be less than 72 characters');
            return;
        }

        setLoading(true);

        try {
            if (isLogin) {
                const formData = new URLSearchParams();
                formData.append('username', username);
                formData.append('password', password);

                const res = await fetch(`${API_URL}/api/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: formData
                });

                const data = await res.json();
                if (res.ok) {
                    onLogin(data.access_token, username);
                    toast.success('Logged in successfully');
                } else {
                    toast.error(data.detail || 'Login failed');
                }
            } else {
                const res = await fetch(`${API_URL}/api/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });

                const data = await res.json();

                if (res.ok) {
                    toast.success('Account has been created');
                    setUsername('');
                    setPassword('');
                    setIsLogin(true);
                } else {
                    toast.error(data.detail || 'Registration failed');
                }
            }
        } catch (err) {
            toast.error('Server error. Is the backend running?');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] bg-purple-500/10 blur-[120px] rounded-full" />
                <div className="absolute -bottom-[20%] -right-[10%] w-[50%] h-[50%] bg-blue-500/10 blur-[120px] rounded-full" />
            </div>

            <Card className="w-full max-w-md bg-white/5 border-white/10 backdrop-blur-xl shadow-2xl">
                <CardHeader className="text-center pb-2">
                    <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-blue-500 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-purple-500/20">
                        <Sparkles className="w-8 h-8 text-white" />
                    </div>
                    <CardTitle className="text-2xl font-bold text-white">
                        {isLogin ? 'Welcome Back' : 'Create Account'}
                    </CardTitle>
                    <p className="text-slate-400 text-sm mt-1">
                        {isLogin ? 'Log in to access your NLP Database' : 'Get started with your NLP Database account'}
                    </p>
                </CardHeader>
                <CardContent className="pt-6">
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="space-y-2">
                            <Label className="text-slate-300">Username</Label>
                            <Input
                                placeholder="johndoe"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                autoComplete="off"
                                className="bg-white/5 border-white/10 text-white placeholder:text-slate-600 focus:ring-purple-500"
                                required
                            />
                        </div>
                        <div className="space-y-2">
                            <Label className="text-slate-300">Password</Label>
                            <Input
                                type="password"
                                placeholder="••••••••"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                maxLength={72}
                                autoComplete="new-password"
                                className="bg-white/5 border-white/10 text-white placeholder:text-slate-600 focus:ring-purple-500"
                                required
                            />
                        </div>
                        <Button
                            type="submit"
                            className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white border-0 shadow-lg shadow-purple-500/20 h-11"
                            disabled={loading}
                        >
                            {loading ? (
                                <>
                                    <RefreshCw className="w-5 h-5 animate-spin mr-2" />
                                    Processing...
                                </>
                            ) : (isLogin ? 'Log In' : 'Sign Up')}
                        </Button>
                    </form>

                    <div className="mt-6 text-center">
                        <button
                            type="button"
                            onClick={() => setIsLogin(!isLogin)}
                            className="text-sm text-slate-400 hover:text-purple-400 transition-colors"
                        >
                            {isLogin ? "Don't have an account? Sign Up" : "Already have an account? Log In"}
                        </button>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
};

export default Login;
