import React, { useState } from 'react';
import { Card, Button, Input } from '../components/ui';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Lock, Mail, ArrowRight, Sparkles } from 'lucide-react';

const LoginPage = () => {
    const [credentials, setCredentials] = useState({ username: '', password: '' });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            await login(credentials);
            navigate('/');
        } catch (err: any) {
            setError(err.response?.data?.non_field_errors?.[0] || 'Invalid credentials. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-[85vh] flex items-center justify-center px-4">
            <div className="w-full max-w-[480px]">
                {/* Branding */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center mb-10"
                >
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-primary to-brand-secondary shadow-2xl shadow-brand-primary/30 mb-6">
                        <Sparkles className="w-8 h-8 text-white" />
                    </div>
                    <h1 className="text-3xl font-bold mb-2">Welcome back</h1>
                    <p className="text-white/35">Sign in to continue your learning journey</p>
                </motion.div>

                <Card className="p-8 relative overflow-hidden">
                    {/* Decorative glow */}
                    <div className="absolute -top-24 -right-24 w-48 h-48 bg-brand-primary/8 rounded-full blur-3xl pointer-events-none" />
                    <div className="absolute -bottom-24 -left-24 w-48 h-48 bg-brand-secondary/6 rounded-full blur-3xl pointer-events-none" />

                    <form onSubmit={handleSubmit} className="space-y-5 relative z-10">
                        <Input
                            label="Username"
                            placeholder="Enter your username"
                            icon={<Mail className="w-4 h-4" />}
                            value={credentials.username}
                            onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
                            required
                        />
                        <Input
                            label="Password"
                            type="password"
                            placeholder="••••••••"
                            icon={<Lock className="w-4 h-4" />}
                            value={credentials.password}
                            onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
                            required
                        />

                        {error && (
                            <motion.div
                                initial={{ opacity: 0, y: -8 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="text-sm text-danger bg-danger/10 p-3.5 rounded-xl border border-danger/20 flex items-center gap-2"
                            >
                                <div className="w-1.5 h-1.5 rounded-full bg-danger flex-shrink-0" />
                                {error}
                            </motion.div>
                        )}

                        <Button type="submit" className="w-full h-12" size="lg" isLoading={loading}>
                            Sign In <ArrowRight className="w-4 h-4" />
                        </Button>
                    </form>

                    <div className="mt-8 pt-6 border-t border-white/[0.06] text-center">
                        <span className="text-white/30 text-sm">Don't have an account? </span>
                        <Link to="/register" className="text-brand-primary text-sm font-semibold hover:text-brand-secondary transition-colors">
                            Create one
                        </Link>
                    </div>
                </Card>
            </div>
        </div>
    );
};

export default LoginPage;
