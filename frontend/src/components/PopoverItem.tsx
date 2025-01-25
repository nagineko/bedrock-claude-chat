import React, { ReactNode } from 'react';

type Props = {
  className?: string;
  children: ReactNode;
  onClick: () => void;
};

const PopoverItem: React.FC<Props> = (props) => {
  return (
    <div
      className={`${
        props.className ?? ''
      } flex cursor-pointer items-center gap-1 border-b border-aws-blue-navy/50 dark:border-aws-gray-light/50 bg-aws-white-smoke dark:bg-aws-black-graphite px-2 py-1 first:rounded-t last:rounded-b last:border-b-0 hover:brightness-75`}
      onClick={props.onClick}>
      {props.children}
    </div>
  );
};

export default PopoverItem;
