import React, { useState } from 'react';
import { Card, CardContent, Typography, Box, CircularProgress, Alert } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

interface SummaryData {
  total: string;
  max_daily: string;
  peak_date: string;
}

interface SummaryResponse {
  summary: SummaryData;
  error: string | null;
}

const SummaryBiot: React.FC<{ query: string; dataset: string }> = ({ query, dataset }) => {
  const [error, setError] = useState<string | null>(null);

  const { data, isLoading, isError } = useQuery<SummaryResponse>({
    queryKey: ['summary', query, dataset],
    queryFn: async () => {
      try {
        const response = await axios.post<SummaryResponse>('http://localhost:5000/summary', {
          query,
          dataset,
        });
        return response.data;
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
        throw err;
      }
    },
    enabled: !!query && !!dataset,
  });

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (isError || error) {
    return (
      <Alert severity="error">
        {error || 'Failed to fetch summary data'}
      </Alert>
    );
  }

  if (!data?.summary) {
    return (
      <Alert severity="warning">
        No summary data available
      </Alert>
    );
  }

  const { total, max_daily, peak_date } = data.summary;

  return (
    <Card sx={{ maxWidth: 600, margin: 'auto', mt: 2 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Summary Statistics
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          <Typography>
            <strong>Total:</strong> {total}
          </Typography>
          <Typography>
            <strong>Maximum Daily:</strong> {max_daily}
          </Typography>
          <Typography>
            <strong>Peak Date:</strong> {peak_date}
          </Typography>
        </Box>
        {data.error && (
          <Alert severity="warning" sx={{ mt: 2 }}>
            {data.error}
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};

export default SummaryBiot; 