# Home Loan Application Migration Guide

## Project Migration from Streamlit to React + FastAPI

### Core Requirements
1. Preserve all LLM and multi-agent functionality exactly
2. Match Streamlit UI appearance and behavior in React
3. Use Material UI as primary component library (Tailwind for custom styling if needed)
4. Implement FastAPI backend to replace Streamlit server
5. Maintain all existing file processing and S3 integration

### Architecture Overview
- **Frontend**: React (TypeScript) with:
  - Material UI components
  - React Router for navigation
  - Axios for API calls
  - Zustand/Redux for state management (to replace Streamlit session state)

- **Backend**: FastAPI with:
  - Same LLM/agent orchestration logic
  - Pydantic models for request/response validation
  - AWS SDK for S3 integration
  - CORS middleware for frontend access

### Key Components to Migrate
1. **Main Application Flow**:
   - Chat interface (from chatbot.py)
   - Application form (main.py render_application_form)
   - Document upload (main.py render_document_upload)
   - Results display (main.py render_results)

2. **Backend Services**:
   - Orchestration agent (orchestration_agent.py)
   - Loan recommender agent (agent/loan_recommender_agent.py)
   - S3 manager (s3_manager.py)
   - Utility functions (utils.py)

3. **State Management**:
   - Convert Streamlit session state to React state management
   - Maintain chat history persistence
   - Preserve application data flow

### Implementation Steps
1. Set up React project with required dependencies
2. Create FastAPI project structure
3. Implement UI components matching Streamlit:
   - Layout structure
   - Form components
   - Chat interface
   - Results display
4. Connect frontend to backend APIs
5. Test for functional parity
6. Document installation and setup

### Required Dependencies
#### Frontend:
- react
- react-dom
- @mui/material
- @emotion/react
- @emotion/styled
- axios
- react-router-dom
- zustand (or redux)

#### Backend:
- fastapi
- uvicorn
- python-multipart
- pydantic
- boto3
- Existing LLM/agent dependencies from requirements.txt

### File Structure
```
home-loan-app/
  frontend/
    public/
    src/
      components/
        ChatInterface.tsx
        ApplicationForm.tsx
        DocumentUpload.tsx
        ResultsDisplay.tsx
      services/
        api.ts
        s3Service.ts
      stores/
        appStore.ts
      App.tsx
      main.tsx
  backend/
    main.py
    agents/
      orchestration_agent.py
      loan_recommender_agent.py
    services/
      s3_manager.py
    utils/
      utils.py
    models/
      schemas.py
    api/
      endpoints.py
```
