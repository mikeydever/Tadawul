import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import {
  Table,
  TableHeader,
  TableBody,
  TableFooter, // Assuming TableFooter might exist or be added later, included for completeness
  TableRow,
  TableHead,
  TableCell,
  TableCaption,
} from '../table'; // Adjust path as necessary

describe('Table Component', () => {
  it('should render Table with basic structure', () => {
    render(
      <Table>
        <TableCaption>Test Caption</TableCaption>
        <TableHeader>
          <TableRow>
            <TableHead>Header 1</TableHead>
            <TableHead>Header 2</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell>Data 1</TableCell>
            <TableCell>Data 2</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    );

    // Check for caption
    expect(screen.getByText('Test Caption')).toBeInTheDocument();

    // Check for headers
    expect(screen.getByRole('columnheader', { name: 'Header 1' })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: 'Header 2' })).toBeInTheDocument();

    // Check for data cells
    expect(screen.getByRole('cell', { name: 'Data 1' })).toBeInTheDocument();
    expect(screen.getByRole('cell', { name: 'Data 2' })).toBeInTheDocument();
  });

  it('should apply custom className to Table', () => {
    const { container } = render(<Table className="custom-table-class" />);
    // eslint-disable-next-line testing-library/no-container, testing-library/no-node-access
    const tableElement = container.querySelector('.custom-table-class');
    expect(tableElement).toBeInTheDocument();
    expect(tableElement).toHaveClass('custom-table-class');
  });

  it('should apply custom className to TableRow', () => {
     render(
      <Table>
        <TableBody>
          <TableRow className="custom-row-class" data-testid="custom-row">
            <TableCell>Data</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    );
    expect(screen.getByTestId('custom-row')).toHaveClass('custom-row-class');
  });

   it('should apply custom className to TableCell', () => {
     render(
      <Table>
        <TableBody>
          <TableRow>
            <TableCell className="custom-cell-class" data-testid="custom-cell">Data</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    );
    expect(screen.getByTestId('custom-cell')).toHaveClass('custom-cell-class');
  });

});