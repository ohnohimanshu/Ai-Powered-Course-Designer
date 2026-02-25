import React from 'react';
import { motion } from 'framer-motion';
import { Card, Badge } from './ui';
import { BookOpen, Calendar, ArrowUpRight, GraduationCap, Layers } from 'lucide-react';
import { Link } from 'react-router-dom';

interface CourseCardProps {
    course: any;
    index: number;
}

const levelColors: Record<string, string> = {
    beginner: 'success',
    intermediate: 'warning',
    advanced: 'primary',
};

export const CourseCard: React.FC<CourseCardProps> = ({ course, index }) => {
    const moduleCount = course.module_count ?? course.modules?.length ?? 0;
    const lessonCount = course.lesson_count ?? course.modules?.reduce((acc: number, m: any) => acc + (m.lessons?.length || 0), 0) ?? 0;
    const level = course.level || 'beginner';

    return (
        <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.08, duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
        >
            <Link to={`/course/${course.id}`} className="block group">
                <Card hover className="h-full flex flex-col overflow-hidden p-0 border-white/[0.04]">
                    {/* Gradient Top Stripe */}
                    <div className="h-1 bg-gradient-to-r from-brand-primary via-brand-secondary to-brand-accent" />

                    <div className="p-6 flex-1 flex flex-col">
                        {/* Header */}
                        <div className="flex items-start justify-between mb-4">
                            <motion.div
                                whileHover={{ rotate: -10 }}
                                className="w-11 h-11 rounded-xl bg-gradient-to-br from-brand-primary/15 to-brand-secondary/15 border border-brand-primary/10 flex items-center justify-center group-hover:from-brand-primary/25 group-hover:to-brand-secondary/25 transition-all duration-300"
                            >
                                <GraduationCap className="w-5 h-5 text-brand-primary" />
                            </motion.div>
                            <ArrowUpRight className="w-4 h-4 text-white/0 group-hover:text-brand-primary transition-all duration-300 translate-y-1 group-hover:translate-y-0" />
                        </div>

                        {/* Content */}
                        <div className="flex-1">
                            <h3 className="text-lg font-bold mb-2 line-clamp-2 group-hover:text-brand-primary transition-colors duration-200">
                                {course.topic}
                            </h3>
                            <p className="text-white/35 text-sm line-clamp-2 leading-relaxed">
                                {course.description || `Explore the fundamentals and advanced concepts of ${course.topic}.`}
                            </p>
                        </div>

                        {/* Tags */}
                        <div className="flex items-center gap-2 mt-4">
                            <Badge variant={levelColors[level] as any || 'neutral'} className="text-[10px]">
                                {level}
                            </Badge>
                        </div>

                        {/* Footer */}
                        <div className="flex items-center justify-between text-xs text-white/25 pt-4 mt-4 border-t border-white/[0.04]">
                            <div className="flex items-center gap-4">
                                <span className="flex items-center gap-1.5">
                                    <Layers className="w-3.5 h-3.5" />
                                    {moduleCount} modules
                                </span>
                                <span className="flex items-center gap-1.5">
                                    <BookOpen className="w-3.5 h-3.5" />
                                    {lessonCount} lessons
                                </span>
                            </div>
                            <span className="flex items-center gap-1.5">
                                <Calendar className="w-3.5 h-3.5" />
                                {new Date(course.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                            </span>
                        </div>
                    </div>
                </Card>
            </Link>
        </motion.div>
    );
};
