import { api } from './api';
import type { Category } from './types';

export const categoryService = {
  async getAll(): Promise<Category[]> {
    const response = await api.get<{ results: Category[] }>('/categories/');
    return response.results ?? response;
  },

  async getById(id: number): Promise<Category> {
    return api.get<Category>(`/categories/${id}/`);
  },

  async create(data: Omit<Category, 'id' | 'created_at'>): Promise<Category> {
    return api.post<Category>('/categories/', data);
  },

  async update(id: number, data: Partial<Category>): Promise<Category> {
    return api.patch<Category>(`/categories/${id}/`, data);
  },

  async delete(id: number): Promise<void> {
    return api.delete<void>(`/categories/${id}/`);
  },
};