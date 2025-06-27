import type { FC } from 'react';

/**
 * A skeleton loading component that mimics the layout of the ProviderCard.
 * It's used to provide a visual placeholder while the actual provider data is being fetched,
 * improving the user experience by reducing perceived loading time.
 */
const SkeletonCard: FC = () => {
  return (
    <div className="bg-white dark:bg-neutral-800 p-4 rounded-lg shadow-md animate-pulse">
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="w-full sm:w-28 h-28 bg-neutral-200 dark:bg-neutral-700 rounded-md flex-shrink-0"></div>
        <div className="flex-1 space-y-3 py-1">
          <div className="h-5 bg-neutral-200 dark:bg-neutral-700 rounded w-3/4"></div>
          <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-1/2"></div>
          <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-5/6"></div>
          <div className="pt-4 flex justify-between items-center">
            <div className="h-5 bg-neutral-200 dark:bg-neutral-700 rounded-full w-20"></div>
            <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-24"></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SkeletonCard;
