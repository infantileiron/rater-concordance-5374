import {request,post} from './client';import type {Report} from '../types/domain';
export const list=()=>request<Report[]>('/reports');
export const create=(data:unknown)=>post<Report>('/reports',data);
