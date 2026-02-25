import React, { useState } from 'react';
import { Card, Button, Input, Badge } from '../components/ui';
import { courseService } from '../services/api';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, Brain, Target, Layers, ArrowRight, ArrowLeft, CheckCircle2, Rocket, BookOpen, Zap } from 'lucide-react';

const levels = [
    { value: 'beginner', label: 'Beginner', desc: 'Starting from scratch', icon: <BookOpen className="w-5 h-5" /> },
    { value: 'intermediate', label: 'Intermediate', desc: 'Some prior knowledge', icon: <Zap className="w-5 h-5" /> },
    { value: 'advanced', label: 'Advanced', desc: 'Deep dive expertise', icon: <Rocket className="w-5 h-5" /> },
];

const GenerateCourse = () => {
    const [step, setStep] = useState(1);
    const [formData, setFormData] = useState({
        topic: '',
        level: 'beginner',
        goal: ''
    });
    const [isGenerating, setIsGenerating] = useState(false);
    const navigate = useNavigate();

    const handleGenerate = async () => {
        setIsGenerating(true);
        try {
            const course = await courseService.generateCourse(formData);
            setTimeout(() => navigate(`/course/${course.id}`), 1500);
        } catch (error) {
            console.error("Generation failed", error);
            setIsGenerating(false);
        }
    };

    return (
        <div className="max-w-2xl mx-auto py-8 px-4">
            <AnimatePresence mode="wait">
                {!isGenerating ? (
                    <motion.div
                        key="setup"
                        initial={{ opacity: 0, y: 16 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.97 }}
                        className="space-y-8"
                    >
                        {/* Header */}
                        <div className="text-center space-y-4">
                            <Badge variant="primary" icon={<Sparkles className="w-3 h-3" />}>
                                AI Course Architect
                            </Badge>
                            <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
                                What do you want to <span className="text-gradient">learn?</span>
                            </h1>
                            <p className="text-white/30 text-lg max-w-md mx-auto">
                                Tell us your topic and goals — our AI builds a personalized curriculum.
                            </p>
                        </div>

                        <Card className="p-8 space-y-8 relative overflow-hidden">
                            <div className="absolute -top-32 -right-32 w-64 h-64 bg-brand-primary/5 rounded-full blur-3xl pointer-events-none" />

                            {/* Step Progress */}
                            <div className="flex items-center gap-3 relative z-10">
                                {[1, 2].map((s) => (
                                    <React.Fragment key={s}>
                                        <button
                                            onClick={() => s < step && setStep(s)}
                                            className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm border-2 transition-all duration-500 ${step > s
                                                ? 'border-success bg-success/20 text-success'
                                                : step === s
                                                    ? 'border-brand-primary bg-brand-primary/10 text-brand-primary pulse-glow'
                                                    : 'border-white/10 text-white/20'
                                                }`}
                                        >
                                            {step > s ? <CheckCircle2 className="w-5 h-5" /> : s}
                                        </button>
                                        {s === 1 && (
                                            <div className="flex-1 h-0.5 rounded-full overflow-hidden bg-white/[0.06]">
                                                <motion.div
                                                    animate={{ width: step > 1 ? '100%' : '0%' }}
                                                    className="h-full bg-gradient-to-r from-success to-brand-primary rounded-full"
                                                    transition={{ duration: 0.5 }}
                                                />
                                            </div>
                                        )}
                                    </React.Fragment>
                                ))}
                            </div>

                            {/* Steps */}
                            <AnimatePresence mode="wait">
                                {step === 1 ? (
                                    <motion.div
                                        key="step1"
                                        initial={{ opacity: 0, x: 20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        exit={{ opacity: 0, x: -20 }}
                                        className="space-y-6 relative z-10"
                                    >
                                        <div className="space-y-3">
                                            <label className="text-lg font-semibold flex items-center gap-2">
                                                <Brain className="w-5 h-5 text-brand-primary" />
                                                Choose Your Topic
                                            </label>
                                            <Input
                                                placeholder="e.g. Machine Learning with Python, Web Development, Data Science..."
                                                value={formData.topic}
                                                onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
                                                className="text-base py-4 h-14"
                                            />
                                        </div>
                                        <Button
                                            className="w-full h-12"
                                            disabled={!formData.topic.trim()}
                                            onClick={() => setStep(2)}
                                        >
                                            Continue <ArrowRight className="w-4 h-4" />
                                        </Button>
                                    </motion.div>
                                ) : (
                                    <motion.div
                                        key="step2"
                                        initial={{ opacity: 0, x: 20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        exit={{ opacity: 0, x: -20 }}
                                        className="space-y-8 relative z-10"
                                    >
                                        {/* Level Selector */}
                                        <div className="space-y-3">
                                            <label className="text-lg font-semibold flex items-center gap-2">
                                                <Target className="w-5 h-5 text-brand-accent" />
                                                Skill Level
                                            </label>
                                            <div className="grid grid-cols-3 gap-3">
                                                {levels.map((lvl) => (
                                                    <button
                                                        key={lvl.value}
                                                        onClick={() => setFormData({ ...formData, level: lvl.value })}
                                                        className={`p-4 rounded-xl border-2 text-left transition-all duration-200 ${formData.level === lvl.value
                                                            ? 'border-brand-primary bg-brand-primary/10'
                                                            : 'border-white/[0.06] bg-white/[0.02] hover:border-white/10 hover:bg-white/[0.04]'
                                                            }`}
                                                    >
                                                        <div className={`mb-2 ${formData.level === lvl.value ? 'text-brand-primary' : 'text-white/30'}`}>
                                                            {lvl.icon}
                                                        </div>
                                                        <div className={`text-sm font-semibold ${formData.level === lvl.value ? 'text-white' : 'text-white/70'}`}>
                                                            {lvl.label}
                                                        </div>
                                                        <div className="text-[11px] text-white/25 mt-0.5">{lvl.desc}</div>
                                                    </button>
                                                ))}
                                            </div>
                                        </div>

                                        {/* Goal */}
                                        <div className="space-y-3">
                                            <label className="text-lg font-semibold flex items-center gap-2">
                                                <Layers className="w-5 h-5 text-brand-secondary" />
                                                Learning Goal
                                                <span className="text-xs text-white/20 font-normal">(optional)</span>
                                            </label>
                                            <textarea
                                                placeholder="e.g. I want to build production-ready ML models for my startup..."
                                                className="w-full bg-white/[0.04] border border-white/10 rounded-xl px-4 py-3.5 h-28 text-white placeholder:text-white/20 focus:outline-none focus:border-brand-primary/50 focus:bg-white/[0.06] focus:ring-4 focus:ring-brand-primary/10 transition-all duration-200 resize-none"
                                                value={formData.goal}
                                                onChange={(e) => setFormData({ ...formData, goal: e.target.value })}
                                            />
                                        </div>

                                        <div className="flex gap-3">
                                            <Button variant="secondary" className="flex-1" onClick={() => setStep(1)}>
                                                <ArrowLeft className="w-4 h-4" />
                                                Back
                                            </Button>
                                            <Button className="flex-[2] h-12" onClick={handleGenerate}>
                                                <Sparkles className="w-4 h-4" />
                                                Generate Course
                                            </Button>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </Card>
                    </motion.div>
                ) : (
                    /* ─── Generating State ─── */
                    <motion.div
                        key="generating"
                        initial={{ opacity: 0, scale: 1.05 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="flex flex-col items-center justify-center space-y-12 py-24 text-center"
                    >
                        {/* Orbiting rings */}
                        <div className="relative w-44 h-44">
                            <motion.div
                                animate={{ rotate: 360 }}
                                transition={{ duration: 12, repeat: Infinity, ease: "linear" }}
                                className="absolute inset-0 rounded-full border-2 border-dashed border-brand-primary/15"
                            />
                            <motion.div
                                animate={{ rotate: -360 }}
                                transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
                                className="absolute inset-3 rounded-full border-2 border-brand-primary/30 border-t-brand-primary shadow-[0_0_40px_rgba(99,102,241,0.3)]"
                            />
                            <motion.div
                                animate={{ rotate: 360 }}
                                transition={{ duration: 5, repeat: Infinity, ease: "linear" }}
                                className="absolute inset-8 rounded-full border-2 border-brand-secondary/40 border-b-transparent"
                            />
                            <div className="absolute inset-0 flex items-center justify-center">
                                <motion.div
                                    animate={{ scale: [1, 1.15, 1] }}
                                    transition={{ duration: 2, repeat: Infinity }}
                                >
                                    <Brain className="w-14 h-14 text-brand-primary" />
                                </motion.div>
                            </div>
                        </div>

                        <div className="space-y-3 max-w-md">
                            <h2 className="text-3xl font-bold">Crafting your curriculum...</h2>
                            <p className="text-white/25 leading-relaxed">
                                Our AI is researching <span className="text-brand-primary font-medium">{formData.topic}</span>, finding the best resources, and structuring your personalized learning path.
                            </p>
                        </div>

                        <div className="w-full max-w-xs space-y-2">
                            <div className="h-1.5 w-full bg-white/[0.04] rounded-full overflow-hidden">
                                <motion.div
                                    initial={{ width: "0%" }}
                                    animate={{ width: "100%" }}
                                    transition={{ duration: 20, ease: "linear" }}
                                    className="h-full bg-gradient-to-r from-brand-primary to-brand-secondary rounded-full"
                                />
                            </div>
                            <p className="text-[10px] uppercase tracking-[0.2em] text-white/15 font-bold">
                                Analyzing • Researching • Building
                            </p>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default GenerateCourse;
