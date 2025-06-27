import type { NextPage } from 'next';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { useState, useEffect, useMemo, FC, FormEvent } from 'react';
import useSWR from 'swr';
import {
  MagnifyingGlassIcon,
  MapIcon,
  ListBulletIcon,
  AdjustmentsHorizontalIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import { clsx } from 'clsx';

// --- MOCK DATA & TYPES (to be replaced with API types) ---
// In a real app, these types would be generated from the backend's OpenAPI schema
// or defined in a shared types package.
interface ProviderLocation {
  address: string;
  city: string;
  state: string;
  postal_code: string;
}

interface Provider {
  id: string;
  name: string;
  provider_type: 'doctor' | 'clinic';
  specialties: { name: string }[];
  location: ProviderLocation;
  phone?: string;
  rating?: number;
  review_count?: number;
  image_url?: string;
  source: 'betterdoctor' | 'practo';
}

interface ApiResponse {
  total: number;
  page: number;
  limit: number;
  providers: Provider[];
}

// --- API FETCHER ---
// This would typically live in `utils/api.ts`
const fetcher = (url: string) => fetch(url).then((res) => res.json());

// --- UI SUB-COMPONENTS ---
// In a real app, these would be in their own files under `/components`

const SkeletonCard: FC = () => (
  <div className="bg-white dark:bg-neutral-800 p-4 rounded-lg shadow-md animate-pulse">
    <div className="flex gap-4">
      <div className="w-24 h-24 bg-neutral-200 dark:bg-neutral-700 rounded-md"></div>
      <div className="flex-1 space-y-3 py-1">
        <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-3/4"></div>
        <div className="h-3 bg-neutral-200 dark:bg-neutral-700 rounded w-1/2"></div>
        <div className="h-3 bg-neutral-200 dark:bg-neutral-700 rounded w-5/6"></div>
      </div>
    </div>
  </div>
);

const ProviderCard: FC<{ provider: Provider }> = ({ provider }) => (
  <div className="bg-white dark:bg-neutral-800 p-4 rounded-lg shadow-md hover:shadow-lg transition-shadow duration-300 flex flex-col sm:flex-row gap-4">
    <img
      src={provider.image_url || `https://ui-avatars.com/api/?name=${provider.name.replace(' ', '+')}&background=E6F0FF&color=0044CC`}
      alt={`Photo of ${provider.name}`}
      className="w-full sm:w-28 h-28 object-cover rounded-md"
    />
    <div className="flex-1">
      <h3 className="text-xl font-bold text-primary-dark dark:text-primary-light">{provider.name}</h3>
      <p className="text-neutral-600 dark:text-neutral-400">{provider.specialties[0]?.name || 'General Practice'}</p>
      <p className="text-sm text-neutral-500 mt-1">
        {provider.location.address}, {provider.location.city}, {provider.location.state} {provider.location.postal_code}
      </p>
      <div className="mt-2 text-sm text-neutral-700 dark:text-neutral-300">
        {provider.phone && <p>Phone: {provider.phone}</p>}
        {provider.rating && <p>Rating: {provider.rating}/5 ({provider.review_count} reviews)</p>}
      </div>
      <div className="mt-3 flex justify-between items-center">
        <span className="text-xs font-semibold uppercase px-2 py-1 bg-secondary-light text-secondary-dark rounded-full">
          {provider.source}
        </span>
        <a
          href={`/providers/${provider.id}?source=${provider.source}`}
          className="text-primary hover:text-primary-dark font-semibold transition-colors"
        >
          View Details &rarr;
        </a>
      </div>
    </div>
  </div>
);

// --- MAIN PAGE COMPONENT ---

const ProviderSearchPage: NextPage = () => {
  const router = useRouter();
  const [viewMode, setViewMode] = useState<'list' | 'map'>('list');
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  // Search and filter states
  const [searchQuery, setSearchQuery] = useState((router.query.q as string) || '');
  const [locationQuery, setLocationQuery] = useState((router.query.loc as string) || '');
  const [filters, setFilters] = useState({
    specialty: '',
    providerType: 'doctor',
    gender: 'any',
  });
  const [currentPage, setCurrentPage] = useState(1);

  // Update state from URL on initial load
  useEffect(() => {
    if (router.isReady) {
      setSearchQuery((router.query.q as string) || '');
      setLocationQuery((router.query.loc as string) || '');
    }
  }, [router.isReady, router.query]);

  // Construct API URL for SWR based on state
  const apiUrl = useMemo(() => {
    const params = new URLSearchParams();
    if (searchQuery) params.append('query', searchQuery);
    if (locationQuery) params.append('city', locationQuery); // Simple mapping for now
    if (filters.specialty) params.append('specialty', filters.specialty);
    if (filters.providerType) params.append('provider_type', filters.providerType);
    if (filters.gender !== 'any') params.append('gender', filters.gender);
    params.append('page', String(currentPage));
    params.append('limit', '12');

    return `/api/providers/search?${params.toString()}`;
  }, [searchQuery, locationQuery, filters, currentPage]);

  const { data, error, isLoading } = useSWR<ApiResponse>(apiUrl, fetcher);

  const handleSearch = (e: FormEvent) => {
    e.preventDefault();
    // Update URL to reflect search, which will trigger SWR refetch via useEffect
    router.push({
      pathname: '/providers/search',
      query: { q: searchQuery, loc: locationQuery },
    });
    setCurrentPage(1); // Reset to first page on new search
  };

  const handleFilterChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
    setCurrentPage(1);
  };

  return (
    <>
      <Head>
        <title>Provider Search - HealthFinder</title>
        <meta name="description" content="Find and compare doctors, clinics, and specialists near you." />
      </Head>

      <div className="min-h-screen bg-neutral-50 dark:bg-neutral-900">
        {/* In a real app, a <Navbar /> would be here */}

        <main className="container mx-auto px-4 py-8">
          <div className="flex flex-col lg:flex-row gap-8">
            {/* --- FILTER PANEL (Left Sidebar) --- */}
            <aside className={clsx(
              "fixed inset-y-0 left-0 z-30 w-72 bg-white dark:bg-neutral-800 shadow-xl transform transition-transform duration-300 ease-in-out lg:static lg:transform-none lg:shadow-none lg:bg-transparent lg:dark:bg-transparent",
              isFilterOpen ? "translate-x-0" : "-translate-x-full"
            )}>
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-bold">Filters</h2>
                  <button onClick={() => setIsFilterOpen(false)} className="lg:hidden">
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>
                <form className="space-y-6">
                  <div>
                    <label htmlFor="specialty" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">Specialty</label>
                    <input type="text" name="specialty" id="specialty" value={filters.specialty} onChange={handleFilterChange} className="mt-1 block w-full rounded-md border-neutral-300 dark:border-neutral-600 shadow-sm focus:border-primary focus:ring-primary sm:text-sm dark:bg-neutral-700" placeholder="e.g., Cardiology" />
                  </div>
                  <div>
                    <label htmlFor="providerType" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">Provider Type</label>
                    <select name="providerType" id="providerType" value={filters.providerType} onChange={handleFilterChange} className="mt-1 block w-full rounded-md border-neutral-300 dark:border-neutral-600 shadow-sm focus:border-primary focus:ring-primary sm:text-sm dark:bg-neutral-700">
                      <option value="doctor">Doctor</option>
                      <option value="clinic">Clinic</option>
                      <option value="hospital">Hospital</option>
                    </select>
                  </div>
                  <div>
                    <label htmlFor="gender" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">Gender</label>
                    <select name="gender" id="gender" value={filters.gender} onChange={handleFilterChange} className="mt-1 block w-full rounded-md border-neutral-300 dark:border-neutral-600 shadow-sm focus:border-primary focus:ring-primary sm:text-sm dark:bg-neutral-700">
                      <option value="any">Any</option>
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                    </select>
                  </div>
                </form>
              </div>
            </aside>

            {/* --- MAIN CONTENT (Search, Results, Map) --- */}
            <div className="flex-1">
              {/* Search Bar */}
              <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-2 mb-6">
                <input type="text" value={searchQuery} onChange={e => setSearchQuery(e.target.value)} placeholder="Condition, specialty, name..." className="flex-grow p-3 border border-neutral-300 dark:border-neutral-600 rounded-md focus:ring-2 focus:ring-primary dark:bg-neutral-800" />
                <input type="text" value={locationQuery} onChange={e => setLocationQuery(e.target.value)} placeholder="City, State, ZIP" className="flex-grow p-3 border border-neutral-300 dark:border-neutral-600 rounded-md focus:ring-2 focus:ring-primary dark:bg-neutral-800" />
                <button type="submit" className="bg-primary hover:bg-primary-dark text-white font-bold py-3 px-6 rounded-md flex items-center justify-center gap-2 transition-colors">
                  <MagnifyingGlassIcon className="h-5 w-5" />
                  <span>Search</span>
                </button>
              </form>

              {/* View Toggle & Result Summary */}
              <div className="flex justify-between items-center mb-4">
                <div className="text-sm text-neutral-600 dark:text-neutral-400">
                  {isLoading ? 'Loading...' : `Showing ${data?.providers.length || 0} of ${data?.total || 0} results`}
                </div>
                <div className="flex items-center gap-2">
                   <button onClick={() => setIsFilterOpen(true)} className="lg:hidden p-2 rounded-md bg-white dark:bg-neutral-700 border border-neutral-300 dark:border-neutral-600">
                    <AdjustmentsHorizontalIcon className="h-5 w-5" />
                  </button>
                  <div className="flex rounded-md bg-white dark:bg-neutral-700 border border-neutral-300 dark:border-neutral-600">
                    <button onClick={() => setViewMode('list')} className={clsx("p-2 rounded-l-md", { 'bg-primary text-white': viewMode === 'list' })}>
                      <ListBulletIcon className="h-5 w-5" />
                    </button>
                    <button onClick={() => setViewMode('map')} className={clsx("p-2 rounded-r-md", { 'bg-primary text-white': viewMode === 'map' })}>
                      <MapIcon className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Conditional Content */}
              {error && <div className="text-center text-danger p-8 bg-red-50 dark:bg-red-900/20 rounded-lg">Failed to load data. Please try again.</div>}
              
              {viewMode === 'list' ? (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                  {isLoading && Array.from({ length: 9 }).map((_, i) => <SkeletonCard key={i} />)}
                  {data?.providers.map(provider => <ProviderCard key={provider.id} provider={provider} />)}
                  {!isLoading && data?.providers.length === 0 && (
                    <div className="md:col-span-2 xl:col-span-3 text-center py-16">
                      <h3 className="text-2xl font-semibold">No Results Found</h3>
                      <p className="text-neutral-500 mt-2">Try adjusting your search or filters.</p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="h-[600px] bg-neutral-200 dark:bg-neutral-800 rounded-lg flex items-center justify-center text-neutral-500">
                  <p>Map view would be rendered here. (Requires a library like Leaflet or React-Google-Maps)</p>
                </div>
              )}

              {/* Pagination */}
              {data && data.total > data.limit && (
                <div className="mt-8 flex justify-center items-center gap-4">
                  <button
                    onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    className="px-4 py-2 bg-white dark:bg-neutral-700 border border-neutral-300 dark:border-neutral-600 rounded-md disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <span className="text-sm">
                    Page {currentPage} of {Math.ceil(data.total / data.limit)}
                  </span>
                  <button
                    onClick={() => setCurrentPage(p => Math.min(p + 1, Math.ceil(data.total / data.limit)))}
                    disabled={currentPage * data.limit >= data.total}
                    className="px-4 py-2 bg-white dark:bg-neutral-700 border border-neutral-300 dark:border-neutral-600 rounded-md disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </>
  );
};

export default ProviderSearchPage;
