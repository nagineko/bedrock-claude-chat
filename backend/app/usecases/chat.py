import logging
from copy import deepcopy
from typing import Literal

from app.agents.agent import AgentRunner
from app.agents.tools.knowledge import create_knowledge_tool
from app.agents.utils import get_tool_by_name
from app.bedrock import (
    calculate_price,
    call_converse_api,
    compose_args_for_converse_api,
)
from app.prompt import build_rag_prompt
from app.repositories.conversation import (
    RecordNotFoundError,
    find_conversation_by_id,
    store_conversation,
)
from app.repositories.custom_bot import find_alias_by_id, store_alias
from app.repositories.models.conversation import (
    ChunkModel,
    ContentModel,
    ConversationModel,
    MessageModel,
)
from app.repositories.models.custom_bot import (
    BotAliasModel,
    BotModel,
    ConversationQuickStarterModel,
)
from app.routes.schemas.conversation import (
    AgentMessage,
    ChatInput,
    ChatOutput,
    Chunk,
    Content,
    Conversation,
    FeedbackOutput,
    MessageOutput,
    RelatedDocumentsOutput,
    type_model_name,
)
from app.usecases.bot import fetch_bot, modify_bot_last_used_time
from app.utils import get_current_time, is_running_on_lambda
from app.vector_search import (
    SearchResult,
    filter_used_results,
    get_source_link,
    search_related_docs,
    to_guardrails_grounding_source,
)
from ulid import ULID

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def prepare_conversation(
    user_id: str,
    chat_input: ChatInput,
) -> tuple[str, ConversationModel, BotModel | None]:
    current_time = get_current_time()
    bot = None

    try:
        # Fetch existing conversation
        conversation = find_conversation_by_id(user_id, chat_input.conversation_id)
        logger.info(f"Found conversation: {conversation}")
        parent_id = chat_input.message.parent_message_id
        if chat_input.message.parent_message_id == "system" and chat_input.bot_id:
            # The case editing first user message and use bot
            parent_id = "instruction"
        elif chat_input.message.parent_message_id is None:
            parent_id = conversation.last_message_id
        if chat_input.bot_id:
            logger.info("Bot id is provided. Fetching bot.")
            owned, bot = fetch_bot(user_id, chat_input.bot_id)
    except RecordNotFoundError:
        # The case for new conversation. Note that editing first user message is not considered as new conversation.
        logger.info(
            f"No conversation found with id: {chat_input.conversation_id}. Creating new conversation."
        )

        initial_message_map = {
            # Dummy system message, which is used for root node of the message tree.
            "system": MessageModel(
                role="system",
                content=[
                    ContentModel(
                        content_type="text",
                        media_type=None,
                        body="",
                        file_name=None,
                    )
                ],
                model=chat_input.message.model,
                children=[],
                parent=None,
                create_time=current_time,
                feedback=None,
                used_chunks=None,
                thinking_log=None,
            )
        }
        parent_id = "system"
        if chat_input.bot_id:
            logger.info("Bot id is provided. Fetching bot.")
            parent_id = "instruction"
            # Fetch bot and append instruction
            owned, bot = fetch_bot(user_id, chat_input.bot_id)
            initial_message_map["instruction"] = MessageModel(
                role="instruction",
                content=[
                    ContentModel(
                        content_type="text",
                        media_type=None,
                        body=bot.instruction,
                        file_name=None,
                    )
                ],
                model=chat_input.message.model,
                children=[],
                parent="system",
                create_time=current_time,
                feedback=None,
                used_chunks=None,
                thinking_log=None,
            )
            initial_message_map["system"].children.append("instruction")

            if not owned:
                try:
                    # Check alias is already created
                    find_alias_by_id(user_id, chat_input.bot_id)
                except RecordNotFoundError:
                    logger.info(
                        "Bot is not owned by the user. Creating alias to shared bot."
                    )
                    # Create alias item
                    store_alias(
                        user_id,
                        BotAliasModel(
                            id=bot.id,
                            title=bot.title,
                            description=bot.description,
                            original_bot_id=chat_input.bot_id,
                            create_time=current_time,
                            last_used_time=current_time,
                            is_pinned=False,
                            sync_status=bot.sync_status,
                            has_knowledge=bot.has_knowledge(),
                            has_agent=bot.is_agent_enabled(),
                            conversation_quick_starters=(
                                []
                                if bot.conversation_quick_starters is None
                                else [
                                    ConversationQuickStarterModel(
                                        title=starter.title,
                                        example=starter.example,
                                    )
                                    for starter in bot.conversation_quick_starters
                                ]
                            ),
                            model_activate=bot.model_activate,
                        ),
                    )

        # Create new conversation
        conversation = ConversationModel(
            id=chat_input.conversation_id,
            title="New conversation",
            total_price=0.0,
            create_time=current_time,
            message_map=initial_message_map,
            last_message_id="",
            bot_id=chat_input.bot_id,
            should_continue=False,
        )

    # Append user chat input to the conversation
    if chat_input.message.message_id:
        message_id = chat_input.message.message_id
    else:
        message_id = str(ULID())
    # If the "Generate continue" button is pressed, a new_message is not generated.
    if not chat_input.continue_generate:
        new_message = MessageModel(
            role=chat_input.message.role,
            content=[
                ContentModel(
                    content_type=c.content_type,
                    media_type=c.media_type,
                    body=c.body,
                    file_name=c.file_name,
                )
                for c in chat_input.message.content
            ],
            model=chat_input.message.model,
            children=[],
            parent=parent_id,
            create_time=current_time,
            feedback=None,
            used_chunks=None,
            thinking_log=None,
        )
        conversation.message_map[message_id] = new_message
        conversation.message_map[parent_id].children.append(message_id)  # type: ignore

    return (message_id, conversation, bot)


def trace_to_root(
    node_id: str | None, message_map: dict[str, MessageModel]
) -> list[MessageModel]:
    """Trace message map from leaf node to root node."""
    result = []
    if not node_id or node_id == "system":
        node_id = "instruction" if "instruction" in message_map else "system"

    current_node = message_map.get(node_id)
    while current_node:
        result.append(current_node)
        parent_id = current_node.parent
        if parent_id is None:
            break
        current_node = message_map.get(parent_id)

    return result[::-1]


def insert_knowledge(
    conversation: ConversationModel,
    search_results: list[SearchResult],
    display_citation: bool = True,
) -> ConversationModel:
    """Insert knowledge to the conversation."""
    if len(search_results) == 0:
        return conversation

    inserted_prompt = build_rag_prompt(conversation, search_results, display_citation)
    logger.info(f"Inserted prompt: {inserted_prompt}")

    conversation_with_context = deepcopy(conversation)
    conversation_with_context.message_map["instruction"].content[
        0
    ].body = inserted_prompt

    return conversation_with_context


def chat(user_id: str, chat_input: ChatInput) -> ChatOutput:
    user_msg_id, conversation, bot = prepare_conversation(user_id, chat_input)
    used_chunks = None
    price = 0.0
    thinking_log = None

    if bot and bot.is_agent_enabled():
        logger.info("Bot has agent tools. Using agent for response.")
        tools = [get_tool_by_name(t.name) for t in bot.agent.tools]

        if bot.has_knowledge():
            # Add knowledge tool
            knowledge_tool = create_knowledge_tool(bot, chat_input.message.model)
            tools.append(knowledge_tool)

        runner = AgentRunner(
            bot=bot,
            tools=tools,
            model=chat_input.message.model,
            on_thinking=None,
            on_tool_result=None,
            on_stop=None,
        )
        message_map = conversation.message_map
        messages = trace_to_root(
            node_id=conversation.message_map[user_msg_id].parent,
            message_map=message_map,
        )
        messages.append(chat_input.message)  # type: ignore
        result = runner.run(messages)
        reply_txt = result.last_response["output"]["message"]["content"][0].get(
            "text", ""
        )
        price = result.price
        thinking_log = result.thinking_conversation

        # Agent does not support continued generation
        conversation.should_continue = False
    else:
        message_map = conversation.message_map
        search_results = []
        if bot and bot.has_knowledge() and is_running_on_lambda():
            # NOTE: `is_running_on_lambda`is a workaround for local testing due to no postgres mock.
            # Fetch most related documents from vector store
            # NOTE: Currently embedding not support multi-modal. For now, use the last content.
            query: str = conversation.message_map[user_msg_id].content[-1].body  # type: ignore[assignment]

            search_results = search_related_docs(bot=bot, query=query)
            logger.info(f"Search results from vector store: {search_results}")

            # Insert contexts to instruction
            conversation_with_context = insert_knowledge(
                conversation,
                search_results,
                display_citation=bot.display_retrieved_chunks,
            )
            message_map = conversation_with_context.message_map

        messages = trace_to_root(
            node_id=conversation.message_map[user_msg_id].parent,
            message_map=message_map,
        )

        if not chat_input.continue_generate:
            messages.append(MessageModel.from_message_input(chat_input.message))

        # Guardrails
        guardrail = bot.bedrock_guardrails if bot else None
        grounding_source = None
        if guardrail and guardrail.is_guardrail_enabled:
            grounding_source = to_guardrails_grounding_source(search_results)

        # Create payload to invoke Bedrock
        args = compose_args_for_converse_api(
            messages=messages,
            model=chat_input.message.model,
            instruction=(
                message_map["instruction"].content[0].body
                if "instruction" in message_map
                else None  # type: ignore[union-attr]
            ),
            generation_params=(bot.generation_params if bot else None),
            grounding_source=grounding_source,
            guardrail=guardrail,
        )
        converse_response = call_converse_api(args)
        reply_txt = converse_response["output"]["message"]["content"][0].get("text", "")
        reply_txt = reply_txt.rstrip()

        # Used chunks for RAG generation
        if bot and bot.display_retrieved_chunks and is_running_on_lambda():
            if len(search_results) > 0:
                used_chunks = []
                for r in filter_used_results(reply_txt, search_results):
                    content_type, source_link = get_source_link(r.source)
                    used_chunks.append(
                        ChunkModel(
                            content=r.content,
                            content_type=content_type,
                            source=source_link,
                            rank=r.rank,
                        )
                    )

        input_tokens = converse_response["usage"]["inputTokens"]
        output_tokens = converse_response["usage"]["outputTokens"]

        price = calculate_price(chat_input.message.model, input_tokens, output_tokens)
        # Published API does not support continued generation
        conversation.should_continue = False

    # Issue id for new assistant message
    assistant_msg_id = str(ULID())
    # Append bedrock output to the existing conversation
    message = MessageModel(
        role="assistant",
        content=[
            ContentModel(
                content_type="text", body=reply_txt, media_type=None, file_name=None
            )
        ],
        model=chat_input.message.model,
        children=[],
        parent=user_msg_id,
        create_time=get_current_time(),
        feedback=None,
        used_chunks=used_chunks,
        thinking_log=thinking_log,
    )

    if chat_input.continue_generate:
        conversation.message_map[conversation.last_message_id].content[
            0
        ].body += reply_txt  # type: ignore[union-attr]
    else:
        conversation.message_map[assistant_msg_id] = message

        # Append children to parent
        conversation.message_map[user_msg_id].children.append(assistant_msg_id)
        conversation.last_message_id = assistant_msg_id

    conversation.total_price += price

    # Store updated conversation
    store_conversation(user_id, conversation)
    # Update bot last used time
    if chat_input.bot_id:
        logger.info("Bot id is provided. Updating bot last used time.")
        # Update bot last used time
        modify_bot_last_used_time(user_id, chat_input.bot_id)

    output = ChatOutput(
        conversation_id=conversation.id,
        create_time=conversation.create_time,
        message=MessageOutput(
            role=message.role,
            content=[
                Content(
                    content_type=c.content_type,
                    body=c.body,
                    media_type=c.media_type,
                    file_name=None,
                )
                for c in message.content
            ],
            model=message.model,
            children=message.children,
            parent=message.parent,
            feedback=None,
            used_chunks=(
                [
                    Chunk(
                        content=c.content,
                        content_type=c.content_type,
                        source=c.source,
                        rank=c.rank,
                    )
                    for c in message.used_chunks
                ]
                if message.used_chunks
                else None
            ),
            thinking_log=(
                [AgentMessage.from_model(m) for m in message.thinking_log]
                if message.thinking_log
                else None
            ),
        ),
        bot_id=conversation.bot_id,
    )

    return output


def propose_conversation_title(
    user_id: str,
    conversation_id: str,
    model: type_model_name = "claude-v3-haiku",
) -> str:
    PROMPT = """Reading the conversation above, what is the appropriate title for the conversation? When answering the title, please follow the rules below:
<rules>
- Title length must be from 15 to 20 characters.
- Prefer more specific title than general. Your title should always be distinct from others.
- Return the conversation title only. DO NOT include any strings other than the title.
- Title must be in the same language as the conversation.
</rules>
"""
    # Fetch existing conversation
    conversation = find_conversation_by_id(user_id, conversation_id)

    messages = trace_to_root(
        node_id=conversation.last_message_id,
        message_map=conversation.message_map,
    )

    # Append message to generate title
    new_message = MessageModel(
        role="user",
        content=[
            ContentModel(
                content_type="text",
                body=PROMPT,
                media_type=None,
                file_name=None,
            )
        ],
        model=model,
        children=[],
        parent=conversation.last_message_id,
        create_time=get_current_time(),
        feedback=None,
        used_chunks=None,
        thinking_log=None,
    )
    messages.append(new_message)

    # Invoke Bedrock
    args = compose_args_for_converse_api(
        messages=messages,
        model=model,
    )
    response = call_converse_api(args)
    reply_txt = response["output"]["message"]["content"][0].get("text", "")

    return reply_txt


def fetch_conversation(user_id: str, conversation_id: str) -> Conversation:
    conversation = find_conversation_by_id(user_id, conversation_id)

    message_map = {
        message_id: MessageOutput(
            role=message.role,
            content=[
                Content(
                    content_type=c.content_type,
                    body=c.body,
                    media_type=c.media_type,
                    file_name=c.file_name,
                )
                for c in message.content
            ],
            model=message.model,
            children=message.children,
            parent=message.parent,
            feedback=(
                FeedbackOutput(
                    thumbs_up=message.feedback.thumbs_up,
                    category=message.feedback.category,
                    comment=message.feedback.comment,
                )
                if message.feedback
                else None
            ),
            used_chunks=(
                [
                    Chunk(
                        content=c.content,
                        content_type=c.content_type,
                        source=c.source,
                        rank=c.rank,
                    )
                    for c in message.used_chunks
                ]
                if message.used_chunks
                else None
            ),
            thinking_log=(
                [AgentMessage.from_model(m) for m in message.thinking_log]
                if message.thinking_log
                else None
            ),
        )
        for message_id, message in conversation.message_map.items()
    }
    # Omit instruction
    if "instruction" in message_map:
        for c in message_map["instruction"].children:
            message_map[c].parent = "system"
        message_map["system"].children = message_map["instruction"].children

        del message_map["instruction"]

    output = Conversation(
        id=conversation_id,
        title=conversation.title,
        create_time=conversation.create_time,
        last_message_id=conversation.last_message_id,
        message_map=message_map,
        bot_id=conversation.bot_id,
        should_continue=conversation.should_continue,
    )
    return output


def fetch_related_documents(
    user_id: str, chat_input: ChatInput
) -> list[RelatedDocumentsOutput] | None:
    """Retrieve related documents from vector store.
    If `display_retrieved_chunks` is disabled, return None.
    """
    if not chat_input.bot_id:
        return []

    _, bot = fetch_bot(user_id, chat_input.bot_id)
    if not bot.display_retrieved_chunks:
        return None

    query: str = chat_input.message.content[-1].body  # type: ignore[assignment]
    chunks = search_related_docs(bot=bot, query=query)

    documents = []
    for chunk in chunks:
        content_type, source_link = get_source_link(chunk.source)
        documents.append(
            RelatedDocumentsOutput(
                chunk_body=chunk.content,
                content_type=content_type,
                source_link=source_link,
                rank=chunk.rank,
            )
        )
    return documents
