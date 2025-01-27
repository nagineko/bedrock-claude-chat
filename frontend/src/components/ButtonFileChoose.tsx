import React, { ReactNode, useCallback } from 'react';
import { BaseProps } from '../@types/common';
import { twMerge } from 'tailwind-merge';

type Props = BaseProps & {
  children: ReactNode;
  disabled?: boolean;
  accept?: string;
  icon?: boolean;
  onChange: (fileList: FileList) => void;
};

const ButtonFileChoose: React.FC<Props> = (props) => {
  const onChange: React.ChangeEventHandler<HTMLInputElement> = useCallback(
    (e) => {
      if (e.target.files) {
        props.onChange(e.target.files);
      }
    },
    [props]
  );

  return (
    <label
      className={twMerge(
        props.className,
        'flex  items-center justify-center whitespace-nowrap rounded-lg  hover:shadow hover:brightness-75',
        props.icon
          ? 'rounded-full p-2 text-xl text-aws-blue dark:text-aws-gray'
          : 'border dark:border-aws-black-jet bg-aws-blue dark:bg-aws-black-jet p-1 px-3 text-aws-white dark:text-aws-white-silver',
        props.disabled ? 'opacity-30 ' : 'cursor-pointer'
      )}>
      {props.children}
      <input
        type="file"
        hidden
        disabled={props.disabled}
        multiple
        value={[]}
        onChange={onChange}
        accept={props.accept}
      />
    </label>
  );
};

export default ButtonFileChoose;
