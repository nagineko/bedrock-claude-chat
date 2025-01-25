import React from 'react';
import { BaseProps } from '../@types/common';
type Props = BaseProps & {
  progress: number;
};

const Progress: React.FC<Props> = (props) => {
  return (
    <div className="h-2.5 w-full rounded-full bg-aws-gray-french transition-all">
      <div
        className={`h-2.5 rounded-full bg-aws-blue-cerulean`}
        style={{ width: `${props.progress}%` }}></div>
    </div>
  );
};

export default Progress;
