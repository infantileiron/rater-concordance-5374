import {request,post} from './client';import type {Scale} from '../types/domain';
export const list=()=>request<Scale[]>('/scales');
export const create=(data:unknown)=>post<Scale>('/scales',data);
