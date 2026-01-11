export interface UnifiedResponse<T> {
    code: number;
    message: string;
    data: T;
}
