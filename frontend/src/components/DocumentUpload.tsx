// src/components/DocumentUpload.tsx
import React, { useState, useEffect } from 'react';
import {
  Box, Paper, Typography, Button, List, ListItem,
  ListItemIcon, ListItemText, IconButton, CircularProgress,
  Alert, Card, CardContent, Chip, Grid
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Delete as DeleteIcon,
  Description as FileIcon,
  CheckCircle as CheckIcon
} from '@mui/icons-material';
import { useAppStore } from '../store/appStore';
import { uploadDocument, listDocuments, deleteDocument, Document } from '../services/api';
import axios from 'axios';

const requiredDocuments = [
  { name: 'PAN', description: 'PAN Card (Front)', required: true },
  { name: 'Aadhaar', description: 'Aadhaar Card (Front + Back)', required: true },
  { name: 'CompanyID', description: 'Company ID Card/Letter', required: true },
  { name: 'Payslip', description: 'Latest Payslip (3 months)', required: true },
];

const DocumentUpload: React.FC = () => {
  const { sessionId } = useAppStore();
  const [currentApplicationId, setCurrentApplicationId] = useState<string | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    const fetchSessionData = async () => {
      try {
        const response = await axios.get(`/api/session/${sessionId}`);
        if (response.data?.current_application_id) {
          console.log('Current application ID from backend:', response.data.current_application_id);
          setCurrentApplicationId(response.data.current_application_id);
        } else {
          console.log('No application ID found in session');
          setError('No active application found. Please complete your application first.');
        }
      } catch (err) {
        console.error('Failed to fetch session data:', err);
        setError('Failed to verify application status. Please try again.');
      }
    };
    
    if (sessionId) {
      fetchSessionData();
    } else {
      setError('Session not found. Please return to chat.');
    }
  }, [sessionId]);

  useEffect(() => {
    const loadDocuments = async () => {
      try {
        setLoading(true);
        if (!currentApplicationId) {
          setError('Please complete your application first');
          return;
        }
        
        const docs = await listDocuments(currentApplicationId);
        setDocuments(docs);
      } catch (err) {
        setError('Failed to load documents');
      } finally {
        setLoading(false);
      }
    };
    if (currentApplicationId) {
      loadDocuments();
    }
  }, [currentApplicationId]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.length) {
      setError('Please select a file to upload');
      return;
    }
    
    if (!currentApplicationId) {
      setError('Please complete your application first');
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      
      const file = e.target.files[0];
      await uploadDocument(file, sessionId, currentApplicationId);
      
      // Refresh documents list
      const updatedDocs = await listDocuments(currentApplicationId);
      setDocuments(updatedDocs);
      setSuccess('Document uploaded successfully!');
    } catch (err) {
      setError('Failed to upload document: ' + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (file_id: string) => {
    if (!currentApplicationId) return;
    try {
      setLoading(true);
      await deleteDocument(file_id, currentApplicationId);
      setSuccess('Document deleted successfully');
      const updatedDocs = await listDocuments(currentApplicationId);
      setDocuments(updatedDocs);
    } catch (err) {
      setError('Failed to delete document');
    } finally {
      setLoading(false);
    }
  };

  const isDocumentUploaded = (docName: string) => {
    return documents.some(doc => doc.name.includes(docName));
  };

  if (!currentApplicationId) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="h6" color="error">
          Application ID Required
        </Typography>
        <Typography>
          Please return to the chat and provide your application ID
        </Typography>
      </Paper>
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h5" gutterBottom>
        Document Upload
      </Typography>
      <Typography color="text.secondary" gutterBottom>
        Application ID: {currentApplicationId}
      </Typography>

      {error && <Alert severity="error">{error}</Alert>}
      {success && <Alert severity="success">{success}</Alert>}

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <UploadIcon fontSize="large" color="primary" />
              <Typography variant="h6" gutterBottom>
                Upload Documents
              </Typography>
              <Button
                variant="contained"
                component="label"
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} /> : null}
              >
                {loading ? 'Uploading...' : 'Select File'}
                <input type="file" hidden onChange={handleUpload} />
              </Button>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 2 }}>
                Supported formats: PDF, JPG, JPEG, PNG
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Required Documents
            </Typography>
            <List>
              {requiredDocuments.map((doc) => (
                <ListItem key={doc.name}>
                  <ListItemIcon>
                    {isDocumentUploaded(doc.name) ? 
                      <CheckIcon color="success" /> : 
                      <FileIcon color={doc.required ? 'error' : 'disabled'} />}
                  </ListItemIcon>
                  <ListItemText
                    primary={doc.name}
                    secondary={doc.description}
                  />
                  <Chip
                    label={doc.required ? 'Required' : 'Optional'}
                    size="small"
                    color={doc.required ? 'primary' : 'default'}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Paper elevation={2} sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Uploaded Documents
            </Typography>
            {documents.length > 0 ? (
              <List>
                {documents.map((doc) => (
                  <ListItem
                    key={doc.file_id}
                    secondaryAction={
                      <IconButton 
                        edge="end" 
                        onClick={() => handleDelete(doc.file_id)}
                        disabled={loading}
                      >
                        <DeleteIcon />
                      </IconButton>
                    }
                  >
                    <ListItemIcon>
                      <FileIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary={doc.name}
                      secondary={
                        <>
                          <div>Type: {doc.type}</div>
                          <div>Size: {(doc.size / 1024).toFixed(1)} KB</div>
                          <div>Uploaded: {new Date(doc.last_modified).toLocaleString()}</div>
                        </>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography color="text.secondary" sx={{ textAlign: 'center' }}>
                No documents uploaded yet
              </Typography>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default DocumentUpload;