import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  Button,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckIcon,
  Cancel as CancelIcon,
  Info as InfoIcon,
  TrendingUp as TrendingUpIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';
import { useAppStore } from '../store/appStore';

const Results: React.FC = () => {
  const { applications, sessionId, setCurrentView } = useAppStore();
  const [analysisResults, setAnalysisResults] = useState<any>(null);

  // Mock analysis results - in real app, this would come from the orchestrator
  const mockResults = {
    eligibility: {
      status: 'approved',
      confidence: 85,
      reasons: [
        'Strong credit score (750+)',
        'Stable employment history',
        'Adequate down payment',
        'Good debt-to-income ratio'
      ]
    },
    recommendations: [
      {
        lender: 'Bank of America',
        product: '30-Year Fixed Rate Mortgage',
        rate: 6.75,
        monthlyPayment: 2847,
        totalCost: 1024920,
        pros: ['Competitive rate', 'No PMI with 20% down', 'Local branch support'],
        cons: ['Higher closing costs', 'Strict documentation requirements']
      },
      {
        lender: 'Wells Fargo',
        product: '30-Year Fixed Rate Mortgage',
        rate: 6.85,
        monthlyPayment: 2891,
        totalCost: 1040760,
        pros: ['Fast approval process', 'Online application', 'First-time buyer programs'],
        cons: ['Slightly higher rate', 'Limited customer service hours']
      },
      {
        lender: 'Quicken Loans',
        product: '30-Year Fixed Rate Mortgage',
        rate: 6.65,
        monthlyPayment: 2814,
        totalCost: 1013040,
        pros: ['Best rate offered', 'Fully digital process', '24/7 support'],
        cons: ['No local branches', 'Higher origination fees']
      }
    ],
    riskFactors: [
      'Market volatility may affect rates',
      'Property appraisal pending',
      'Employment verification required'
    ],
    nextSteps: [
      'Submit additional documentation',
      'Schedule property appraisal',
      'Review and sign loan documents',
      'Coordinate closing date'
    ]
  };

  useEffect(() => {
    // Simulate loading analysis results
    setTimeout(() => {
      setAnalysisResults(mockResults);
    }, 1000);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'approved':
        return 'success';
      case 'pending':
        return 'warning';
      case 'denied':
        return 'error';
      default:
        return 'default';
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  if (!analysisResults) {
    return (
      <Box sx={{ maxWidth: 1000, mx: 'auto', textAlign: 'center', mt: 4 }}>
        <Typography variant="h6">Analyzing your application...</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          This may take a few moments
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
      {/* Header */}
      <Paper sx={{ p: 3, mb: 3, backgroundColor: 'primary.main', color: 'white' }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 'bold', mb: 1 }}>
          📊 Loan Analysis Results
        </Typography>
        <Typography variant="body1" sx={{ opacity: 0.9 }}>
          Your personalized loan recommendations and analysis
        </Typography>
      </Paper>

      <Grid container spacing={3}>
        {/* Eligibility Status */}
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <AssessmentIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Eligibility Status</Typography>
              </Box>
              
              <Box sx={{ textAlign: 'center', mb: 2 }}>
                <Chip
                  icon={analysisResults.eligibility.status === 'approved' ? <CheckIcon /> : <CancelIcon />}
                  label={analysisResults.eligibility.status.toUpperCase()}
                  color={getStatusColor(analysisResults.eligibility.status) as any}
                  size="medium"
                  sx={{ mb: 2 }}
                />
                <Typography variant="h4" color="primary.main">
                  {analysisResults.eligibility.confidence}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Confidence Score
                </Typography>
              </Box>

              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Key Factors:
              </Typography>
              <List dense>
                {analysisResults.eligibility.reasons.map((reason: string, index: number) => (
                  <ListItem key={index} sx={{ py: 0.5 }}>
                    <CheckIcon sx={{ fontSize: 16, mr: 1, color: 'success.main' }} />
                    <ListItemText
                      primary={reason}
                      primaryTypographyProps={{ variant: 'body2' }}
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Risk Factors */}
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <InfoIcon sx={{ mr: 1, color: 'warning.main' }} />
                <Typography variant="h6">Risk Factors</Typography>
              </Box>
              
              <List>
                {analysisResults.riskFactors.map((risk: string, index: number) => (
                  <ListItem key={index} sx={{ py: 1 }}>
                    <ListItemText
                      primary={risk}
                      primaryTypographyProps={{ variant: 'body2' }}
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Next Steps */}
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <TrendingUpIcon sx={{ mr: 1, color: 'info.main' }} />
                <Typography variant="h6">Next Steps</Typography>
              </Box>
              
              <List>
                {analysisResults.nextSteps.map((step: string, index: number) => (
                  <ListItem key={index} sx={{ py: 1 }}>
                    <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                      {index + 1}. {step}
                    </Typography>
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Loan Recommendations */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 3, color: 'primary.main' }}>
                💰 Recommended Loan Products
              </Typography>
              
              {analysisResults.recommendations.map((loan: any, index: number) => (
                <Accordion key={index} sx={{ mb: 1 }}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                      <Box sx={{ flexGrow: 1 }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                          {loan.lender} - {loan.product}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {loan.rate}% APR • {formatCurrency(loan.monthlyPayment)}/month
                        </Typography>
                      </Box>
                      {index === 0 && (
                        <Chip label="Best Rate" color="success" size="small" />
                      )}
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Grid container spacing={2}>
                      <Grid item xs={12} md={6}>
                        <Typography variant="subtitle2" color="success.main" sx={{ mb: 1 }}>
                          Advantages:
                        </Typography>
                        <List dense>
                          {loan.pros.map((pro: string, proIndex: number) => (
                            <ListItem key={proIndex} sx={{ py: 0 }}>
                              <CheckIcon sx={{ fontSize: 16, mr: 1, color: 'success.main' }} />
                              <ListItemText
                                primary={pro}
                                primaryTypographyProps={{ variant: 'body2' }}
                              />
                            </ListItem>
                          ))}
                        </List>
                      </Grid>
                      <Grid item xs={12} md={6}>
                        <Typography variant="subtitle2" color="error.main" sx={{ mb: 1 }}>
                          Considerations:
                        </Typography>
                        <List dense>
                          {loan.cons.map((con: string, conIndex: number) => (
                            <ListItem key={conIndex} sx={{ py: 0 }}>
                              <InfoIcon sx={{ fontSize: 16, mr: 1, color: 'warning.main' }} />
                              <ListItemText
                                primary={con}
                                primaryTypographyProps={{ variant: 'body2' }}
                              />
                            </ListItem>
                          ))}
                        </List>
                      </Grid>
                      <Grid item xs={12}>
                        <Divider sx={{ my: 1 }} />
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap' }}>
                          <Typography variant="body2">
                            <strong>Monthly Payment:</strong> {formatCurrency(loan.monthlyPayment)}
                          </Typography>
                          <Typography variant="body2">
                            <strong>Total Cost:</strong> {formatCurrency(loan.totalCost)}
                          </Typography>
                          <Typography variant="body2">
                            <strong>Interest Rate:</strong> {loan.rate}%
                          </Typography>
                        </Box>
                      </Grid>
                    </Grid>
                  </AccordionDetails>
                </Accordion>
              ))}
            </CardContent>
          </Card>
        </Grid>

        {/* Action Buttons */}
        <Grid item xs={12}>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
            <Button
              variant="contained"
              size="large"
              onClick={() => setCurrentView('chat')}
            >
              Ask Questions
            </Button>
            <Button
              variant="outlined"
              size="large"
              onClick={() => setCurrentView('application')}
            >
              Update Application
            </Button>
            <Button
              variant="outlined"
              size="large"
              onClick={() => setCurrentView('upload')}
            >
              Upload More Documents
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Results;
