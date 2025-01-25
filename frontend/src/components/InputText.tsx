import React, { HTMLInputTypeAttribute } from 'react';
import { twMerge } from 'tailwind-merge';

type Props = {
  className?: string;
  label?: string;
  type?: HTMLInputTypeAttribute;
  value: string;
  disabled?: boolean;
  placeholder?: string;
  hint?: string;
  errorMessage?: string;
  onChange?: (s: string) => void;
};

const InputText: React.FC<Props> = (props) => {
  return (
    <div className={twMerge('flex flex-col', props.className)}>
      <input
        type={props.type ?? 'text'}
        className={twMerge(
          'peer h-9 rounded border p-1 dark:[color-scheme:dark]',
          'dark:bg-aws-black-jet dark:placeholder-aws-gray-ash dark:text-aws-gray-light',
          props.errorMessage
            ? 'border-2 border-aws-red'
            : 'border-aws-blue-navy/50 dark:border-aws-gray-light/50'
        )}
        disabled={props.disabled}
        value={props.value}
        placeholder={props.placeholder}
        onChange={(e) => {
          props.onChange ? props.onChange(e.target.value) : null;
        }}
      />
      {props.label && (
        <div
          className={twMerge(
            'order-first text-sm peer-focus:font-semibold peer-focus:italic',
            props.errorMessage
              ? 'font-bold text-aws-red'
              : 'text-aws-gray-grayish dark:text-aws-gray-ice peer-focus:text-aws-blue-navy dark:peer-focus:text-aws-gray-light'
          )}>
          {props.label}
        </div>
      )}
      {props.hint && !props.errorMessage && (
        <div className="mt-0.5 text-xs text-aws-gray-french dark:text-aws-gray-light">{props.hint}</div>
      )}
      {props.errorMessage && (
        <div className="mt-0.5 text-xs text-aws-red ">{props.errorMessage}</div>
      )}
    </div>
  );
};

export default InputText;
