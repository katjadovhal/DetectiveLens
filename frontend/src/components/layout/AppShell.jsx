import { Outlet } from 'react-router-dom';
import { Header } from './Header';

export function AppShell() {
  return (
    <div className="flex min-h-screen flex-col bg-white">
      <Header />
      <main className="flex-1 w-full px-6 py-10 sm:px-10 lg:px-16">
        <Outlet />
      </main>
    </div>
  );
}
