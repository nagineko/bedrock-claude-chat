import React from 'react';
import { useTranslation } from 'react-i18next';
import { PiSmileyXEyesFill } from 'react-icons/pi';

const ErrorFallback: React.FC = () => {
  const { t } = useTranslation();
  return (
    <div className="flex h-dvh flex-col items-center justify-center bg-aws-white-smoke dark:bg-aws-black-graphite">
      <div className="flex text-5xl font-bold dark:text-aws-gray-light">
        <PiSmileyXEyesFill />
        ERROR
      </div>
      <div className="mt-4 text-lg dark:text-aws-gray-light">{t('error.unexpectedError.title')}</div>
      <button
        className="underline dark:text-aws-blue-cobalt dark:hover:text-aws-gray-slate"
        onClick={() => (window.location.href = '/')}>
        {t('error.unexpectedError.restore')}
      </button>
    </div>
  );
};

export default ErrorFallback;
