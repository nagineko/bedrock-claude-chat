import { ReactNode } from 'react';
import { BaseProps } from '../@types/common';
import { useTranslation } from 'react-i18next';

type Props = BaseProps & {
  bot: {
    id: string;
    title: string;
    description: string;
    available: boolean;
  };
  onClick: (botId: string) => void;
  children: ReactNode;
};

const ListItemBot: React.FC<Props> = (props) => {
  const { t } = useTranslation();
  return (
    <div
      key={props.bot.id}
      className={`${
        props.className ?? ''
      } relative flex w-full justify-between border-b border-aws-gray-ice`}>
      <div
        className={`h-full grow bg-aws-white-smoke dark:bg-aws-black-graphite p-2 ${
          props.bot.available
            ? 'cursor-pointer hover:brightness-90'
            : 'text-aws-blue-navy/30 dark:text-aws-gray-light/30'
        }`}
        onClick={() => {
          if (props.bot.available) {
            props.onClick(props.bot.id);
          }
        }}>
        <div className="w-full overflow-hidden text-ellipsis text-sm font-semibold">
          <span
            className={
              props.bot.available
                ? 'dark:text-aws-gray-light'
                : 'dark:text-aws-gray-ash'
            }
          >
            {props.bot.title}
          </span>
        </div>
        {props.bot.description ? (
          <div className="mt-1 overflow-hidden text-ellipsis text-xs dark:text-aws-gray-light">
            {props.bot.available
              ? props.bot.description
              : t('bot.label.notAvailable')}
          </div>
        ) : (
          <div className="mt-1 overflow-hidden text-ellipsis text-xs italic text-aws-gray-french dark:text-aws-gray-ash">
            {t('bot.label.noDescription')}
          </div>
        )}
      </div>

      <div className="absolute right-0 flex h-full justify-between">
        <div className="w-10 bg-gradient-to-r from-transparent to-aws-white-smoke dark:to-aws-black-graphite"></div>
        <div className="flex items-center gap-2 bg-aws-white-smoke dark:bg-aws-black-graphite dark:text-aws-gray-light pl-2">
          {props.children}
        </div>
      </div>
    </div>
  );
};

export default ListItemBot;
