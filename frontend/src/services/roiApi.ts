
import { api } from './api';

export interface ROISimulationParams {
    requestsPerYear: number;
    employees: number;
    manualTimeMins: number;
    avgValue?: number;
}

export interface ROIResult {
    potential_savings: number;
    revenue_upside: number;
    hours_saved_annually: number;
    pipeline_value: number;
    currency: string;
}

export const roiApi = {
    calculateROI: async (params: ROISimulationParams): Promise<ROIResult> => {
        const response = await api.post('/impact/simulate', {
            requests_per_year: params.requestsPerYear,
            employees: params.employees,
            manual_time_mins: params.manualTimeMins,
            avg_value_per_quote: params.avgValue || 2500 // Default avg value
        });
        return response.data;
    }
};
