import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Alert,
  LinearProgress,
  Card,
  CardContent,
  Chip,
  Grid,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Delete as DeleteIcon,
  Description as FileIcon,
  CheckCircle as CheckIcon,
} from '@mui/icons-material';
import { useAppStore } from '../store/appStore';
import { uploadDocument, listDocuments, deleteDocument } from '../services/api';

const DocumentUpload: React.FC = () => {
  const { sessionId, uploadedDocuments, setUploadedDocuments } = useAppStore();
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [token] = useState(`TOKEN_${sessionId}`); // Generate token based on session

  const requiredDocuments = [
    { name: 'Pay Stubs', description: 'Recent pay stubs (last 2-3 months)', required: true },
    { name: 'Tax Returns', description: 'Last 2 years of tax returns', required: true },
    { name: 'Bank Statements', description: 'Last 2-3 months of bank statements', required: true },
    { name: 'Employment Letter', description: 'Letter of employment verification', required: true },
    { name: 'Credit Report', description: 'Recent credit report', required: false },
    { name: 'Property Documents', description: 'Purchase agreement or property details', required: false },
  ];

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      const docs = await listDocuments(token);
      setUploadedDocuments(docs);
    } catch (err) {
      console.error('Failed to load documents:', err);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    setError(null);
    setSuccess(null);

    try {
      for (const file of Array.from(files)) {
        await uploadDocument(file, sessionId, token);
      }
      
      setSuccess(`Successfully uploaded ${files.length} file(s)`);
      await loadDocuments();
      
      // Clear the input
      event.target.value = '';
      
    } catch (err) {
      setError('Failed to upload documents. Please try again.');
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDocument = async (filename: string) => {
    try {
      await deleteDocument(token, filename);
      setSuccess(`Deleted ${filename}`);
      await loadDocuments();
    } catch (err) {
      setError(`Failed to delete ${filename}`);
      console.error('Delete error:', err);
    }
  };

  const getDocumentStatus = (docType: string) => {
    const hasDoc = uploadedDocuments.some(doc => 
      doc.toLowerCase().includes(docType.toLowerCase().replace(' ', ''))
    );
    return hasDoc;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Box sx={{ maxWidth: 1000, mx: 'auto' }}>
      {/* Header */}
      <Paper sx={{ p: 3, mb: 3, backgroundColor: 'primary.main', color: 'white' }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 'bold', mb: 1 }}>
          📁 Document Upload
        </Typography>
        <Typography variant="body1" sx={{ opacity: 0.9 }}>
          Upload required documents for your loan application
        </Typography>
      </Paper>

      <Grid container spacing={3}>
        {/* Upload Section */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, color: 'primary.main' }}>
                Upload Documents
              </Typography>
              
              <Box
                sx={{
                  border: '2px dashed',
                  borderColor: 'primary.light',
                  borderRadius: 2,
                  p: 4,
                  textAlign: 'center',
                  backgroundColor: 'primary.light',
                  opacity: 0.1,
                  mb: 2,
                }}
              >
                <UploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                <Typography variant="body1" sx={{ mb: 2 }}>
                  Drag and drop files here or click to browse
                </Typography>
                <input
                  accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                  style={{ display: 'none' }}
                  id="file-upload"
                  multiple
                  type="file"
                  onChange={handleFileUpload}
                  disabled={uploading}
                />
                <label htmlFor="file-upload">
                  <Button
                    variant="contained"
                    component="span"
                    startIcon={<UploadIcon />}
                    disabled={uploading}
                  >
                    Choose Files
                  </Button>
                </label>
              </Box>

              {uploading && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    Uploading documents...
                  </Typography>
                  <LinearProgress />
                </Box>
              )}

              <Typography variant="caption" color="text.secondary">
                Supported formats: PDF, DOC, DOCX, JPG, JPEG, PNG (Max 10MB per file)
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Required Documents Checklist */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, color: 'primary.main' }}>
                Document Checklist
              </Typography>
              
              <List>
                {requiredDocuments.map((doc, index) => {
                  const hasDocument = getDocumentStatus(doc.name);
                  return (
                    <ListItem key={index} sx={{ px: 0 }}>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            {hasDocument ? (
                              <CheckIcon sx={{ color: 'success.main', fontSize: 20 }} />
                            ) : (
                              <FileIcon sx={{ color: 'text.secondary', fontSize: 20 }} />
                            )}
                            <Typography
                              variant="body2"
                              sx={{
                                textDecoration: hasDocument ? 'line-through' : 'none',
                                color: hasDocument ? 'success.main' : 'text.primary',
                              }}
                            >
                              {doc.name}
                            </Typography>
                            {doc.required && (
                              <Chip
                                label="Required"
                                size="small"
                                color="error"
                                variant="outlined"
                              />
                            )}
                          </Box>
                        }
                        secondary={doc.description}
                      />
                    </ListItem>
                  );
                })}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Uploaded Documents */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, color: 'primary.main' }}>
                Uploaded Documents ({uploadedDocuments.length})
              </Typography>
              
              {uploadedDocuments.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  No documents uploaded yet
                </Typography>
              ) : (
                <List>
                  {uploadedDocuments.map((filename, index) => (
                    <ListItem key={index} divider>
                      <FileIcon sx={{ mr: 2, color: 'primary.main' }} />
                      <ListItemText
                        primary={filename}
                        secondary={`Uploaded on ${new Date().toLocaleDateString()}`}
                      />
                      <ListItemSecondaryAction>
                        <IconButton
                          edge="end"
                          aria-label="delete"
                          onClick={() => handleDeleteDocument(filename)}
                          color="error"
                        >
                          <DeleteIcon />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Alerts */}
      {error && (
        <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mt: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}
    </Box>
  );
};

export default DocumentUpload;
