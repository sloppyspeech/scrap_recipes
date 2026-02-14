import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

const api = axios.create({
    baseURL: API_BASE,
    timeout: 120000,
});

// ─── Recipes ────────────────────────────────────
export const searchRecipes = (params) =>
    api.get('/recipes/search', { params }).then((r) => r.data);

export const getRecipe = (id) =>
    api.get(`/recipes/${id}`).then((r) => r.data);

export const getTags = () =>
    api.get('/tags').then((r) => r.data);

// ─── Ollama ─────────────────────────────────────
export const summarizeRecipe = (id) =>
    api.post(`/recipes/${id}/summarize`).then((r) => r.data);

export const scaleRecipe = (id, targetServings, mode = 'llm') =>
    api.post(`/recipes/${id}/scale`, { target_servings: targetServings, mode }).then((r) => r.data);

// ─── Admin ──────────────────────────────────────
export const getModels = () =>
    api.get('/admin/models').then((r) => r.data);

export const setModel = (model) =>
    api.post('/admin/model', { model }).then((r) => r.data);

export const getSettings = () =>
    api.get('/admin/settings').then((r) => r.data);

export default api;
