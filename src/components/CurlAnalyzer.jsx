import React, { useState } from 'react';
import { 
  Box, 
  TextField, 
  Button, 
  Paper, 
  Tabs, 
  Tab, 
  CircularProgress,
  Alert
} from '@mui/material';
import { parseCurlCommand } from '../services/curlParser';
import { analyzeRequest } from '../services/requestAnalyzer';
import { analyzeResponse } from '../services/responseAnalyzer';
import ReactJson from 'react-json-view';

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

export default function CurlAnalyzer() {
  const [curlCommand, setCurlCommand] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [analysisData, setAnalysisData] = useState(null);
  const [tabValue, setTabValue] = useState(0);

  const handleAnalyze = async () => {
    try {
      setLoading(true);
      setError('');

      // Parse curl command
      const parsedRequest = parseCurlCommand(curlCommand);
      
      // Analyze request
      const requestInfo = analyzeRequest(parsedRequest);
      
      // Execute request and analyze response
      const responseInfo = await analyzeResponse(parsedRequest);

      setAnalysisData({
        request: requestInfo,
        response: responseInfo
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <TextField
          fullWidth
          multiline
          rows={4}
          value={curlCommand}
          onChange={(e) => setCurlCommand(e.target.value)}
          placeholder="Enter curl command here..."
          variant="outlined"
          sx={{ mb: 2 }}
        />
        <Button
          variant="contained"
          onClick={handleAnalyze}
          disabled={loading || !curlCommand}
          fullWidth
        >
          {loading ? <CircularProgress size={24} /> : 'Analyze'}
        </Button>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {analysisData && (
        <Paper elevation={3}>
          <Tabs
            value={tabValue}
            onChange={(e, newValue) => setTabValue(newValue)}
            centered
          >
            <Tab label="Request Details" />
            <Tab label="Response Details" />
            <Tab label="Raw Data" />
          </Tabs>

          <TabPanel value={tabValue} index={0}>
            <ReactJson src={analysisData.request} theme="rjv-default" />
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <ReactJson src={analysisData.response} theme="rjv-default" />
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <Box component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
              {analysisData.response.raw}
            </Box>
          </TabPanel>
        </Paper>
      )}
    </Box>
  );
}
