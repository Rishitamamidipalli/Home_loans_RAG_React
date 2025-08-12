# Home Loan Assistant - React + FastAPI Migration

This project migrates the original Streamlit-based Home Loan Assistant to a modern React frontend with FastAPI backend architecture.

## 🏗️ Architecture Overview

### Frontend (React + TypeScript + Material UI)
- **Framework**: React 18 with TypeScript
- **UI Library**: Material UI v5
- **State Management**: Zustand
- **HTTP Client**: Axios
- **Routing**: React Router v6

### Backend (FastAPI + Python)
- **Framework**: FastAPI
- **Authentication**: JWT (optional)
- **Database**: In-memory (can be replaced with Redis/PostgreSQL)
- **File Storage**: AWS S3
- **AI/ML**: Existing LangChain + AWS Bedrock integration

## 📁 Project Structure

```
home_loans_code_rag_streamlit/
├── backend/                    # FastAPI backend
│   ├── main.py                # FastAPI application
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example          # Environment variables template
│   └── __init__.py
├── frontend/                  # React frontend
│   ├── public/
│   │   └── index.html        # HTML template
│   ├── src/
│   │   ├── components/       # React components
│   │   │   ├── Sidebar.tsx
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── ApplicationForm.tsx
│   │   │   ├── DocumentUpload.tsx
│   │   │   └── Results.tsx
│   │   ├── services/
│   │   │   └── api.ts        # API service layer
│   │   ├── store/
│   │   │   └── appStore.ts   # Zustand state management
│   │   ├── App.tsx           # Main App component
│   │   ├── index.tsx         # React entry point
│   │   └── index.css         # Global styles
│   ├── package.json          # Node.js dependencies
│   └── tsconfig.json         # TypeScript configuration
├── start_backend.bat         # Backend startup script
├── start_frontend.bat        # Frontend startup script
└── README_MIGRATION.md       # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 16+
- AWS Account with S3 and Bedrock access

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy environment file and configure
copy .env.example .env
# Edit .env with your AWS credentials and configuration

# Start FastAPI server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start React development server
npm start
```

### 3. Using Startup Scripts (Windows)

Alternatively, use the provided batch files:

```bash
# Start backend (in one terminal)
start_backend.bat

# Start frontend (in another terminal)
start_frontend.bat
```

## 🔧 Configuration

### Backend Environment Variables (.env)

```env
# AWS Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_DEFAULT_REGION=us-east-1

# S3 Configuration
S3_BUCKET_NAME=your_s3_bucket_name
S3_PREFIX=home_loans/

# Bedrock Configuration
BEDROCK_REGION=us-east-1

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=["http://localhost:3000"]
```

## 📋 API Endpoints

### Chat Endpoints
- `POST /api/chat` - Send chat message
- `GET /api/chat/history/{session_id}` - Get chat history

### Application Endpoints
- `POST /api/application` - Submit loan application
- `GET /api/application/{session_id}/{application_id}` - Get application details

### Document Endpoints
- `POST /api/upload` - Upload document
- `GET /api/documents/{token}` - List documents
- `DELETE /api/documents/{token}/{filename}` - Delete document

## 🎨 UI Components

### 1. Sidebar Navigation
- Clean navigation between different sections
- Matches Streamlit's sidebar functionality
- Material UI Drawer component

### 2. Chat Interface
- Real-time chat with AI assistant
- Message history persistence
- Action buttons for forms and uploads
- Typing indicators and error handling

### 3. Application Form
- Multi-step form with validation
- Matches original Streamlit form fields exactly
- Progress indicator and navigation

### 4. Document Upload
- Drag-and-drop file upload
- Document checklist and status tracking
- File management (view, delete)

### 5. Results Display
- Loan recommendations and analysis
- Risk factors and next steps
- Interactive accordions and charts

## 🔄 Migration Benefits

### Improved Performance
- Client-side rendering reduces server load
- Better caching and state management
- Faster page transitions

### Enhanced User Experience
- Modern, responsive UI
- Better mobile support
- Improved accessibility

### Developer Experience
- Clear separation of concerns
- Type safety with TypeScript
- Better testing capabilities
- Easier deployment and scaling

## 🧪 Testing

### Backend Testing
```bash
cd backend
pytest tests/  # Add test files as needed
```

### Frontend Testing
```bash
cd frontend
npm test
```

## 🚢 Deployment

### Backend Deployment
- Use Docker for containerization
- Deploy to AWS ECS, Google Cloud Run, or similar
- Set up environment variables in production

### Frontend Deployment
- Build production bundle: `npm run build`
- Deploy to Netlify, Vercel, or AWS S3 + CloudFront
- Configure API endpoints for production

### Docker Setup (Optional)

Create `Dockerfile` for backend:
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🔍 Key Features Preserved

✅ **Exact UI Match**: All Streamlit components replicated in React  
✅ **LLM Integration**: Unchanged AI/ML workflows  
✅ **Multi-agent System**: Preserved orchestration logic  
✅ **S3 Integration**: Document upload/management  
✅ **Session Management**: User state persistence  
✅ **Form Validation**: Complete application processing  

## 🛠️ Customization

### Adding New Components
1. Create component in `frontend/src/components/`
2. Add to routing in `App.tsx`
3. Update store if needed in `appStore.ts`

### Adding New API Endpoints
1. Add endpoint in `backend/main.py`
2. Create Pydantic models for request/response
3. Add service function in `frontend/src/services/api.ts`

### Styling Customization
- Modify theme in `App.tsx`
- Add custom CSS in component files
- Use Material UI's sx prop for inline styles

## 📞 Support

For issues or questions:
1. Check the original Streamlit code for business logic reference
2. Review Material UI documentation for UI components
3. Check FastAPI documentation for backend functionality

## 🎯 Next Steps

1. **Testing**: Add comprehensive unit and integration tests
2. **Authentication**: Implement user authentication if needed
3. **Database**: Replace in-memory storage with persistent database
4. **Monitoring**: Add logging and monitoring
5. **Performance**: Optimize bundle size and API responses
