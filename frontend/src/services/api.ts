import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add interceptor to include token
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Token ${token}`;
    }
    return config;
});

export const authService = {
    login: async (credentials: any) => {
        const response = await axios.post(`${API_BASE_URL}/auth/token/`, credentials);
        return response.data;
    },

    register: async (userData: any) => {
        const response = await api.post('/users/', userData);
        return response.data;
    },

    getCurrentUser: async () => {
        const response = await api.get('/users/me/');
        return response.data;
    }
};

export const courseService = {
    getCourses: async () => {
        const response = await api.get('/courses/');
        return response.data;
    },

    getCourse: async (id: number) => {
        const response = await api.get(`/courses/${id}/`);
        return response.data;
    },

    generateCourse: async (data: any) => {
        const response = await api.post('/courses/generate/', data);
        return response.data;
    }
};

export const lessonService = {
    getLesson: async (id: number) => {
        const response = await api.get(`/lessons/${id}/`);
        return response.data;
    },

    // Streaming version uses native fetch for EventSource-like behavior
    generateContentStream: async (id: number, onChunk: (text: string) => void) => {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/lessons/${id}/generate_content/`, {
            method: 'POST',
            headers: {
                'Authorization': `Token ${token}`,
            },
        });

        if (!response.body) return;

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value);
            onChunk(chunk);
        }
    }
};

export const evaluationService = {
    generateQuiz: async (lessonId: number) => {
        const response = await api.post('/evaluations/generate_quiz/', { lesson_id: lessonId });
        return response.data;
    },

    submitQuiz: async (id: number, answers: string[]) => {
        const response = await api.post(`/evaluations/${id}/submit_quiz/`, { answers });
        return response.data;
    }
};

export default api;
