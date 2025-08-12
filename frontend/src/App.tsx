import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box } from '@mui/material';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import ApplicationForm from './components/ApplicationForm';
import DocumentUpload from './components/DocumentUpload';
import Results from './components/Results';
import { useAppStore } from './store/appStore';

// Create theme matching Streamlit's appearance
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#ff4b4b', // Streamlit red
    },
    secondary: {
      main: '#00c0f2', // Streamlit blue
    },
    background: {
      default: '#ffffff',
      paper: '#f0f2f6',
    },
  },
  typography: {
    fontFamily: '"Source Sans Pro", sans-serif',
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: '0.5rem',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: '0.5rem',
        },
      },
    },
  },
});

function App() {
  const { currentView } = useAppStore();

  const renderMainContent = () => {
    switch (currentView) {
      case 'chat':
        return <ChatInterface />;
      case 'application':
        return <ApplicationForm />;
      case 'upload':
        return <DocumentUpload />;
      case 'results':
        return <Results />;
      default:
        return <ChatInterface />;
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', height: '100vh' }}>
          <Sidebar />
          <Box
            component="main"
            sx={{
              flexGrow: 1,
              p: 3,
              backgroundColor: 'background.default',
              overflow: 'auto',
            }}
          >
            <Routes>
              <Route path="/" element={renderMainContent()} />
              <Route path="/chat" element={<ChatInterface />} />
              <Route path="/application" element={<ApplicationForm />} />
              <Route path="/upload" element={<DocumentUpload />} />
              <Route path="/results" element={<Results />} />
            </Routes>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;
