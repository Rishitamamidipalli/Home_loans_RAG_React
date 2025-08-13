import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  Avatar,
  IconButton,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Send as SendIcon,
  Person as PersonIcon,
  SmartToy as BotIcon,
  Description as FormIcon,
  CloudUpload as UploadIcon,
} from '@mui/icons-material';

import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../store/appStore';
import { sendChatMessage } from '../services/api';

const ChatInterface: React.FC = () => {
  const {
    chatHistory,
    addChatMessage,
    sessionId,
    isLoading,
    setIsLoading,
    showUploadButton,
    setUIButtons,
    setCurrentView,
    setSessionId,
  } = useAppStore();
  const navigate = useNavigate();

  const [message, setMessage] = useState('');
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [expectingToken, setExpectingToken] = useState(false);
  const [initialOptionsUsed, setInitialOptionsUsed] = useState(false);
  const [shouldShowOptions, setShouldShowOptions] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory]);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        // This endpoint needs to be created in the backend
        const response = await fetch(`http://localhost:8000/api/chat/history/${sessionId}`);
        if (response.ok) {
          const data = await response.json();
          useAppStore.setState({
            chatHistory: data.history,
            showFormButton: data.show_form_button,
            showUploadButton: data.show_upload_button,
            showUpdateButton: data.show_update_button,
            showCancelButton: data.show_cancel_button
          });
        }
      } catch (error) {
        console.error('Failed to fetch chat history:', error);
      }
    };

    if (sessionId) {
      fetchHistory();
    }
  }, [sessionId]);

  const handleSendMessage = async () => {
    if (expectingToken) {
      const tokenVal = message.trim();
      addChatMessage({ role: 'user', content: tokenVal });
      setSessionId(tokenVal);
      setMessage('');
      setExpectingToken(false);
      setUIButtons({ showUploadButton: true }); 
      addChatMessage({ 
        role: 'assistant', 
        content: `Thank you. You can now upload documents for application ${tokenVal}.`
      });
      navigate('/documents');
      return;
    }

    const userMessage = { role: 'user' as const, content: message };
    addChatMessage(userMessage);
    setMessage('');
    setIsLoading(true);
    setError(null);

    try {
      const response = await sendChatMessage(userMessage.content, sessionId);
      const assistantMessage = { role: 'assistant' as const, content: response.response };
      addChatMessage(assistantMessage);
      // Update UI buttons based on response
      setUIButtons({
        showFormButton: response.show_form_button,
        showUploadButton: response.show_upload_button,
        showUpdateButton: response.show_update_button,
        showCancelButton: response.show_cancel_button,
      });
    } catch (err) {
      setError('Failed to send message. Please try again.');
      console.error('Chat error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  const handleGoToForm = () => {
    setUIButtons({ showFormButton: false });
    setInitialOptionsUsed(true);
    setCurrentView('application');
  };

  const handleOpenExisting = () => {
    addChatMessage({
      role: 'assistant',
      content: 'Please enter your application token.',
    });
    setExpectingToken(true);
    setInitialOptionsUsed(true);
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper sx={{ p: 2, mb: 2, backgroundColor: 'primary.main', color: 'white' }}>
        <Typography variant="h5" component="h1" sx={{ fontWeight: 'bold' }}>
          💬 Home Loan Chat Assistant
        </Typography>
        <Typography variant="body2" sx={{ opacity: 0.9, mt: 0.5 }}>
          Ask me anything about home loans, eligibility, rates, and more!
        </Typography>
      </Paper>

      {chatHistory.map((msg, index) => (
          <Box
            key={index}
            sx={{
              display: 'flex',
              mb: 2,
              alignItems: 'flex-start',
              flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
            }}
          >
            <Avatar
              sx={{
                bgcolor: msg.role === 'user' ? 'primary.main' : 'secondary.main',
                mx: 1,
                width: 32,
                height: 32,
              }}
            >
              {msg.role === 'user' ? <PersonIcon fontSize="small" /> : <BotIcon fontSize="small" />}
            </Avatar>
            <Paper
              sx={{
                p: 2,
                maxWidth: '70%',
                backgroundColor: msg.role === 'user' ? 'primary.light' : 'white',
                color: msg.role === 'user' ? 'white' : 'text.primary',
                borderRadius: 2,
                boxShadow: 1,
              }}
            >
              <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                {msg.content}
              </Typography>
            </Paper>
          </Box>
        ))}
        
        {isLoading && (
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Avatar sx={{ bgcolor: 'secondary.main', mx: 1, width: 32, height: 32 }}>
              <BotIcon fontSize="small" />
            </Avatar>
            <Paper sx={{ p: 2, backgroundColor: 'white', borderRadius: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <CircularProgress size={16} sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Thinking...
                </Typography>
              </Box>
            </Paper>
          </Box>
        )}
        
        <div ref={messagesEndRef} />

       
      {/* Action Buttons */}
      {chatHistory.length > 0 &&
        chatHistory[chatHistory.length - 1].role === 'assistant' &&
        chatHistory[chatHistory.length - 1].content.includes('Are you an existing customer?') &&
        !initialOptionsUsed && (
        <Box sx={{ mb: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Button
            variant="contained"
            startIcon={<FormIcon />}
            onClick={handleGoToForm}
            sx={{ borderRadius: 2 }}
          >
            New Customer - Start Application
          </Button>
          <Button
            variant="outlined"
            startIcon={<UploadIcon />}
            onClick={handleOpenExisting}
            sx={{ borderRadius: 2 }}
          >
            Existing Customer - Enter Token
          </Button>
        </Box>
      )}

      {/* Upload Documents Button */}
      {showUploadButton && (
        <Box sx={{ mb: 2 }}>
          <Button
            variant="contained"
            color="secondary"
            startIcon={<UploadIcon />}
            onClick={() => setCurrentView('upload')}
            sx={{ borderRadius: 2 }}
          >
            Upload Documents
          </Button>
        </Box>
      )}

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Message Input */}
      <Paper sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message here..."
            disabled={isLoading}
            variant="outlined"
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 2,
              },
            }}
          />
          <IconButton
            color="primary"
            onClick={handleSendMessage}
            disabled={!message.trim() || isLoading}
            sx={{
              bgcolor: 'primary.main',
              color: 'white',
              '&:hover': {
                bgcolor: 'primary.dark',
              },
              '&.Mui-disabled': {
                bgcolor: 'grey.300',
                color: 'grey.500',
              },
            }}
          >
            {isLoading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
          </IconButton>
        </Box>
      </Paper>

      
    </Box>
  );
};

export default ChatInterface;
