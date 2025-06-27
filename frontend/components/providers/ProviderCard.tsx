import type { FC } from 'react';
import Link from 'next/link';

// In a real application, this type would likely be imported from a shared types
// directory or generated from the backend's OpenAPI schema.
interface ProviderLocation {
  address?: string;
  city?: string;
  state?: string;
  postal_code?: string;
}

interface Provider {
  id: string;
  name: string;
  specialties: { name: string }[];
  location: ProviderLocation;
  image_url?: string;
  source: 'betterdoctor' | 'practo';
}

interface ProviderCardProps {
  provider: Provider;
}

/**
 * A reusable card component to display summary information for a single healthcare provider.
 * It shows the provider's name, specialty, location, and a link to their detailed profile.
 *
 * @param {ProviderCardProps} props - The component props.
 * @param {Provider} props.provider - The provider object to display.
 */
const ProviderCard: FC<ProviderCardProps> = ({ provider }) => {
  const detailUrl = `/providers/${provider.id}?source=${provider.source}`;

  // Construct a displayable location string, filtering out empty parts.
  const locationString = [
    provider.location.address,
    provider.location.city,
    provider.location.state,
    provider.location.postal_code,
  ]
    .filter(Boolean)
    .join(', ');

  return (
    <div className="bg-white dark:bg-neutral-800 p-4 rounded-lg shadow-md hover:shadow-lg transition-shadow duration-300 flex flex-col sm:flex-row gap-4 h-full">
      <div className="flex-shrink-0">
        <img
          src={provider.image_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(provider.name)}&background=E6F0FF&color=0044CC&size=112`}
          alt={`Photo of ${provider.name}`}
          className="w-full sm:w-28 h-28 object-cover rounded-md"
          width={112}
          height={112}
        />
      </div>
      <div className="flex-1 flex flex-col">
        <div>
          <h3 className="text-xl font-bold text-primary-dark dark:text-primary-light">
            <Link href={detailUrl} legacyBehavior>
              <a className="hover:underline">{provider.name}</a>
            </Link>
          </h3>
          <p className="text-neutral-600 dark:text-neutral-400">
            {provider.specialties[0]?.name || 'General Practice'}
          </p>
          <p className="text-sm text-neutral-500 mt-1">
            {locationString}
          </p>
        </div>
        <div className="mt-auto pt-3 flex justify-between items-center">
          <span className="text-xs font-semibold uppercase px-2 py-1 bg-secondary-light text-secondary-dark rounded-full capitalize">
            {provider.source}
          </span>
          <Link href={detailUrl} legacyBehavior>
            <a className="text-primary hover:text-primary-dark font-semibold transition-colors">
              View Details &rarr;
            </a>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default ProviderCard;
