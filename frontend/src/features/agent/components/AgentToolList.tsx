import React from 'react';
import ToolCard from './ToolCard';
import ChatMessageMarkdown from '../../../components/ChatMessageMarkdown';
import { AgentToolsProps } from '../xstates/agentThink';
import { useTranslation } from 'react-i18next';
import { PiCircleNotchBold } from 'react-icons/pi';
import { RelatedDocument } from '../../../@types/conversation';

type AgentToolListProps = {
  messageId: string;
  tools: AgentToolsProps;
  relatedDocuments?: RelatedDocument[];
};

const AgentToolList: React.FC<AgentToolListProps> = ({messageId, tools, relatedDocuments}) => {
  const { t } = useTranslation();
  const isRunning = (
    Object.keys(tools.tools).length === 0 ||
    Object.values(tools.tools).some(tool => tool.status === 'running')
  );
  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col rounded border border-aws-gray-french bg-aws-white-smoke dark:bg-aws-black-graphite text-aws-blue-navy/80 dark:text-aws-gray-light/80">
      {(isRunning || tools.thought) && (
        <div className="flex items-center border-b border-aws-gray-french p-2 last:border-b-0">
          {isRunning && <PiCircleNotchBold className="mr-2 animate-spin" />}
          {tools.thought ? (
            <ChatMessageMarkdown
              messageId={messageId}
              relatedDocuments={relatedDocuments}
            >
              {tools.thought}
            </ChatMessageMarkdown>
          ) : t('agent.progress.label')}
        </div>
      )}

      {Object.entries(tools.tools).map(([toolUseId, toolUse]) => (
        <ToolCard
          className=" border-b border-aws-gray-french last:border-b-0"
          key={toolUseId}
          toolUseId={toolUseId}
          name={toolUse.name}
          status={toolUse.status}
          input={toolUse.input}
          resultContents={toolUse.resultContents}
          relatedDocuments={toolUse.relatedDocuments}
        />
      ))}
    </div>
  );
};

export default AgentToolList;
