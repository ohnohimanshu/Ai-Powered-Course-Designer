import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LogOut, Sparkles, Plus, LayoutDashboard } from 'lucide-react';
import { motion } from 'framer-motion';

export const Navbar = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    const isActive = (path: string) => location.pathname === path;

    return (
        <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/[0.06] bg-surface-0/70 backdrop-blur-2xl">
            <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                {/* Logo */}
                <Link to="/" className="flex items-center gap-3 group">
                    <motion.div
                        whileHover={{ rotate: 15, scale: 1.1 }}
                        className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-primary to-brand-secondary flex items-center justify-center shadow-lg shadow-brand-primary/20"
                    >
                        <Sparkles className="w-5 h-5 text-white" />
                    </motion.div>
                    <span className="text-lg font-bold tracking-tight">
                        <span className="text-white">Course</span>
                        <span className="text-gradient">Gen AI</span>
                    </span>
                </Link>

                {/* Navigation */}
                <div className="flex items-center gap-2">
                    {user ? (
                        <>
                            <Link
                                to="/"
                                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${isActive('/')
                                        ? 'bg-brand-primary/10 text-brand-primary'
                                        : 'text-white/50 hover:text-white hover:bg-white/5'
                                    }`}
                            >
                                <LayoutDashboard className="w-4 h-4" />
                                Dashboard
                            </Link>
                            <Link
                                to="/generate"
                                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${isActive('/generate')
                                        ? 'bg-brand-primary/10 text-brand-primary'
                                        : 'text-white/50 hover:text-white hover:bg-white/5'
                                    }`}
                            >
                                <Plus className="w-4 h-4" />
                                New Course
                            </Link>

                            <div className="h-6 w-px bg-white/[0.06] mx-2" />

                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand-primary/30 to-brand-secondary/30 border border-white/10 flex items-center justify-center">
                                    <span className="text-xs font-bold text-white/80">
                                        {user.username?.charAt(0).toUpperCase()}
                                    </span>
                                </div>
                                <span className="text-sm text-white/40 hidden sm:block">{user.username}</span>
                                <button
                                    onClick={() => { logout(); navigate('/login'); }}
                                    className="p-2 rounded-lg hover:bg-red-500/10 text-white/30 hover:text-red-400 transition-all duration-200"
                                    title="Sign out"
                                >
                                    <LogOut className="w-4 h-4" />
                                </button>
                            </div>
                        </>
                    ) : (
                        <div className="flex items-center gap-3">
                            <Link
                                to="/login"
                                className="text-sm font-medium text-white/50 hover:text-white transition-colors px-4 py-2"
                            >
                                Sign In
                            </Link>
                            <Link
                                to="/register"
                                className="btn-primary px-5 py-2 text-sm"
                            >
                                Get Started
                            </Link>
                        </div>
                    )}
                </div>
            </div>
        </nav>
    );
};

export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    return (
        <div className="min-h-screen relative overflow-x-hidden">
            <div className="animated-bg" />
            <div className="glow-mesh" />
            <Navbar />
            <main className="max-w-7xl mx-auto px-6 pt-24 pb-16 relative z-10">
                <motion.div
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -12 }}
                    transition={{ duration: 0.3, ease: "easeOut" }}
                >
                    {children}
                </motion.div>
            </main>
        </div>
    );
};
