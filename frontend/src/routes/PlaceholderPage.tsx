import { Link } from 'react-router-dom';
import { Button } from '../components/ui/Button';

interface PlaceholderPageProps {
  title: string;
  description: string;
}

export function PlaceholderPage({ title, description }: PlaceholderPageProps) {
  return (
    <div className="mx-auto w-full max-w-2xl py-16 text-center">
      <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl">{title}</h1>
      <p className="mt-6 text-xl text-gray-600">{description}</p>
      <Link to="/">
        <Button className="mt-10">Back to Home</Button>
      </Link>
    </div>
  );
}
