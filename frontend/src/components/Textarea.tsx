import { forwardRef, useEffect, useRef, useState } from 'react';
import { BaseProps } from '../@types/common';
import { twMerge } from 'tailwind-merge';

type Props = BaseProps & {
  value?: string;
  label?: string;
  placeholder?: string;
  disabled?: boolean;
  hint?: string;
  noBorder?: boolean;
  rows?: number;
  onChange?: (value: string) => void;
};

const MAX_HEIGHT = 300;

const Textarea = forwardRef<HTMLElement, Props>((props, focusInputRef) => {
  const ref = useRef<HTMLTextAreaElement | null>(null);
  const [isMax, setIsMax] = useState(false);

  useEffect(() => {
    if (!ref.current) {
      return;
    }

    ref.current.style.height = 'auto';

    if (ref.current.scrollHeight > MAX_HEIGHT) {
      ref.current.style.height = MAX_HEIGHT + 'px';
      setIsMax(true);
    } else {
      ref.current.style.height = ref.current.scrollHeight + 'px';
      setIsMax(false);
    }
  }, [props.value]);

  return (
    <div className={`${props.className ?? ''} flex w-full flex-col`}>
      <textarea
        ref={element => {
          ref.current = element;
          if (focusInputRef) {
            if (typeof focusInputRef === 'function') {
              focusInputRef(element);
            } else {
              focusInputRef.current = element;
            }
          }
        }}
        className={twMerge(
          'peer w-full resize-none rounded p-1.5 outline-none dark:bg-aws-black-jet dark:placeholder-aws-gray-ash',
          isMax ? 'overflow-y-auto' : 'overflow-hidden',
          props.noBorder ? '' : 'border border-aws-blue-navy/50 dark:border-aws-gray-light/50',
          props.className
        )}
        rows={props.rows ?? 1}
        placeholder={props.placeholder}
        disabled={props.disabled}
        value={props.value}
        onChange={(e) => {
          props.onChange ? props.onChange(e.target.value) : null;
        }}
      />
      {props.label && (
        <div className="order-first text-sm text-aws-gray-grayish dark:text-aws-gray-ice peer-focus:font-semibold peer-focus:italic peer-focus:text-aws-blue-navy dark:peer-focus:text-aws-gray-light">
          {props.label}
        </div>
      )}
      {props.hint && (
        <div className="mt-0.5 text-xs text-aws-gray-french dark:text-aws-gray-light">{props.hint}</div>
      )}
    </div>
  );
});

export default Textarea;
