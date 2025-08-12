import { create } from 'zustand';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

interface ApplicationData {
  // Personal Information
  first_name: string;
  last_name: string;
  date_of_birth: string;
  ssn: string;
  phone: string;
  email: string;
  marital_status: string;
  dependents: number;
  
  // Employment Information
  employment_status: string;
  employer_name: string;
  job_title: string;
  employment_duration_years: number;
  employment_duration_months: number;
  annual_income: number;
  additional_income: number;
  
  // Financial Information
  monthly_debt_payments: number;
  credit_score: number;
  down_payment: number;
  savings_amount: number;
  checking_balance: number;
  investment_accounts: number;
  retirement_accounts: number;
  
  // Property Information
  property_type: string;
  property_value: number;
  property_address: string;
  property_city: string;
  property_state: string;
  property_zip: string;
  loan_purpose: string;
  loan_amount: number;
  loan_term: number;
}

interface AppState {
  // Navigation
  currentView: 'chat' | 'application' | 'upload' | 'results';
  setCurrentView: (view: 'chat' | 'application' | 'upload' | 'results') => void;
  
  // Chat
  chatHistory: ChatMessage[];
  addChatMessage: (message: ChatMessage) => void;
  setChatHistory: (history: ChatMessage[]) => void;
  
  // Session
  sessionId: string;
  setSessionId: (id: string) => void;
  // Optional existing customer token for uploads
  uploadToken: string | null;
  setUploadToken: (token: string | null) => void;
  
  // Application
  applicationData: Partial<ApplicationData>;
  setApplicationData: (data: Partial<ApplicationData>) => void;
  applications: Record<string, ApplicationData>;
  setApplications: (apps: Record<string, ApplicationData>) => void;
  
  // UI State
  showFormButton: boolean;
  showUploadButton: boolean;
  showUpdateButton: boolean;
  showCancelButton: boolean;
  setUIButtons: (buttons: {
    showFormButton?: boolean;
    showUploadButton?: boolean;
    showUpdateButton?: boolean;
    showCancelButton?: boolean;
  }) => void;
  
  // Documents
  uploadedDocuments: string[];
  setUploadedDocuments: (docs: string[]) => void;
  
  // Loading states
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
}

export const useAppStore = create<AppState>((set, get) => ({
  // Navigation
  currentView: 'chat',
  setCurrentView: (view) => set({ currentView: view }),
  
  // Chat
  chatHistory: [{
    role: 'assistant',
    content: "Hello! I'm your Home Loan Assistant. I can help you with information about home loans, eligibility, interest rates, and more. How can I assist you today?"
  }],
  addChatMessage: (message) => set((state) => ({
    chatHistory: [...state.chatHistory, message]
  })),
  setChatHistory: (history) => set({ chatHistory: history }),
  
  // Session
  sessionId: `session_${Date.now()}`,
  setSessionId: (id) => set({ sessionId: id }),
  // Existing customer token (optional)
  uploadToken: null,
  setUploadToken: (token) => set({ uploadToken: token }),
  
  // Application
  applicationData: {},
  setApplicationData: (data) => set((state) => ({
    applicationData: { ...state.applicationData, ...data }
  })),
  applications: {},
  setApplications: (apps) => set({ applications: apps }),
  
  // UI State
  showFormButton: false,
  showUploadButton: false,
  showUpdateButton: false,
  showCancelButton: false,
  setUIButtons: (buttons) => set((state) => ({
    showFormButton: buttons.showFormButton ?? state.showFormButton,
    showUploadButton: buttons.showUploadButton ?? state.showUploadButton,
    showUpdateButton: buttons.showUpdateButton ?? state.showUpdateButton,
    showCancelButton: buttons.showCancelButton ?? state.showCancelButton,
  })),
  
  // Documents
  uploadedDocuments: [],
  setUploadedDocuments: (docs) => set({ uploadedDocuments: docs }),
  
  // Loading states
  isLoading: false,
  setIsLoading: (loading) => set({ isLoading: loading }),
}));
