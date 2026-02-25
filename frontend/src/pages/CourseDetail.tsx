import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { courseService } from '../services/api';
import { Card, Button, Badge, Skeleton } from '../components/ui';
import { motion } from 'framer-motion';
import { BookOpen, PlayCircle, Clock, ChevronDown, ChevronUp, GraduationCap, Layers, CheckCircle2, Lock, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const CourseDetail = () => {
    const { id } = useParams<{ id: string }>();
    const [course, setCourse] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [expandedModules, setExpandedModules] = useState<Set<number>>(new Set());
    const navigate = useNavigate();

    useEffect(() => {
        const fetchCourse = async () => {
            try {
                const data = await courseService.getCourse(Number(id));
                setCourse(data);
                // Expand first module by default
                if (data.modules?.length > 0) {
                    setExpandedModules(new Set([data.modules[0].id]));
                }
            } catch (error) {
                console.error("Failed to fetch course", error);
            } finally {
                setLoading(false);
            }
        };
        fetchCourse();
    }, [id]);

    const toggleModule = (moduleId: number) => {
        setExpandedModules(prev => {
            const next = new Set(prev);
            if (next.has(moduleId)) {
                next.delete(moduleId);
            } else {
                next.add(moduleId);
            }
            return next;
        });
    };

    if (loading) {
        return (
            <div className="space-y-8">
                <Skeleton className="h-64 rounded-3xl" />
                <Skeleton className="h-48" />
                <Skeleton className="h-48" />
            </div>
        );
    }

    if (!course) {
        return (
            <div className="h-[60vh] flex flex-col items-center justify-center text-center space-y-4">
                <GraduationCap className="w-16 h-16 text-white/10" />
                <h2 className="text-2xl font-bold">Course not found</h2>
                <Button variant="secondary" onClick={() => navigate('/')}>Back to Dashboard</Button>
            </div>
        );
    }

    const totalLessons = course.modules?.reduce((acc: number, m: any) => acc + (m.lessons?.length || 0), 0) || 0;
    const completedLessons = course.modules?.reduce((acc: number, m: any) =>
        acc + (m.lessons?.filter((l: any) => l.content)?.length || 0), 0) || 0;

    return (
        <div className="space-y-8 pb-20">
            {/* Back Button */}
            <Button variant="ghost" onClick={() => navigate('/')} className="text-white/40 hover:text-white -ml-2">
                <ArrowLeft className="w-4 h-4" />
                Back to Dashboard
            </Button>

            {/* Hero */}
            <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                className="relative rounded-3xl overflow-hidden bg-gradient-to-br from-surface-1 to-surface-2 border border-white/[0.06] p-8 md:p-12"
            >
                {/* Decorative */}
                <div className="absolute top-0 right-0 w-1/2 h-full bg-gradient-to-l from-brand-primary/8 to-transparent pointer-events-none" />
                <div className="absolute -bottom-20 -right-20 w-64 h-64 bg-brand-secondary/8 rounded-full blur-[100px] pointer-events-none" />

                <div className="max-w-2xl space-y-6 relative z-10">
                    <motion.div
                        initial={{ opacity: 0, y: 12 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="flex items-center gap-3"
                    >
                        <Badge variant="primary" icon={<GraduationCap className="w-3 h-3" />}>
                            Course
                        </Badge>
                        {course.level && (
                            <Badge variant={
                                course.level === 'beginner' ? 'success' :
                                    course.level === 'advanced' ? 'primary' : 'warning'
                            }>
                                {course.level}
                            </Badge>
                        )}
                    </motion.div>

                    <motion.h1
                        initial={{ opacity: 0, y: 12 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.15 }}
                        className="text-3xl md:text-5xl font-bold tracking-tight leading-tight"
                    >
                        {course.topic}
                    </motion.h1>

                    {course.description && (
                        <motion.p
                            initial={{ opacity: 0, y: 12 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 }}
                            className="text-white/40 text-lg leading-relaxed"
                        >
                            {course.description}
                        </motion.p>
                    )}

                    <motion.div
                        initial={{ opacity: 0, y: 12 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.25 }}
                        className="flex flex-wrap gap-3 pt-2"
                    >
                        <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/[0.04] border border-white/[0.06] text-sm">
                            <Layers className="w-4 h-4 text-brand-primary" />
                            <span className="text-white/60">{course.modules?.length || 0} Modules</span>
                        </div>
                        <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/[0.04] border border-white/[0.06] text-sm">
                            <BookOpen className="w-4 h-4 text-brand-secondary" />
                            <span className="text-white/60">{totalLessons} Lessons</span>
                        </div>
                        <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/[0.04] border border-white/[0.06] text-sm">
                            <Clock className="w-4 h-4 text-brand-accent" />
                            <span className="text-white/60">~{(course.modules?.length || 0) * 2}h</span>
                        </div>
                    </motion.div>

                    {/* Progress */}
                    {totalLessons > 0 && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.3 }}
                            className="pt-2"
                        >
                            <div className="flex items-center justify-between text-xs text-white/30 mb-2">
                                <span>Progress</span>
                                <span>{completedLessons}/{totalLessons} lessons</span>
                            </div>
                            <div className="h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
                                <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: `${(completedLessons / totalLessons) * 100}%` }}
                                    transition={{ delay: 0.5, duration: 0.8, ease: "easeOut" }}
                                    className="h-full bg-gradient-to-r from-brand-primary to-brand-secondary rounded-full"
                                />
                            </div>
                        </motion.div>
                    )}
                </div>
            </motion.div>

            {/* Modules */}
            <div className="space-y-4">
                {course.modules?.map((module: any, mIdx: number) => (
                    <motion.div
                        key={module.id}
                        initial={{ opacity: 0, y: 16 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 + mIdx * 0.08 }}
                    >
                        <div className="glass-card overflow-hidden border-white/[0.04]">
                            {/* Module Header */}
                            <button
                                onClick={() => toggleModule(module.id)}
                                className="w-full p-5 flex items-center justify-between hover:bg-white/[0.02] transition-colors"
                            >
                                <div className="flex items-center gap-4">
                                    <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-brand-primary/15 to-brand-secondary/15 border border-brand-primary/10 flex items-center justify-center text-brand-primary font-bold text-sm">
                                        {mIdx + 1}
                                    </div>
                                    <div className="text-left">
                                        <h3 className="font-semibold text-white/90">{module.title}</h3>
                                        {module.description && (
                                            <p className="text-xs text-white/30 mt-0.5 line-clamp-1">{module.description}</p>
                                        )}
                                    </div>
                                </div>
                                <div className="flex items-center gap-3">
                                    <span className="text-xs text-white/20">
                                        {module.lessons?.length || 0} lessons
                                    </span>
                                    {expandedModules.has(module.id)
                                        ? <ChevronUp className="w-4 h-4 text-white/20" />
                                        : <ChevronDown className="w-4 h-4 text-white/20" />
                                    }
                                </div>
                            </button>

                            {/* Lessons */}
                            {expandedModules.has(module.id) && (
                                <motion.div
                                    initial={{ height: 0, opacity: 0 }}
                                    animate={{ height: 'auto', opacity: 1 }}
                                    transition={{ duration: 0.2 }}
                                    className="border-t border-white/[0.04]"
                                >
                                    {module.lessons?.map((lesson: any, lIdx: number) => (
                                        <Link
                                            key={lesson.id}
                                            to={`/lesson/${lesson.id}`}
                                            className="flex items-center justify-between p-4 pl-[4.5rem] hover:bg-white/[0.03] transition-colors group border-b border-white/[0.02] last:border-0"
                                        >
                                            <div className="flex items-center gap-3">
                                                {lesson.content ? (
                                                    <CheckCircle2 className="w-4 h-4 text-success flex-shrink-0" />
                                                ) : (
                                                    <div className="w-4 h-4 rounded-full border border-white/10 flex-shrink-0 group-hover:border-brand-primary/50 transition-colors" />
                                                )}
                                                <span className="text-sm text-white/60 group-hover:text-white transition-colors">
                                                    {lesson.title}
                                                </span>
                                            </div>
                                            <div className="flex items-center gap-3">
                                                {lesson.content ? (
                                                    <Badge variant="success" className="text-[9px] py-0.5">Completed</Badge>
                                                ) : (
                                                    <Badge variant="neutral" className="text-[9px] py-0.5">
                                                        <Lock className="w-2.5 h-2.5" />
                                                        Start
                                                    </Badge>
                                                )}
                                                <PlayCircle className="w-4 h-4 text-white/10 group-hover:text-brand-primary transition-colors" />
                                            </div>
                                        </Link>
                                    ))}
                                </motion.div>
                            )}
                        </div>
                    </motion.div>
                ))}
            </div>
        </div>
    );
};

export default CourseDetail;
