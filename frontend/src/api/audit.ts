import {request,post} from './client';import type {Audit} from '../types/domain';
export const list=()=>request<Audit[]>('/audit');
