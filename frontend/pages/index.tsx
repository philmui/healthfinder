import type { NextPage } from 'next';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { useState, FormEvent } from 'react';
import { MagnifyingGlassIcon, UserGroupIcon, BeakerIcon, DocumentTextIcon, LifebuoyIcon } from '@heroicons/react/24/outline';
import Link from 'next/link';

// A conceptual Layout component - in a real app, this would wrap the page content
// providing consistent navbar, footer, etc.
const Layout = ({ children }: { children: React.ReactNode }) => (
  <div className="min-h-screen bg-neutral-100 dark:bg-neutral-900 text-neutral-800 dark:text-neutral-200">
    {/* In a real app, a <Navbar /> component would go here */}
    <main>{children}</main>
    {/* In a real app, a <Footer /> component would go here */}
  </div>
);

const HomePage: NextPage = () => {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [location, setLocation] = useState('');

  const handleSearch = (e: FormEvent) => {
    e.preventDefault();
    if (!query && !location) return; // Prevent empty search

    // Navigate to the provider search page with query parameters
    router.push({
      pathname: '/providers/search',
      query: { q: query, loc: location },
    });
  };

  const featureCards = [
    {
      icon: UserGroupIcon,
      title: 'Find a Provider',
      description: 'Search for doctors, clinics, and specialists in your area.',
      href: '/providers',
      bgColor: 'bg-primary-light',
      textColor: 'text-primary-dark',
    },
    {
      icon: BeakerIcon,
      title: 'Clinical Trials',
      description: 'Explore ongoing clinical trials for various conditions.',
      href: '/clinical-trials',
      bgColor: 'bg-secondary-light',
      textColor: 'text-secondary-dark',
    },
    {
      icon: DocumentTextIcon,
      title: 'Biomedical Research',
      description: 'Access the latest medical articles and research from PubMed.',
      href: '/research',
      bgColor: 'bg-accent-light',
      textColor: 'text-accent-dark',
    },
    {
      icon: LifebuoyIcon,
      title: 'Genetics & Diseases',
      description: 'Understand genetic conditions and diseases with trusted info.',
      href: '/genetics',
      bgColor: 'bg-neutral-200',
      textColor: 'text-neutral-700',
    },
  ];

  return (
    <Layout>
      <Head>
        <title>HealthFinder - Your Guide to Healthcare Information</title>
        <meta name="description" content="Search for doctors, clinical trials, and biomedical research. HealthFinder helps you make informed health decisions." />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      {/* Hero Section */}
      <section className="bg-primary-light dark:bg-neutral-800 py-20 sm:py-28">
        <div className="container mx-auto px-4 text-center">
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold text-primary-dark dark:text-white mb-4">
            Find the Right Care, Right Now
          </h1>
          <p className="text-lg sm:text-xl text-neutral-600 dark:text-neutral-300 max-w-3xl mx-auto mb-8">
            HealthFinder connects you with trusted doctors, cutting-edge clinical trials, and the latest medical research to empower your health journey.
          </p>

          {/* Provider Search Form */}
          <form
            onSubmit={handleSearch}
            className="max-w-2xl mx-auto bg-white dark:bg-neutral-700 p-4 rounded-lg shadow-lg flex flex-col sm:flex-row gap-2"
          >
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Specialty, condition, or doctor's name..."
              className="flex-grow p-3 border border-neutral-300 dark:border-neutral-600 rounded-md focus:ring-2 focus:ring-primary dark:bg-neutral-800"
              aria-label="Search query"
            />
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="City, State, or ZIP Code"
              className="flex-grow p-3 border border-neutral-300 dark:border-neutral-600 rounded-md focus:ring-2 focus:ring-primary dark:bg-neutral-800"
              aria-label="Location"
            />
            <button
              type="submit"
              className="bg-primary hover:bg-primary-dark text-white font-bold py-3 px-6 rounded-md flex items-center justify-center gap-2 transition-colors"
            >
              <MagnifyingGlassIcon className="h-5 w-5" />
              <span>Search</span>
            </button>
          </form>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 sm:py-24">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-neutral-800 dark:text-white">
              Your Health Information Hub
            </h2>
            <p className="mt-4 text-lg text-neutral-600 dark:text-neutral-400">
              Explore our features designed to provide you with comprehensive health insights.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {featureCards.map((feature) => (
              <Link href={feature.href} key={feature.title} legacyBehavior>
                <a className="block p-8 bg-white dark:bg-neutral-800 rounded-xl shadow-md hover:shadow-xl hover:-translate-y-1 transition-all duration-300">
                  <div className={`w-16 h-16 rounded-full flex items-center justify-center ${feature.bgColor}`}>
                    <feature.icon className={`h-8 w-8 ${feature.textColor}`} />
                  </div>
                  <h3 className="mt-6 text-xl font-bold text-neutral-900 dark:text-white">
                    {feature.title}
                  </h3>
                  <p className="mt-2 text-neutral-600 dark:text-neutral-400">
                    {feature.description}
                  </p>
                </a>
              </Link>
            ))}
          </div>
        </div>
      </section>
    </Layout>
  );
};

export default HomePage;
