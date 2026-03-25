import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiService = {
  // Health check
  healthCheck: () => axios.get(`${API_BASE_URL}/api/health`),
  
  // Demo data
  getDemoTrackA: () => axios.get(`${API_BASE_URL}/api/demo-track-a`),
  
  // Pipeline execution
  runPipeline: () => axios.post(`${API_BASE_URL}/api/run-pipeline`),
  runPipelineCSV: (formData: FormData) => 
    axios.post(`${API_BASE_URL}/api/run-pipeline-csv`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }),
  
  // Adversarial testing
  runAdversarialTest: (testType?: string) => 
    axios.get(`${API_BASE_URL}/api/adversarial-test`, {
      params: testType ? { test: testType } : undefined,
    }),
  
  // Feedback
  submitFeedback: (feedbackData: any) => 
    axios.post(`${API_BASE_URL}/api/feedback`, feedbackData),
  getFeedbackDecisions: (alertId?: string) => 
    axios.get(`${API_BASE_URL}/api/feedback/decisions`, {
      params: alertId ? { alert_id: alertId } : undefined,
    }),
  getFeedbackConfig: () => axios.get(`${API_BASE_URL}/api/feedback/config`),
};

export default apiService;