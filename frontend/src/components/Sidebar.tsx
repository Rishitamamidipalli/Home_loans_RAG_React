import React from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  Box,
  Divider,
} from '@mui/material';
import {
  Chat as ChatIcon,
  Description as FormIcon,
  CloudUpload as UploadIcon,
  Assessment as ResultsIcon,
  Home as HomeIcon,
} from '@mui/icons-material';
import { useAppStore } from '../store/appStore';

const DRAWER_WIDTH = 240;

const Sidebar: React.FC = () => {
  const { currentView, setCurrentView } = useAppStore();

  const menuItems = [
    { id: 'chat', label: 'Chat Assistant', icon: <ChatIcon />, view: 'chat' as const },
    { id: 'application', label: 'Loan Application', icon: <FormIcon />, view: 'application' as const },
    { id: 'upload', label: 'Document Upload', icon: <UploadIcon />, view: 'upload' as const },
    { id: 'results', label: 'Results & Analysis', icon: <ResultsIcon />, view: 'results' as const },
  ];

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: DRAWER_WIDTH,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: DRAWER_WIDTH,
          boxSizing: 'border-box',
          backgroundColor: '#f0f2f6',
          borderRight: '1px solid #e0e0e0',
        },
      }}
    >
      <Box sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <HomeIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h6" component="div" sx={{ fontWeight: 'bold' }}>
            Home Loan Assistant
          </Typography>
        </Box>
        <Divider />
      </Box>
      
      <List sx={{ px: 1 }}>
        {menuItems.map((item) => (
          <ListItem key={item.id} disablePadding sx={{ mb: 0.5 }}>
            <ListItemButton
              selected={currentView === item.view}
              onClick={() => setCurrentView(item.view)}
              sx={{
                borderRadius: 1,
                '&.Mui-selected': {
                  backgroundColor: 'primary.main',
                  color: 'white',
                  '&:hover': {
                    backgroundColor: 'primary.dark',
                  },
                  '& .MuiListItemIcon-root': {
                    color: 'white',
                  },
                },
                '&:hover': {
                  backgroundColor: 'rgba(255, 75, 75, 0.1)',
                },
              }}
            >
              <ListItemIcon
                sx={{
                  minWidth: 40,
                  color: currentView === item.view ? 'white' : 'text.secondary',
                }}
              >
                {item.icon}
              </ListItemIcon>
              <ListItemText 
                primary={item.label}
                primaryTypographyProps={{
                  fontSize: '0.9rem',
                  fontWeight: currentView === item.view ? 'bold' : 'normal',
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      
      <Box sx={{ mt: 'auto', p: 2 }}>
        <Divider sx={{ mb: 2 }} />
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textAlign: 'center' }}>
          Powered by AI
        </Typography>
      </Box>
    </Drawer>
  );
};

export default Sidebar;
