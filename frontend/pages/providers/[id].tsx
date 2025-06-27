import type { GetServerSideProps, InferGetServerSidePropsType, NextPage } from 'next';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { useState, FC } from 'react';
import {
  BuildingOffice2Icon,
  AcademicCapIcon,
  PhoneIcon,
  GlobeAltIcon,
  MapPinIcon,
  InformationCircleIcon,
  CalendarDaysIcon,
  StarIcon,
} from '@heroicons/react/24/outline';
import { clsx } from 'clsx';

// --- TYPE DEFINITIONS ---
// These should ideally be generated from an OpenAPI spec or shared in a types package.
// They are based on the Pydantic models in `server/app/api/providers.py`.

interface ProviderLocation {
  address?: string;
  city?: string;
  state?: string;
  postal_code?: string;
  country?: string;
  latitude?: number;
  longitude?: number;
}

interface ProviderSpecialty {
  name: string;
  description?: string;
  category?: string;
}

interface ProviderBase {
  id: string;
  name: string;
  provider_type: 'doctor' | 'clinic' | 'hospital';
  specialties: ProviderSpecialty[];
  location: ProviderLocation;
  phone?: string;
  website?: string;
  rating?: number;
  review_count?: number;
  accepts_new_patients?: boolean;
  source: 'betterdoctor' | 'practo';
  image_url?: string;
  biography?: string;
}

interface DoctorDetails extends ProviderBase {
  provider_type: 'doctor';
  npi?: string;
  gender?: string;
  education: string[];
  board_certifications: string[];
  years_of_experience?: number;
}

type Provider = DoctorDetails; // Add other types like ClinicDetails with a |

interface ProviderPageProps {
  provider: Provider | null;
  error?: string;
}

// --- SERVER-SIDE DATA FETCHING ---

export const getServerSideProps: GetServerSideProps<ProviderPageProps> = async (context) => {
  const { id, source } = context.query;

  if (typeof id !== 'string' || typeof source !== 'string') {
    return { notFound: true }; // Invalid route
  }

  try {
    const apiUrl = `${process.env.NEXT_PUBLIC_API_URL}/providers/${id}?source=${source}`;
    const res = await fetch(apiUrl);

    if (!res.ok) {
      if (res.status === 404) {
        return { notFound: true };
      }
      throw new Error(`Failed to fetch provider data: ${res.statusText}`);
    }

    const data = await res.json();
    return {
      props: {
        provider: data.provider,
      },
    };
  } catch (error) {
    console.error('Error fetching provider details:', error);
    // You could pass an error message to the component to display a user-friendly error
    return { props: { provider: null, error: 'Could not load provider information.' } };
  }
};

// --- UI SUB-COMPONENTS ---

const InfoCard: FC<{ icon: React.ElementType; title: string; children: React.ReactNode }> = ({ icon: Icon, title, children }) => (
  <div className="bg-white dark:bg-neutral-800 p-6 rounded-lg shadow">
    <div className="flex items-center mb-3">
      <Icon className="h-6 w-6 text-primary mr-3" />
      <h3 className="text-lg font-semibold text-neutral-800 dark:text-neutral-200">{title}</h3>
    </div>
    <div className="text-neutral-600 dark:text-neutral-400 space-y-2">{children}</div>
  </div>
);

const TabButton: FC<{ active: boolean; onClick: () => void; children: React.ReactNode }> = ({ active, onClick, children }) => (
  <button
    onClick={onClick}
    className={clsx(
      'px-4 py-2 font-semibold rounded-md transition-colors duration-200',
      active
        ? 'bg-primary text-white'
        : 'text-neutral-600 dark:text-neutral-300 hover:bg-neutral-200 dark:hover:bg-neutral-700'
    )}
  >
    {children}
  </button>
);

// --- MAIN PAGE COMPONENT ---

const ProviderDetailPage: NextPage<InferGetServerSidePropsType<typeof getServerSideProps>> = ({ provider, error }) => {
  const [activeTab, setActiveTab] = useState<'info' | 'availability' | 'reviews'>('info');
  const router = useRouter();

  if (router.isFallback) {
    return <div>Loading...</div>; // Fallback loading state
  }

  if (error || !provider) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-neutral-100">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-danger">An Error Occurred</h1>
          <p className="text-neutral-600">{error || 'Provider could not be found.'}</p>
          <button onClick={() => router.back()} className="mt-4 px-4 py-2 bg-primary text-white rounded-md">
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <>
      <Head>
        <title>{`${provider.name} | HealthFinder`}</title>
        <meta name="description" content={`Detailed information for ${provider.name}, a ${provider.specialties[0]?.name || 'healthcare provider'}.`} />
      </Head>

      <div className="min-h-screen bg-neutral-100 dark:bg-neutral-900">
        {/* Placeholder for a global Navbar */}

        <main className="container mx-auto p-4 sm:p-6 lg:p-8">
          {/* --- Provider Header --- */}
          <div className="bg-white dark:bg-neutral-800 rounded-lg shadow-lg p-6 md:p-8 mb-8">
            <div className="flex flex-col md:flex-row items-center gap-6">
              <img
                src={provider.image_url || `https://ui-avatars.com/api/?name=${provider.name.replace(' ', '+')}&size=128&background=E6F0FF&color=0044CC`}
                alt={`Photo of ${provider.name}`}
                className="w-32 h-32 rounded-full object-cover border-4 border-primary-light"
              />
              <div className="text-center md:text-left">
                <h1 className="text-3xl md:text-4xl font-bold text-neutral-900 dark:text-white">{provider.name}</h1>
                <p className="text-xl text-primary dark:text-primary-light mt-1">
                  {provider.specialties.map(s => s.name).join(', ') || 'General Practice'}
                </p>
                <div className="mt-2 text-sm text-neutral-500">
                  Sourced from: <span className="font-semibold capitalize">{provider.source}</span>
                </div>
              </div>
            </div>
          </div>

          {/* --- Tab Navigation --- */}
          <div className="mb-6 flex items-center justify-center space-x-2 border-b border-neutral-200 dark:border-neutral-700 pb-2">
            <TabButton active={activeTab === 'info'} onClick={() => setActiveTab('info')}>
              <InformationCircleIcon className="h-5 w-5 inline-block mr-2" />
              Information
            </TabButton>
            <TabButton active={activeTab === 'availability'} onClick={() => setActiveTab('availability')}>
              <CalendarDaysIcon className="h-5 w-5 inline-block mr-2" />
              Availability
            </TabButton>
            <TabButton active={activeTab === 'reviews'} onClick={() => setActiveTab('reviews')}>
              <StarIcon className="h-5 w-5 inline-block mr-2" />
              Reviews
            </TabButton>
          </div>

          {/* --- Tab Content --- */}
          <div>
            {activeTab === 'info' && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {provider.biography && (
                  <div className="md:col-span-2 lg:col-span-3">
                    <InfoCard icon={InformationCircleIcon} title="About">
                      <p className="whitespace-pre-wrap">{provider.biography}</p>
                    </InfoCard>
                  </div>
                )}
                <InfoCard icon={MapPinIcon} title="Location & Contact">
                  <p>{provider.location.address}</p>
                  <p>{`${provider.location.city}, ${provider.location.state} ${provider.location.postal_code}`}</p>
                  {provider.phone && (
                    <a href={`tel:${provider.phone}`} className="flex items-center hover:text-primary">
                      <PhoneIcon className="h-4 w-4 mr-2" /> {provider.phone}
                    </a>
                  )}
                  {provider.website && (
                    <a href={provider.website} target="_blank" rel="noopener noreferrer" className="flex items-center hover:text-primary">
                      <GlobeAltIcon className="h-4 w-4 mr-2" /> Website
                    </a>
                  )}
                </InfoCard>
                <InfoCard icon={AcademicCapIcon} title="Credentials">
                  {provider.education?.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-neutral-700 dark:text-neutral-300">Education</h4>
                      <ul className="list-disc list-inside">
                        {provider.education.map((edu, i) => <li key={i}>{edu}</li>)}
                      </ul>
                    </div>
                  )}
                  {provider.board_certifications?.length > 0 && (
                    <div className="mt-2">
                      <h4 className="font-semibold text-neutral-700 dark:text-neutral-300">Certifications</h4>
                      <ul className="list-disc list-inside">
                        {provider.board_certifications.map((cert, i) => <li key={i}>{cert}</li>)}
                      </ul>
                    </div>
                  )}
                  {provider.years_of_experience && <p className="mt-2">Years of Experience: {provider.years_of_experience}</p>}
                </InfoCard>
                <InfoCard icon={BuildingOffice2Icon} title="Practice Details">
                  <p>Accepts New Patients: {provider.accepts_new_patients ? 'Yes' : 'No'}</p>
                  {provider.gender && <p>Gender: <span className="capitalize">{provider.gender}</span></p>}
                  {provider.npi && <p>NPI: {provider.npi}</p>}
                </InfoCard>
              </div>
            )}
            {activeTab === 'availability' && (
              <div className="text-center py-12 bg-white dark:bg-neutral-800 rounded-lg shadow">
                <CalendarDaysIcon className="h-12 w-12 mx-auto text-neutral-400" />
                <h3 className="mt-2 text-xl font-semibold">Availability Information</h3>
                <p className="mt-1 text-neutral-500">This feature is coming soon.</p>
              </div>
            )}
            {activeTab === 'reviews' && (
              <div className="text-center py-12 bg-white dark:bg-neutral-800 rounded-lg shadow">
                <StarIcon className="h-12 w-12 mx-auto text-neutral-400" />
                <h3 className="mt-2 text-xl font-semibold">Patient Reviews</h3>
                <p className="mt-1 text-neutral-500">This feature is coming soon.</p>
              </div>
            )}
          </div>
        </main>
      </div>
    </>
  );
};

export default ProviderDetailPage;
