import React, { useEffect, useState } from 'react';
import { courseService } from '../services/api';
import { CourseCard } from '../components/CourseCard';
import { Button, Skeleton, Badge } from '../components/ui';
import { Plus, Search, Sparkles, BookOpen, Layers, GraduationCap } from 'lucide-react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

const Dashboard = () => {
    const [courses, setCourses] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        const fetchCourses = async () => {
            try {
                const data = await courseService.getCourses();
                setCourses(data.results || data);
            } catch (error) {
                console.error("Failed to fetch courses", error);
            } finally {
                setLoading(false);
            }
        };
        fetchCourses();
    }, []);

    const filteredCourses = courses.filter(c =>
        c.topic?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.description?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const totalModules = courses.reduce((acc, c) => acc + (c.module_count ?? c.modules?.length ?? 0), 0);
    const totalLessons = courses.reduce((acc, c) => acc + (c.lesson_count ?? c.modules?.reduce((a: number, m: any) => a + (m.lessons?.length || 0), 0) ?? 0), 0);

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                <motion.div
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <Badge variant="primary" icon={<Sparkles className="w-3 h-3" />} className="mb-3">
                        AI-Powered Learning
                    </Badge>
                    <h1 className="text-3xl md:text-4xl font-bold tracking-tight">Your Courses</h1>
                    <p className="text-white/30 mt-1.5 text-base max-w-lg">
                        Continue learning or create a new AI-curated course.
                    </p>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.1 }}
                >
                    <Button onClick={() => navigate('/generate')} size="lg">
                        <Plus className="w-5 h-5" />
                        New Course
                    </Button>
                </motion.div>
            </div>

            {/* Stats */}
            {!loading && courses.length > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="grid grid-cols-3 gap-4"
                >
                    {[
                        { icon: <GraduationCap className="w-5 h-5" />, label: 'Courses', value: courses.length },
                        { icon: <Layers className="w-5 h-5" />, label: 'Modules', value: totalModules },
                        { icon: <BookOpen className="w-5 h-5" />, label: 'Lessons', value: totalLessons },
                    ].map((stat, i) => (
                        <div key={i} className="glass-card p-4 flex items-center gap-4">
                            <div className="w-10 h-10 rounded-xl bg-brand-primary/10 flex items-center justify-center text-brand-primary">
                                {stat.icon}
                            </div>
                            <div>
                                <div className="text-2xl font-bold">{stat.value}</div>
                                <div className="text-xs text-white/30 uppercase tracking-wider font-medium">{stat.label}</div>
                            </div>
                        </div>
                    ))}
                </motion.div>
            )}

            {/* Search */}
            <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15 }}
                className="relative"
            >
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20" />
                <input
                    type="text"
                    placeholder="Search your courses..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full bg-white/[0.03] border border-white/[0.06] rounded-xl pl-11 pr-4 py-3 text-sm text-white/80 placeholder:text-white/20 focus:outline-none focus:border-brand-primary/30 focus:bg-white/[0.04] transition-all duration-200"
                />
            </motion.div>

            {/* Course Grid */}
            {loading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {[1, 2, 3].map((i) => (
                        <Skeleton key={i} className="h-72" />
                    ))}
                </div>
            ) : filteredCourses.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pb-8">
                    {filteredCourses.map((course, index) => (
                        <CourseCard key={course.id} course={course} index={index} />
                    ))}
                </div>
            ) : courses.length > 0 && searchQuery ? (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="py-20 text-center text-white/30"
                >
                    <Search className="w-12 h-12 mx-auto mb-4 text-white/10" />
                    <p className="text-lg font-medium">No courses matching "{searchQuery}"</p>
                </motion.div>
            ) : (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="glass-card border-dashed border-white/[0.08] py-20 flex flex-col items-center justify-center text-center"
                >
                    <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-brand-primary/10 to-brand-secondary/10 border border-brand-primary/10 flex items-center justify-center mb-6">
                        <BookOpen className="w-10 h-10 text-brand-primary/40" />
                    </div>
                    <h2 className="text-2xl font-bold mb-2">Your library is empty</h2>
                    <p className="text-white/30 mb-8 max-w-sm">
                        Create your first AI-powered course and start your personalized learning journey.
                    </p>
                    <Button onClick={() => navigate('/generate')} size="lg">
                        <Sparkles className="w-4 h-4" />
                        Create Your First Course
                    </Button>
                </motion.div>
            )}
        </div>
    );
};

export default Dashboard;
