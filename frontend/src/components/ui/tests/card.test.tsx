import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../card'; // Adjust path as necessary

describe('Card Component', () => {
  it('should render Card with children', () => {
    render(<Card><div>Card Content</div></Card>);
    expect(screen.getByText('Card Content')).toBeInTheDocument();
  });

  it('should render CardHeader with CardTitle and CardDescription', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Test Title</CardTitle>
          <CardDescription>Test Description</CardDescription>
        </CardHeader>
      </Card>
    );
    expect(screen.getByText('Test Title')).toBeInTheDocument();
    expect(screen.getByText('Test Description')).toBeInTheDocument();
  });

  it('should render CardContent', () => {
    render(
      <Card>
        <CardContent>
          <p>This is the main content.</p>
        </CardContent>
      </Card>
    );
    expect(screen.getByText('This is the main content.')).toBeInTheDocument();
  });

  it('should render CardFooter', () => {
    render(
      <Card>
        <CardFooter>
          <button>Footer Button</button>
        </CardFooter>
      </Card>
    );
    expect(screen.getByRole('button', { name: 'Footer Button' })).toBeInTheDocument();
  });

  it('should apply custom className to Card', () => {
    const { container } = render(<Card className="custom-card-class">Content</Card>);
    // eslint-disable-next-line testing-library/no-container, testing-library/no-node-access
    const cardElement = container.firstChild;
    expect(cardElement).toHaveClass('custom-card-class');
  });
});