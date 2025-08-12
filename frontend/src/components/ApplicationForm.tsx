import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  MenuItem,
  Alert,
  Stepper,
  Step,
  StepLabel,
  Card,
  CardContent,
  CircularProgress,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { useAppStore } from '../store/appStore';
import { submitApplication, ApplicationFormData } from '../services/api';

const steps = [
  'Personal Details',
  'Employment Details',
  'Property Details',
];

const ApplicationForm: React.FC = () => {
  const { sessionId, setCurrentView, isLoading, setIsLoading } = useAppStore();
  const [activeStep, setActiveStep] = useState(0);
  const [formData, setFormData] = useState<Partial<ApplicationFormData>>({
    // Personal
    full_name: '',
    gender: '',
    date_of_birth: '',
    phone: '',
    email: '',
    pan_number: '',
    aadhar_number: '',
    address: '',
    // Employment
    employment_status: '',
    company_name: '',
    monthly_income: 0,
    existing_loan_amount: 0,
    // Property
    property_location_city: '',
    property_location_area: '',
    property_type: '',
    property_size_sqft: 0,
    property_age_years: 0,
    property_condition: '',
    property_value: 0,
    // Loan
    purpose_of_loan: '',
    required_loan_amount: 0,
   
  });
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleInputChange = (field: keyof ApplicationFormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleNext = () => {
    setActiveStep(prev => prev + 1);
  };

  const handleBack = () => {
    setActiveStep(prev => prev - 1);
  };

  const handleSubmit = async () => {
    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // Map monthly_income to annual_income for backend compatibility
      const annual_income = (Number((formData as any).monthly_income) || 0) * 12;
      const payload: Partial<ApplicationFormData> = {
        ...formData,
        annual_income,
      };

      const response = await submitApplication(payload as ApplicationFormData, sessionId);

      if (response.success) {
        setSuccess(`Application submitted successfully! Application ID: ${response.application_id}`);
        setTimeout(() => {
          setCurrentView('chat'); // Redirect to chat to show token and upload prompt
        }, 2000);
      } else {
        setError(response.message);
      }
    } catch (err) {
      setError('Failed to submit application. Please try again.');
      console.error('Application submission error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const renderPersonalInfo = () => (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <TextField
          fullWidth
          label="Full Name"
          value={(formData as any).full_name || ''}
          onChange={(e) => handleInputChange('full_name' as keyof ApplicationFormData, e.target.value)}
          required
        />
      </Grid>
      <Grid item xs={12} sm={6}>
        <TextField
          fullWidth
          select
          label="Gender"
          value={(formData as any).gender || ''}
          onChange={(e) => handleInputChange('gender' as keyof ApplicationFormData, e.target.value)}
          required
        >
          <MenuItem value="Male">Male</MenuItem>
          <MenuItem value="Female">Female</MenuItem>
          <MenuItem value="Other">Other</MenuItem>
        </TextField>
      </Grid>
      <Grid item xs={12} sm={6}>
        <LocalizationProvider dateAdapter={AdapterDateFns}>
          <DatePicker
            label="Date of Birth"
            value={(formData as any).date_of_birth ? new Date((formData as any).date_of_birth as string) : null}
            onChange={(date) => handleInputChange('date_of_birth' as keyof ApplicationFormData, date ? date.toISOString().split('T')[0] : '')}
            slotProps={{ textField: { fullWidth: true, required: true } }}
          />
        </LocalizationProvider>
      </Grid>
      <Grid item xs={12} sm={6}>
        <TextField
          fullWidth
          label="Phone Number"
          value={(formData as any).phone || ''}
          onChange={(e) => handleInputChange('phone' as keyof ApplicationFormData, e.target.value)}
          required
        />
      </Grid>
      <Grid item xs={12} sm={6}>
        <TextField
          fullWidth
          label="Email"
          type="email"
          value={(formData as any).email || ''}
          onChange={(e) => handleInputChange('email' as keyof ApplicationFormData, e.target.value)}
        />
      </Grid>
      <Grid item xs={12} sm={6}>
        <TextField
          fullWidth
          label="PAN Number"
          value={(formData as any).pan_number || ''}
          onChange={(e) => handleInputChange('pan_number' as keyof ApplicationFormData, e.target.value)}
          required
        />
      </Grid>
      <Grid item xs={12} sm={6}>
        <TextField
          fullWidth
          label="Aadhar Number"
          value={(formData as any).aadhar_number || ''}
          onChange={(e) => handleInputChange('aadhar_number' as keyof ApplicationFormData, e.target.value)}
          required
        />
      </Grid>
      <Grid item xs={12}>
        <TextField
          fullWidth
          multiline
          minRows={2}
          label="Address"
          value={(formData as any).address || ''}
          onChange={(e) => handleInputChange('address' as keyof ApplicationFormData, e.target.value)}
          required
        />
      </Grid>
      <Grid item xs={12} sm={6}>
        <TextField
          fullWidth
          select
          label="Purpose of Loan"
          value={(formData as any).purpose_of_loan || ''}
          onChange={(e) => handleInputChange('purpose_of_loan' as keyof ApplicationFormData, e.target.value)}
          required
        >
          <MenuItem value="Purchasing new house">Purchasing new house</MenuItem>
          <MenuItem value="Renovating current house">Renovating current house</MenuItem>
          <MenuItem value="Constructing a house on current land">Constructing a house on current land</MenuItem>
        </TextField>
      </Grid>
      <Grid item xs={12} sm={6}>
        <TextField
          fullWidth
          type="number"
          label="Loan Amount Required(₹)"
          value={Number((formData as any).required_loan_amount) || 0}
          onChange={(e) => handleInputChange('required_loan_amount' as keyof ApplicationFormData, parseFloat(e.target.value) || 1000)}
          required
        />
      </Grid>
    </Grid>
  );

  const renderEmploymentInfo = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} sm={6}>
        <TextField
          fullWidth
          select
          label="Employment Status"
          value={(formData as any).employment_status || ''}
          onChange={(e) => handleInputChange('employment_status' as keyof ApplicationFormData, e.target.value)}
          required
        >
          <MenuItem value="Salaried">Salaried</MenuItem>
          <MenuItem value="Self-employed">Self-employed</MenuItem>
          <MenuItem value="Business Owner">Business Owner</MenuItem>
          <MenuItem value="Unemployed">Unemployed</MenuItem>
          <MenuItem value="Retired">Retired</MenuItem>
        </TextField>
      </Grid>
      <Grid item xs={12} sm={6}>
        <TextField
          fullWidth
          label="Company Name"
          value={(formData as any).company_name || ''}
          onChange={(e) => handleInputChange('company_name' as keyof ApplicationFormData, e.target.value)}
        />
      </Grid>
      <Grid item xs={12} sm={6}>
        <TextField
          fullWidth
          type="number"
          label="Monthly Income (₹)"
          value={Number((formData as any).monthly_income) || 0}
          onChange={(e) => handleInputChange('monthly_income' as keyof ApplicationFormData, parseFloat(e.target.value) || 0)}
          required
        />
      </Grid>
      <Grid item xs={12} sm={6}>
        <TextField
          fullWidth
          type="number"
          label="Existing Loan Amount (₹)"
          value={Number((formData as any).existing_loan_amount) || 0}
          onChange={(e) => handleInputChange('existing_loan_amount' as keyof ApplicationFormData, parseFloat(e.target.value) || 0)}
        />
      </Grid>
    </Grid>
  );

  // Financial step removed as per new requirements

  const renderPropertyInfo = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} sm={6}>
        <TextField
          fullWidth
          select
          label="Property Type"
          value={(formData as any).property_type || ''}
          onChange={(e) => handleInputChange('property_type' as keyof ApplicationFormData, e.target.value)}
          required
        >
          <MenuItem value="Apartment">Apartment</MenuItem>
          <MenuItem value="Independent House">Independent House</MenuItem>
          <MenuItem value="Villa">Villa</MenuItem>
          <MenuItem value="Plot">Plot</MenuItem>
        </TextField>
      </Grid>
      <Grid item xs={12} sm={6}>
        <TextField
          fullWidth
          type="number"
          label="Property Value (₹)"
          value={Number((formData as any).property_value) || 0}
          onChange={(e) => handleInputChange('property_value' as keyof ApplicationFormData, parseFloat(e.target.value) || 0)}
          required
        />
      </Grid>
      <Grid item xs={12} sm={6}>
        <TextField
          fullWidth
          label="Property City"
          value={(formData as any).property_location_city || ''}
          onChange={(e) => handleInputChange('property_location_city' as keyof ApplicationFormData, e.target.value)}
          required
        />
      </Grid>
      <Grid item xs={12} sm={6}>
        <TextField
          fullWidth
          label="Property Area / Locality"
          value={(formData as any).property_location_area || ''}
          onChange={(e) => handleInputChange('property_location_area' as keyof ApplicationFormData, e.target.value)}
          required
        />
      </Grid>
      <Grid item xs={12} sm={4}>
        <TextField
          fullWidth
          type="number"
          label="Size (sqft)"
          value={Number((formData as any).property_size_sqft) || 0}
          onChange={(e) => handleInputChange('property_size_sqft' as keyof ApplicationFormData, parseFloat(e.target.value) || 0)}
        />
      </Grid>
      <Grid item xs={12} sm={4}>
        <TextField
          fullWidth
          type="number"
          label="Age (years)"
          value={Number((formData as any).property_age_years) || 0}
          onChange={(e) => handleInputChange('property_age_years' as keyof ApplicationFormData, parseFloat(e.target.value) || 0)}
        />
      </Grid>
      <Grid item xs={12} sm={4}>
        <TextField
          fullWidth
          select
          label="Condition"
          value={(formData as any).property_condition || ''}
          onChange={(e) => handleInputChange('property_condition' as keyof ApplicationFormData, e.target.value)}
        >
          <MenuItem value="Excellent">Excellent</MenuItem>
          <MenuItem value="Good">Good</MenuItem>
          <MenuItem value="Average">Average</MenuItem>
          <MenuItem value="Poor">Poor</MenuItem>
        </TextField>
      </Grid>
    </Grid>
  );

  // Loan details section removed; relevant fields moved into Personal Details

  const getStepContent = (step: number) => {
    switch (step) {
      case 0:
        return renderPersonalInfo();
      case 1:
        return renderEmploymentInfo();
      case 2:
        return renderPropertyInfo();
      default:
        return 'Unknown step';
    }
  };

  return (
    <Box sx={{ maxWidth: 1000, mx: 'auto' }}>
      {/* Header */}
      <Paper sx={{ p: 3, mb: 3, backgroundColor: 'primary.main', color: 'white' }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 'bold', mb: 1 }}>
          📋 Home Loan Application
        </Typography>
        <Typography variant="body1" sx={{ opacity: 0.9 }}>
          Please fill out all required information to process your loan application
        </Typography>
      </Paper>

      {/* Stepper */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Stepper activeStep={activeStep} alternativeLabel>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>
      </Paper>

      {/* Form Content */}
      <Card>
        <CardContent sx={{ p: 4 }}>
          <Typography variant="h6" sx={{ mb: 3, color: 'primary.main' }}>
            {steps[activeStep]}
          </Typography>
          
          {getStepContent(activeStep)}
          
          {/* Navigation Buttons */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
            <Button
              disabled={activeStep === 0}
              onClick={handleBack}
              variant="outlined"
            >
              Back
            </Button>
            
            <Box sx={{ display: 'flex', gap: 2 }}>
              {activeStep === steps.length - 1 ? (
                <Button
                  variant="contained"
                  onClick={handleSubmit}
                  disabled={isLoading}
                  startIcon={isLoading ? <CircularProgress size={20} /> : null}
                >
                  {isLoading ? 'Submitting...' : 'Submit Application'}
                </Button>
              ) : (
                <Button variant="contained" onClick={handleNext}>
                  Next
                </Button>
              )}
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Alerts */}
      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mt: 2 }}>
          {success}
        </Alert>
      )}
    </Box>
  );
};

export default ApplicationForm;
