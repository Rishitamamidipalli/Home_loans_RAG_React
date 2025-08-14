import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface FileUrls {
  file_id: string;
  upload_url: string;
  delete_url: string;
}

export interface UploadedFile {
  file_id: string;
  name: string;
  type: string;
  size: number;
  _file_urls: FileUrls;
}

export interface Document {
  name: string;
  s3_path: string;
  size: number;
  last_modified: string;
  file_id: string;
  type: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  message: string;
  session_id: string;
}

export interface ChatResponse {
  response: string;
  show_form_button: boolean;
  show_upload_button: boolean;
  show_update_button: boolean;
  show_cancel_button: boolean;
}

// Make ApplicationFormData flexible to support updated backend fields
export interface ApplicationFormData {
  [key: string]: any;
}

export interface ApplicationResponse {
  success: boolean;
  message: string;
  application_id?: string;
}
export interface DocumentUploadResponse {
  success: boolean;
  message: string;
  file?: UploadedFile;
  s3_path?: string;
}

// Chat API
export const sendChatMessage = async (message: string, sessionId: string): Promise<ChatResponse> => {
  const response = await api.post<ChatResponse>('/api/chat', {
    message,
    session_id: sessionId,
  });
  return response.data;
};

export const getChatHistory = async (sessionId: string): Promise<ChatMessage[]> => {
  const response = await api.get<{ chat_history: ChatMessage[] }>(`/api/chat/history/${sessionId}`);
  return response.data.chat_history;
};

// Application API
export const submitApplication = async (
  applicationData: ApplicationFormData,
  sessionId: string
): Promise<ApplicationResponse> => {
  const formData = new FormData();
  
  // Add all application fields to FormData
  Object.entries(applicationData).forEach(([key, value]) => {
    formData.append(key, value.toString());
  });
  formData.append('session_id', sessionId);

  const response = await api.post<ApplicationResponse>('/api/application', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getApplication = async (sessionId: string, applicationId: string): Promise<ApplicationFormData> => {
  const response = await api.get<ApplicationFormData>(`/api/application/${sessionId}/${applicationId}`);
  return response.data;
};
// In frontend/src/services/api.ts
export const uploadDocument = async (
  file: File,
  sessionId: string,
  applicationId: string
): Promise<DocumentUploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('session_id', sessionId);
  
  const response = await api.post<DocumentUploadResponse>(
    '/api/upload',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }
  );
  return response.data;
};
export const listDocuments = async (token: string): Promise<Document[]> => {
  const response = await api.get<{ documents: Document[] }>(`/api/documents/${token}`);
  return response.data.documents;
};

export const deleteDocument = async (file_id: string, token: string): Promise<void> => {
  await api.delete(`/api/documents/${token}/${file_id}`);
};

export default api;

