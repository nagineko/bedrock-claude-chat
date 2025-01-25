import React, { useMemo } from 'react';
import { BaseProps } from '../@types/common';
import { PiInfo, PiWarningCircleFill, PiWarningFill } from 'react-icons/pi';
import { twMerge } from 'tailwind-merge';

type Props = BaseProps & {
  severity: 'info' | 'warning' | 'error';
  title: string;
  children: React.ReactNode;
};

const Alert: React.FC<Props> = (props) => {
  const icon = useMemo(() => {
    switch (props.severity) {
      case 'info':
        return <PiInfo className="text-2xl" />;
      case 'warning':
        return <PiWarningFill className="text-2xl" />;
      case 'error':
        return <PiWarningCircleFill className="text-2xl" />;
    }
  }, [props.severity]);

  return (
    <div
      className={twMerge(
        'flex flex-col rounded border border-aws-blue-navy dark:border-aws-black-smoke shadow-lg',
        props.severity === 'info' && 'bg-aws-blue-cerulean',
        props.severity === 'warning' && 'bg-aws-yellow',
        props.severity === 'error' && 'bg-aws-aws-red',
        props.className
      )}>
      <div
        className={twMerge(
          'flex gap-2 p-2 font-bold text-aws-white dark:text-aws-white-silver'
        )}>
        {icon}
        <div>{props.title}</div>
      </div>

      <div className="px-2 pb-2 text-aws-white dark:text-aws-white-silver">
        {props.children}
      </div>
    </div>
  );
};

export default Alert;
