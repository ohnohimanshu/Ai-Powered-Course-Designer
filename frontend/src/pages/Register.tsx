import React, { useState } from 'react';
import { Card, Button, Input } from '../components/ui';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { UserPlus, ArrowRight, User, Mail, Lock, Sparkles } from 'lucide-react';

const RegisterPage = () => {
    const [formData, setFormData] = useState({ username: '', password: '', email: '' });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const { register } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            await register(formData);
            navigate('/login');
        } catch (err: any) {
            const errorData = err.response?.data;
            if (typeof errorData === 'object') {
                const messages = Object.values(errorData).flat().join('. ');
                setError(messages || 'Registration failed');
            } else {
                setError('Registration failed. Please try again.');
            }
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
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-secondary to-brand-accent shadow-2xl shadow-brand-secondary/30 mb-6">
                        <UserPlus className="w-8 h-8 text-white" />
                    </div>
                    <h1 className="text-3xl font-bold mb-2">Create your account</h1>
                    <p className="text-white/35">Start building AI-powered courses in minutes</p>
                </motion.div>

                <Card className="p-8 relative overflow-hidden">
                    <div className="absolute -top-24 -left-24 w-48 h-48 bg-brand-secondary/8 rounded-full blur-3xl pointer-events-none" />
                    <div className="absolute -bottom-24 -right-24 w-48 h-48 bg-brand-accent/6 rounded-full blur-3xl pointer-events-none" />

                    <form onSubmit={handleSubmit} className="space-y-5 relative z-10">
                        <Input
                            label="Username"
                            placeholder="Choose a username"
                            icon={<User className="w-4 h-4" />}
                            value={formData.username}
                            onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                            required
                        />
                        <Input
                            label="Email"
                            type="email"
                            placeholder="name@example.com"
                            icon={<Mail className="w-4 h-4" />}
                            value={formData.email}
                            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                            required
                        />
                        <Input
                            label="Password"
                            type="password"
                            placeholder="••••••••"
                            icon={<Lock className="w-4 h-4" />}
                            value={formData.password}
                            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
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
                            Create Account <ArrowRight className="w-4 h-4" />
                        </Button>
                    </form>

                    <div className="mt-8 pt-6 border-t border-white/[0.06] text-center">
                        <span className="text-white/30 text-sm">Already have an account? </span>
                        <Link to="/login" className="text-brand-primary text-sm font-semibold hover:text-brand-secondary transition-colors">
                            Sign in
                        </Link>
                    </div>
                </Card>
            </div>
        </div>
    );
};

export default RegisterPage;
