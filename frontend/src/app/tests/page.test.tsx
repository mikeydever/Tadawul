import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import Home from '../page'; // Adjust path as necessary

// Mock the fetch function
global.fetch = jest.fn();

// Mock the shadcn/ui components used in the page if they cause issues or need specific checks
// jest.mock('@/components/ui/card', () => ({
//   Card: ({ children, ...props }) => <div {...props}>{children}</div>,
//   CardHeader: ({ children, ...props }) => <div {...props}>{children}</div>,
//   CardTitle: ({ children, ...props }) => <h2 {...props}>{children}</h2>,
//   CardDescription: ({ children, ...props }) => <p {...props}>{children}</p>,
//   CardContent: ({ children, ...props }) => <div {...props}>{children}</div>,
// }));
// jest.mock('@/components/ui/table', () => ({
//   Table: ({ children, ...props }) => <table {...props}>{children}</table>,
//   TableHeader: ({ children, ...props }) => <thead {...props}>{children}</thead>,
//   TableBody: ({ children, ...props }) => <tbody {...props}>{children}</tbody>,
//   TableRow: ({ children, ...props }) => <tr {...props}>{children}</tr>,
//   TableHead: ({ children, ...props }) => <th {...props}>{children}</th>,
//   TableCell: ({ children, ...props }) => <td {...props}>{children}</td>,
//   TableCaption: ({ children, ...props }) => <caption {...props}>{children}</caption>,
// }));

describe('Home Page', () => {
  beforeEach(() => {
    // Reset mocks before each test
    (fetch as jest.Mock).mockClear();
  });

  it('should render loading state initially', () => {
    // Mock the initial /api/results fetch to be pending indefinitely
    (fetch as jest.Mock).mockImplementation((url: string) => {
      if (url === '/api/results') {
        return new Promise(() => {}); // Never resolves
      }
      return Promise.reject(new Error('Unexpected fetch call'));
    });
    render(<Home />);
    // Check for the "Loading..." text within the table body
    expect(screen.getByRole('cell', { name: /Loading.../i })).toBeInTheDocument();
    // Also check the caption
    expect(screen.getByText(/Loading recent signals.../i)).toBeInTheDocument();
  });

  it('should render stock data after successful fetches', async () => {
    const mockResults = {
      golden_crosses: ['2222.SR'],
      last_scan_time: '2025-04-09 21:00:00 UTC',
    };
    const mockStockDetails = {
      status: 'success',
      chart_data: [
        { Date: '2025-04-08', Close: 35.00, SMA_50: 33.80, SMA_200: 32.80 },
        { Date: '2025-04-09', Close: 35.50, SMA_50: 34.00, SMA_200: 33.00 }, // Latest data
      ],
      // other potential fields not used by this component part
    };

    (fetch as jest.Mock).mockImplementation(async (url: string) => {
      if (url === '/api/results') {
        return { ok: true, json: async () => mockResults };
      }
      if (url === '/api/stock/2222.SR') {
        return { ok: true, json: async () => mockStockDetails };
      }
      throw new Error(`Unexpected fetch call to ${url}`);
    });

    render(<Home />);

    // Wait for the data to be loaded and rendered
    // Check for symbol, date, and SMA values from the *last* entry in mockStockDetails.chart_data
    await waitFor(() => {
      expect(screen.getByRole('cell', { name: '2222.SR' })).toBeInTheDocument();
    });
    expect(screen.getByRole('cell', { name: '2025-04-09' })).toBeInTheDocument();
    expect(screen.getByRole('cell', { name: '34.00' })).toBeInTheDocument(); // Formatted SMA50
    expect(screen.getByRole('cell', { name: '33.00' })).toBeInTheDocument(); // Formatted SMA200
    // Check caption update
    expect(screen.getByText(/Recent Golden Cross Signals/i)).toBeInTheDocument();
    // Check last scan time update
    expect(screen.getByText(/Last Scan: 2025-04-09 21:00:00 UTC/i)).toBeInTheDocument();
  });

  it('should render error message on fetch failure for /api/results', async () => {
    const apiError = new Error('API Error Results');
     (fetch as jest.Mock).mockImplementation(async (url: string) => {
      if (url === '/api/results') {
         throw apiError;
      }
       throw new Error(`Unexpected fetch call to ${url}`);
    });


    render(<Home />);

    // Wait for the error message to appear in the table cell
    await waitFor(() => {
      // Check for the error message format used in the component
      expect(screen.getByText(`Error loading data: ${apiError.message}`)).toBeInTheDocument();
    });
     // Check caption update
    expect(screen.getByText(/No recent signals found./i)).toBeInTheDocument();
  });

   it('should render error message on fetch failure for /api/stock/{symbol}', async () => {
    const mockResults = {
      golden_crosses: ['2222.SR'], // Need a symbol to trigger the second fetch
      last_scan_time: '2025-04-09 21:00:00 UTC',
    };
    const stockApiError = new Error('API Error Stock');

    (fetch as jest.Mock).mockImplementation(async (url: string) => {
      if (url === '/api/results') {
        return { ok: true, json: async () => mockResults };
      }
      if (url === '/api/stock/2222.SR') {
         throw stockApiError; // Fail the second fetch
      }
      throw new Error(`Unexpected fetch call to ${url}`);
    });

    render(<Home />);

    // Wait for the error message to appear
    // The component catches the error and sets the general error state
     await waitFor(() => {
      expect(screen.getByText(`Error loading data: ${stockApiError.message}`)).toBeInTheDocument();
    });
     // Check caption update
    expect(screen.getByText(/No recent signals found./i)).toBeInTheDocument();
  });


});