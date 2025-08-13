import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  CircularProgress,
  Alert,
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

interface UploadedDocument {
  filename: string;
  document_type: string;
  s3_path: string;
}

const requiredDocuments = [
  { name: 'Pay Slips', description: 'Recent pay stubs (last 2-3 months)', required: true },
  { name: 'Aadhaar Card', description: 'Aadhaar card', required: true },
  { name: 'Company ID Proof', description: 'Company ID proof', required: true },
  { name: 'Pan Card', description: 'Pan card', required: false },
];

const DocumentUpload: React.FC = () => {
  const { sessionId, uploadToken } = useAppStore();
  const token = uploadToken || sessionId; // Use uploadToken if available, otherwise sessionId
  const [uploadedDocuments, setUploadedDocuments] = useState<UploadedDocument[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const loadDocuments = useCallback(async () => {
    if (!token) return;
    try {
      const docs = await listDocuments(token);
      setUploadedDocuments(docs.map((doc: any) => ({ filename: doc.filename, document_type: doc.document_type, s3_path: doc.s3_path })));
    } catch (err) {
      setError('Failed to load document list.');
      console.error('Failed to load documents:', err);
    }
  }, [token]);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0 || !token) return;

    setUploading(true);
    setError(null);
    setSuccess(null);

    try {
      for (const file of Array.from(files)) {
        await uploadDocument(file, token, file.name.split('.')[0]);
      }
      setSuccess(`Successfully uploaded ${files.length} file(s).`);
      await loadDocuments();
    } catch (err) {
      setError('Failed to upload documents. Please try again.');
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
      // Clear the input
      if (event.target) {
        event.target.value = '';
      }
    }
  };

  const handleDeleteDocument = async (filename: string) => {
    if (!token) return;
    try {
      await deleteDocument(filename, token);
      setSuccess(`Successfully deleted ${filename}.`);
      await loadDocuments(); // Refresh the list
    } catch (err) {
      setError(`Failed to delete ${filename}.`);
      console.error('Delete error:', err);
    }
  };

  const isDocumentUploaded = (docName: string) => {
    const formattedDocName = docName.replace(/\s+/g, '_').toLowerCase();
    return uploadedDocuments.some(doc => 
      doc.document_type.toLowerCase().includes(formattedDocName)
    );
  };

  if (!token) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="h6" color="error">
          Application Token Not Found
        </Typography>
        <Typography color="text.secondary">
          Please go back to the chat and provide your application token to proceed.
        </Typography>
      </Paper>
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h5" gutterBottom>
        Document Upload
      </Typography>
      {token && (
        <Typography color="text.secondary" gutterBottom>
          Application ID: {uploadToken ? `HL${uploadToken.split('_')[1]}` : token}
        </Typography>
      )}
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

      <Grid container spacing={3}>
        {/* Upload Area */}
        <Grid item xs={12} md={6}>
          <Card component={Paper} elevation={2} sx={{ height: '100%' }}>
            <CardContent sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', p: 3 }}>
              <UploadIcon color="primary" sx={{ fontSize: 60, mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Click to Upload
              </Typography>
              <Button
                variant="contained"
                component="label"
                disabled={uploading}
                startIcon={uploading ? <CircularProgress size={20} color="inherit" /> : null}
              >
                {uploading ? 'Uploading...' : 'Select Files'}
                <input type="file" hidden multiple onChange={handleFileUpload} />
              </Button>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 2 }}>
                Supported formats: PDF, JPG, JPEG, PNG (Max 10MB per file)
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Required Documents List */}
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>Required Documents</Typography>
            <List dense>
              {requiredDocuments.map((doc) => (
                <ListItem key={doc.name}>
                  <ListItemIcon>
                    {isDocumentUploaded(doc.name) ? (
                      <CheckIcon color="success" />
                    ) : (
                      <FileIcon color={doc.required ? 'error' : 'disabled'} />
                    )}
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

        {/* Uploaded Documents List */}
        <Grid item xs={12}>
          <Paper elevation={2} sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Uploaded Files</Typography>
            {uploadedDocuments.length > 0 ? (
              <List dense>
                {uploadedDocuments.map((doc) => (
                  <ListItem
                    key={doc.filename}
                    secondaryAction={
                      <IconButton edge="end" aria-label="delete" onClick={() => handleDeleteDocument(doc.filename)}>
                        <DeleteIcon />
                      </IconButton>
                    }
                  >
                    <ListItemIcon>
                      <FileIcon />
                    </ListItemIcon>
                    <ListItemText primary={doc.filename} secondary={`Type: ${doc.document_type}`} />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography color="text.secondary" sx={{ mt: 2, textAlign: 'center' }}>
                No documents uploaded yet.
              </Typography>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default DocumentUpload;