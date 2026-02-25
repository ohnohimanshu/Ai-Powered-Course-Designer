import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { lessonService, evaluationService } from '../services/api';
import { Card, Button, Badge } from '../components/ui';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Sparkles, BookOpen, CheckCircle2, RefreshCw, HelpCircle, X, Trophy, AlertCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

const LessonPlayer = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const [lesson, setLesson] = useState<any>(null);
    const [content, setContent] = useState('');
    const [isStreaming, setIsStreaming] = useState(false);
    const [showQuiz, setShowQuiz] = useState(false);
    const [quiz, setQuiz] = useState<any>(null);
    const [loadingQuiz, setLoadingQuiz] = useState(false);
    const contentEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const fetchLesson = async () => {
            try {
                const data = await lessonService.getLesson(Number(id));
                setLesson(data);
                if (data.content) {
                    setContent(data.content);
                } else {
                    handleGenerate();
                }
            } catch (error) {
                console.error("Failed to fetch lesson", error);
            }
        };
        fetchLesson();
    }, [id]);

    const handleGenerate = async () => {
        setContent('');
        setIsStreaming(true);
        try {
            await lessonService.generateContentStream(Number(id), (chunk) => {
                setContent(prev => prev + chunk);
                contentEndRef.current?.scrollIntoView({ behavior: 'smooth' });
            });
        } catch (error) {
            console.error("Streaming failed", error);
        } finally {
            setIsStreaming(false);
        }
    };

    const handleTakeQuiz = async () => {
        setLoadingQuiz(true);
        try {
            const quizData = await evaluationService.generateQuiz(Number(id));
            setQuiz(quizData);
            setShowQuiz(true);
        } catch (error) {
            console.error("Failed to generate quiz", error);
        } finally {
            setLoadingQuiz(false);
        }
    };

    if (!lesson) {
        return (
            <div className="h-[60vh] flex items-center justify-center">
                <div className="w-10 h-10 border-3 border-brand-primary/30 border-t-brand-primary rounded-full animate-spin" />
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto space-y-6 pb-24">
            {/* Top Bar */}
            <div className="flex items-center justify-between">
                <Button variant="ghost" onClick={() => navigate(-1)} className="text-white/40 hover:text-white -ml-2">
                    <ArrowLeft className="w-4 h-4" />
                    Back
                </Button>

                <Button variant="secondary" size="sm" onClick={handleGenerate} disabled={isStreaming}>
                    <RefreshCw className={`w-3.5 h-3.5 ${isStreaming ? 'animate-spin' : ''}`} />
                    Regenerate
                </Button>
            </div>

            {/* Main Content Card */}
            <Card className="p-0 overflow-hidden border-white/[0.04]">
                {/* Header */}
                <div className="p-6 md:p-8 border-b border-white/[0.04] bg-white/[0.02]">
                    <div className="flex items-center justify-between">
                        <div className="space-y-2">
                            <div className="flex items-center gap-2">
                                <Badge variant="primary" icon={<BookOpen className="w-3 h-3" />} className="text-[10px]">
                                    {lesson.module_title}
                                </Badge>
                                {isStreaming && (
                                    <Badge variant="warning" icon={<Sparkles className="w-3 h-3" />} className="text-[10px] animate-pulse">
                                        Streaming...
                                    </Badge>
                                )}
                            </div>
                            <h1 className="text-2xl md:text-3xl font-bold">{lesson.title}</h1>
                        </div>
                    </div>

                    {/* Streaming progress bar */}
                    {isStreaming && (
                        <div className="mt-4 h-0.5 bg-white/[0.04] rounded-full overflow-hidden">
                            <motion.div
                                initial={{ width: "0%" }}
                                animate={{ width: "100%" }}
                                transition={{ duration: 60, ease: "linear" }}
                                className="h-full bg-gradient-to-r from-brand-primary to-brand-accent rounded-full"
                            />
                        </div>
                    )}
                </div>

                {/* Content Body */}
                <div className="p-6 md:p-10 prose prose-invert prose-custom">
                    {content ? (
                        <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                                code({ node, inline, className, children, ...props }: any) {
                                    const match = /language-(\w+)/.exec(className || '');
                                    return !inline && match ? (
                                        <div className="relative group">
                                            <div className="absolute top-3 right-3 text-[10px] uppercase tracking-wider text-white/20 font-bold">
                                                {match[1]}
                                            </div>
                                            <SyntaxHighlighter
                                                children={String(children).replace(/\n$/, '')}
                                                style={vscDarkPlus as any}
                                                language={match[1]}
                                                PreTag="div"
                                                customStyle={{
                                                    background: 'rgba(17, 17, 39, 0.8)',
                                                    borderRadius: '12px',
                                                    border: '1px solid rgba(255,255,255,0.05)',
                                                    padding: '1.5rem',
                                                    fontSize: '0.875rem',
                                                }}
                                                {...props}
                                            />
                                        </div>
                                    ) : (
                                        <code className={className} {...props}>
                                            {children}
                                        </code>
                                    );
                                }
                            }}
                        >
                            {content}
                        </ReactMarkdown>
                    ) : (
                        <div className="py-24 flex flex-col items-center justify-center text-center space-y-4">
                            <motion.div
                                animate={{ scale: [1, 1.1, 1] }}
                                transition={{ duration: 2, repeat: Infinity }}
                            >
                                <Sparkles className="w-12 h-12 text-brand-primary/30" />
                            </motion.div>
                            <p className="text-white/20 text-lg font-medium">Generating lesson content...</p>
                        </div>
                    )}
                    <div ref={contentEndRef} />
                </div>

                {/* Lesson Complete Footer */}
                {content && !isStreaming && (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="p-6 md:p-8 bg-gradient-to-r from-brand-primary/[0.06] to-brand-secondary/[0.04] border-t border-brand-primary/10"
                    >
                        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                            <div className="flex items-center gap-4">
                                <div className="w-11 h-11 rounded-xl bg-success/10 border border-success/20 flex items-center justify-center">
                                    <CheckCircle2 className="w-5 h-5 text-success" />
                                </div>
                                <div>
                                    <h3 className="font-semibold">Lesson Complete!</h3>
                                    <p className="text-sm text-white/30">Test your understanding with a quiz</p>
                                </div>
                            </div>
                            <Button onClick={handleTakeQuiz} isLoading={loadingQuiz}>
                                <HelpCircle className="w-4 h-4" />
                                Take Quiz
                            </Button>
                        </div>
                    </motion.div>
                )}
            </Card>

            {/* Quiz Modal */}
            <AnimatePresence>
                {showQuiz && quiz && (
                    <QuizModal
                        quiz={quiz}
                        onClose={() => setShowQuiz(false)}
                        onComplete={() => navigate(-1)}
                    />
                )}
            </AnimatePresence>
        </div>
    );
};

/* ─── Quiz Modal ─── */
const QuizModal = ({ quiz, onClose }: any) => {
    const [answers, setAnswers] = useState<string[]>(new Array(quiz.questions?.length).fill(''));
    const [submitting, setSubmitting] = useState(false);
    const [result, setResult] = useState<any>(null);

    const handleSubmit = async () => {
        setSubmitting(true);
        try {
            const data = await evaluationService.submitQuiz(quiz.id, answers);
            setResult(data);
        } catch (error) {
            console.error("Submission failed", error);
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-surface-0/80 backdrop-blur-lg"
            onClick={(e) => e.target === e.currentTarget && onClose()}
        >
            <motion.div
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: 20 }}
                className="w-full max-w-2xl max-h-[90vh] overflow-y-auto glass-card border-white/[0.08] p-8 relative"
            >
                {/* Close button */}
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 p-2 rounded-lg hover:bg-white/5 text-white/30 hover:text-white transition-colors"
                >
                    <X className="w-4 h-4" />
                </button>

                {!result ? (
                    <div className="space-y-8">
                        <div>
                            <Badge variant="primary" icon={<HelpCircle className="w-3 h-3" />} className="mb-3">
                                Knowledge Check
                            </Badge>
                            <h2 className="text-2xl font-bold">Test Your Understanding</h2>
                            <p className="text-white/30 text-sm mt-1">{quiz.lesson_title}</p>
                        </div>

                        <div className="space-y-8">
                            {quiz.questions?.map((q: any, i: number) => (
                                <div key={i} className="space-y-3">
                                    <h4 className="font-medium flex gap-3">
                                        <span className="text-brand-primary font-bold min-w-[1.5rem]">{i + 1}.</span>
                                        <span className="text-white/80">{q.text}</span>
                                    </h4>
                                    <div className="grid grid-cols-1 gap-2 pl-7">
                                        {q.options?.map((opt: string) => (
                                            <button
                                                key={opt}
                                                onClick={() => {
                                                    const newAns = [...answers];
                                                    newAns[i] = opt;
                                                    setAnswers(newAns);
                                                }}
                                                className={`text-left px-4 py-3 rounded-xl text-sm border transition-all duration-200 ${answers[i] === opt
                                                    ? 'bg-brand-primary/10 border-brand-primary/40 text-white'
                                                    : 'bg-white/[0.02] border-white/[0.06] text-white/60 hover:border-white/10 hover:bg-white/[0.04]'
                                                    }`}
                                            >
                                                {opt}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div className="flex gap-3 pt-4">
                            <Button variant="secondary" className="flex-1" onClick={onClose}>Cancel</Button>
                            <Button
                                className="flex-[2]"
                                onClick={handleSubmit}
                                isLoading={submitting}
                                disabled={answers.some(a => !a)}
                            >
                                Submit Answers
                            </Button>
                        </div>
                    </div>
                ) : (
                    <div className="text-center space-y-8 py-4">
                        <div>
                            <motion.div
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                transition={{ type: 'spring', stiffness: 200, damping: 15 }}
                                className={`text-7xl font-black mb-4 ${result.score >= 70 ? 'text-success' : 'text-danger'}`}
                            >
                                {result.score}%
                            </motion.div>
                            <div className="flex items-center justify-center gap-2 mb-1">
                                {result.score >= 70
                                    ? <Trophy className="w-5 h-5 text-success" />
                                    : <AlertCircle className="w-5 h-5 text-danger" />
                                }
                                <h2 className="text-2xl font-bold">
                                    {result.score >= 70 ? 'Excellent Work!' : 'Keep Learning!'}
                                </h2>
                            </div>
                            <p className="text-white/30 text-sm">
                                {result.score >= 70
                                    ? 'Great job! You have a solid understanding.'
                                    : 'Review the material and try again.'}
                            </p>
                        </div>

                        <div className="space-y-3 text-left">
                            <h4 className="text-xs font-bold uppercase tracking-widest text-white/20">Review</h4>
                            {quiz.questions?.map((q: any, i: number) => (
                                <div
                                    key={i}
                                    className={`p-4 rounded-xl border ${result.feedback?.[i]?.correct
                                        ? 'bg-success/[0.04] border-success/15'
                                        : 'bg-danger/[0.04] border-danger/15'
                                        }`}
                                >
                                    <p className="font-medium text-sm mb-1.5">{q.text}</p>
                                    <p className="text-xs text-white/35">{result.feedback?.[i]?.explanation}</p>
                                </div>
                            ))}
                        </div>

                        <Button className="w-full" onClick={onClose}>
                            Continue
                        </Button>
                    </div>
                )}
            </motion.div>
        </motion.div>
    );
};

export default LessonPlayer;
