import { useState } from 'react';
import { Sparkles, RefreshCw, CheckCircle2 } from 'lucide-react';
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
    const [identifier, setIdentifier] = useState(''); // Can be username or email
    const [username, setUsername] = useState('');     // Only for signup
    const [email, setEmail] = useState('');           // Only for signup
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [showSuccessModal, setShowSuccessModal] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (password.length > 72) {
            toast.error('Password must be less than 72 characters');
            return;
        }

        setLoading(true);

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout

        try {
            if (isLogin) {
                console.log('Attempting login with:', identifier);
                const formData = new URLSearchParams();
                formData.append('username', identifier);
                formData.append('password', password);

                const res = await fetch(`${API_URL}/api/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: formData,
                    signal: controller.signal
                });

                const data = await res.json();
                clearTimeout(timeoutId);
                console.log('Login response:', res.status, data);

                if (res.ok) {
                    onLogin(data.access_token, data.username || identifier);
                    toast.success('Logged in successfully');
                } else {
                    toast.error(data.detail || 'Login failed');
                }
            } else {
                console.log('Attempting registration for:', username, email);
                const res = await fetch(`${API_URL}/api/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, email, password }),
                    signal: controller.signal
                });

                const data = await res.json();
                clearTimeout(timeoutId);
                console.log('Registration response:', res.status, data);
                if (res.ok) {
                    setShowSuccessModal(true);
                    setUsername('');
                    setEmail('');
                    setPassword('');
                    // User stays on signup page to manually go to login
                } else {
                    toast.error(data.detail || 'Account already exists');
                }
            }
        } catch (err) {
            if (err instanceof Error && err.name === 'AbortError') {
                toast.error('Connection timeout. The server is taking too long to respond.');
            } else {
                toast.error('Server error. Is the backend running?');
            }
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
                        {isLogin ? (
                            <div className="space-y-2">
                                <Label className="text-slate-300">Username or Email</Label>
                                <Input
                                    placeholder="johndoe or john@example.com"
                                    value={identifier}
                                    onChange={(e) => setIdentifier(e.target.value)}
                                    autoComplete="off"
                                    className="bg-white/5 border-white/10 text-white placeholder:text-slate-600 focus:ring-purple-500"
                                    required
                                />
                            </div>
                        ) : (
                            <>
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
                                    <Label className="text-slate-300">Email ID</Label>
                                    <Input
                                        type="email"
                                        placeholder="john@example.com"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        autoComplete="off"
                                        className="bg-white/5 border-white/10 text-white placeholder:text-slate-600 focus:ring-purple-500"
                                        required
                                    />
                                </div>
                            </>
                        )}
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

            {/* Success Modal */}
            {showSuccessModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-sm animate-in fade-in duration-300">
                    <div className="w-full max-w-sm bg-white rounded-3xl p-8 text-center shadow-2xl transform animate-in zoom-in-95 duration-300">
                        <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                            <CheckCircle2 className="w-10 h-10 text-green-500" />
                        </div>
                        <h3 className="text-2xl font-bold text-slate-800 mb-2">Success!</h3>
                        <p className="text-slate-500 mb-8">
                            Account has been created
                        </p>
                        <Button
                            className="w-full bg-slate-900 hover:bg-slate-800 text-white rounded-xl h-12"
                            onClick={() => {
                                setShowSuccessModal(false);
                                setIsLogin(true);
                            }}
                        >
                            Got it, thanks!
                        </Button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Login;
