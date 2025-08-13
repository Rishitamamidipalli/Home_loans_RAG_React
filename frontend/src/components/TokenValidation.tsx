import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Typography,
  Alert,
  Box,
  CircularProgress,
} from '@mui/material';
import { Security as SecurityIcon } from '@mui/icons-material';

interface TokenValidationProps {
  open: boolean;
  onClose: () => void;
  onValidToken: (token: string) => void;
  targetFeature: 'upload' | 'results';
}

const TokenValidation: React.FC<TokenValidationProps> = ({
  open,
  onClose,
  onValidToken,
  targetFeature,
}) => {
  const [token, setToken] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isValidating, setIsValidating] = useState(false);

  const handleValidateToken = async () => {
    if (!token.trim()) {
      setError('Please enter a token number');
      return;
    }

    setIsValidating(true);
    setError(null);

    try {
      // Call backend API to validate token
      const response = await fetch('http://localhost:8000/validate-token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token: token.trim() }),
      });

      const data = await response.json();

      if (response.ok && data.valid) {
        onValidToken(token.trim());
        setToken('');
        setError(null);
      } else {
        setError(data.message || 'Invalid token. Please check your token number and try again.');
      }
    } catch (err) {
      setError('Failed to validate token. Please try again.');
    } finally {
      setIsValidating(false);
    }
  };

  const handleClose = () => {
    setToken('');
    setError(null);
    onClose();
  };

  const getFeatureTitle = () => {
    return targetFeature === 'upload' ? 'Document Upload' : 'Results & Analysis';
  };

  const getFeatureDescription = () => {
    return targetFeature === 'upload' 
      ? 'upload your loan documents' 
      : 'view your application results and analysis';
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <SecurityIcon color="primary" />
          <Typography variant="h6">
            Access {getFeatureTitle()}
          </Typography>
        </Box>
      </DialogTitle>
      
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          To {getFeatureDescription()}, please enter the token number you received 
          when you submitted your loan application form.
        </Typography>

        <TextField
          autoFocus
          margin="dense"
          label="Token Number"
          type="text"
          fullWidth
          variant="outlined"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          placeholder="Enter your application token"
          error={!!error}
          disabled={isValidating}
          onKeyPress={(e) => {
            if (e.key === 'Enter') {
              handleValidateToken();
            }
          }}
        />

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}

        <Box sx={{ mt: 2, p: 2, backgroundColor: 'grey.50', borderRadius: 1 }}>
          <Typography variant="caption" color="text.secondary">
            <strong>Note:</strong> Your token was generated when you completed the loan application form. 
            If you don't have your token, please complete the application form first.
          </Typography>
        </Box>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 3 }}>
        <Button onClick={handleClose} disabled={isValidating}>
          Cancel
        </Button>
        <Button 
          onClick={handleValidateToken} 
          variant="contained" 
          disabled={isValidating || !token.trim()}
          startIcon={isValidating ? <CircularProgress size={16} /> : null}
        >
          {isValidating ? 'Validating...' : 'Validate Token'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default TokenValidation;
