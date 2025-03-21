# Standard library imports
import os
from typing import Dict, List, Any, Optional

# Third-party imports
import nest_asyncio
from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    String,
    Integer,
    insert
)

# LlamaIndex imports
from llama_index.core import SQLDatabase, Settings
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.core.tools import QueryEngineTool, BaseTool
from llama_index.core.llms import ChatMessage
from llama_index.core.llms.llm import ToolSelection, LLM
from llama_index.llms.openai import OpenAI

from dotenv import load_dotenv
from termcolor import colored
import sys

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PHOENIX_API_KEY = os.getenv('PHOENIX_API_KEY')
LLAMA_CLOUD_API_KEY = os.getenv('LLAMA_CLOUD_API_KEY')

nest_asyncio.apply()

# # setup Arize Phoenix for logging/observability

# import llama_index.core

# import os

# PHOENIX_API_KEY = "<phoenix_api_key>"
# os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"api_key={PHOENIX_API_KEY}"
# llama_index.core.set_global_handler(
#     "arize_phoenix", endpoint="https://llamatrace.com/v1/traces"
# )
# setup Arize Phoenix for logging/observability
import llama_index.core

import os

if PHOENIX_API_KEY:
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"api_key={PHOENIX_API_KEY}"
    llama_index.core.set_global_handler(
        "arize_phoenix", endpoint="https://llamatrace.com/v1/traces"
    )

from llama_index.core import SQLDatabase, Settings
from llama_index.llms.openai import OpenAI
from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    String,
    Integer,
)

Settings.llm = OpenAI("gpt-3.5-turbo")

engine = create_engine("sqlite:///:memory:", future=True)
metadata_obj = MetaData()

# create city SQL table
table_name = "city_stats"
city_stats_table = Table(
    table_name,
    metadata_obj,
    Column("city_name", String(16), primary_key=True),
    Column("population", Integer),
    Column("state", String(16), nullable=False),
)

metadata_obj.create_all(engine)

from sqlalchemy import insert

rows = [
    {"city_name": "New York City", "population": 8336000, "state": "New York"},
    {"city_name": "Los Angeles", "population": 3822000, "state": "California"},
    {"city_name": "Chicago", "population": 2665000, "state": "Illinois"},
    {"city_name": "Houston", "population": 2303000, "state": "Texas"},
    {"city_name": "Miami", "population": 449514, "state": "Florida"},
    {"city_name": "Seattle", "population": 749256, "state": "Washington"},
]
for row in rows:
    stmt = insert(city_stats_table).values(**row)
    with engine.begin() as connection:
        cursor = connection.execute(stmt)

with engine.connect() as connection:
    cursor = connection.exec_driver_sql("SELECT * FROM city_stats")
    print(cursor.fetchall())

from llama_index.core.query_engine import NLSQLTableQueryEngine

sql_database = SQLDatabase(engine, include_tables=["city_stats"])
sql_query_engine = NLSQLTableQueryEngine(
    sql_database=sql_database,
    tables=["city_stats"]
)

from llama_index.indices.managed.llama_cloud import LlamaCloudIndex
# pip install llama-index-indices-managed-llama-cloud

index = LlamaCloudIndex(
  name="daily_dose_of_ds", 
  project_name="Default",
  organization_id="d45a9cb3-e1b6-4cf5-88d8-286a9f17fb14",
  api_key="llx-tqRcUXn0SqXedkXoHnjTJks20ZWhzgYIhB6LujxESaJoQfBf"
)

llama_cloud_query_engine = index.as_query_engine()

from llama_index.core.tools import QueryEngineTool

sql_tool = QueryEngineTool.from_defaults(
    query_engine=sql_query_engine,
    description=(
        "Useful for translating a natural language query into a SQL query over"
        " a table containing: city_stats, containing the population/state of"
        " each city located in the USA."
    ),
    name="sql_tool"
)

cities = ["New York City", "Los Angeles", "Chicago", "Houston", "Miami", "Seattle"]
llama_cloud_tool = QueryEngineTool.from_defaults(
    query_engine=llama_cloud_query_engine,
    description=(
        f"Useful for answering semantic questions about certain cities in the US."
    ),
    name="llama_cloud_tool"
)

from typing import Dict, List, Any, Optional

from llama_index.core.tools import BaseTool
from llama_index.core.llms import ChatMessage
from llama_index.core.llms.llm import ToolSelection, LLM
from llama_index.core.workflow import (
    Workflow,
    Event,
    StartEvent,
    StopEvent,
    step,
    Context,
)
from llama_index.core.base.response.schema import Response
from llama_index.core.tools import FunctionTool

class InputEvent(Event):
    """Input event."""

class GatherToolsEvent(Event):
    """Gather Tools Event"""

    tool_calls: Any

class ToolCallEvent(Event):
    """Tool Call event"""

    tool_call: ToolSelection

class ToolCallEventResult(Event):
    """Tool call event result."""

    msg: ChatMessage

class RouterOutputAgentWorkflow(Workflow):
    """Custom router output agent workflow."""

    def __init__(self,
        tools: List[BaseTool],
        timeout: Optional[float] = 10.0,
        disable_validation: bool = False,
        verbose: bool = False,
        llm: Optional[LLM] = None,
        chat_history: Optional[List[ChatMessage]] = None,
    ):
        """Constructor."""

        super().__init__(timeout=timeout, disable_validation=disable_validation, verbose=verbose)

        self.tools: List[BaseTool] = tools
        self.tools_dict: Optional[Dict[str, BaseTool]] = {tool.metadata.name: tool for tool in self.tools}
        self.llm: LLM = llm or OpenAI(temperature=0, model="gpt-3.5-turbo")
        self.chat_history: List[ChatMessage] = chat_history or []
    

    def reset(self) -> None:
        """Resets Chat History"""

        self.chat_history = []

    @step()
    async def prepare_chat(self, ev: StartEvent) -> InputEvent:
        message = ev.get("message")
        if message is None:
            raise ValueError("'message' field is required.")
        
        # add msg to chat history
        chat_history = self.chat_history
        chat_history.append(ChatMessage(role="user", content=message))
        return InputEvent()

    @step()
    async def chat(self, ev: InputEvent) -> GatherToolsEvent | StopEvent:
        """Appends msg to chat history, then gets tool calls."""

        # Put msg into LLM with tools included
        chat_res = await self.llm.achat_with_tools(
            self.tools,
            chat_history=self.chat_history,
            verbose=self._verbose,
            allow_parallel_tool_calls=True
        )
        tool_calls = self.llm.get_tool_calls_from_response(chat_res, error_on_no_tool_call=False)
        
        ai_message = chat_res.message
        self.chat_history.append(ai_message)
        if self._verbose:
            print(f"Chat message: {ai_message.content}")

        # no tool calls, return chat message.
        if not tool_calls:
            return StopEvent(result=ai_message.content)

        return GatherToolsEvent(tool_calls=tool_calls)

    @step(pass_context=True)
    async def dispatch_calls(self, ctx: Context, ev: GatherToolsEvent) -> ToolCallEvent:
        """Dispatches calls."""

        tool_calls = ev.tool_calls
        await ctx.set("num_tool_calls", len(tool_calls))

        # trigger tool call events
        for tool_call in tool_calls:
            ctx.send_event(ToolCallEvent(tool_call=tool_call))
        
        return None
    
    @step()
    async def call_tool(self, ev: ToolCallEvent) -> ToolCallEventResult:
        """Calls tool."""

        tool_call = ev.tool_call

        # get tool ID and function call
        id_ = tool_call.tool_id

        if self._verbose:
            print(f"Calling function {tool_call.tool_name} with msg {tool_call.tool_kwargs}")

        # call function and put result into a chat message
        tool = self.tools_dict[tool_call.tool_name]
        output = await tool.acall(**tool_call.tool_kwargs)
        msg = ChatMessage(
            name=tool_call.tool_name,
            content=str(output),
            role="tool",
            additional_kwargs={
                "tool_call_id": id_,
                "name": tool_call.tool_name
            }
        )

        return ToolCallEventResult(msg=msg)
    
    @step(pass_context=True)
    async def gather(self, ctx: Context, ev: ToolCallEventResult) -> StopEvent | None:
        """Gathers tool calls."""
        # wait for all tool call events to finish.
        tool_events = ctx.collect_events(ev, [ToolCallEventResult] * await ctx.get("num_tool_calls"))
        if not tool_events:
            return None
        
        for tool_event in tool_events:

            self.chat_history.append(tool_event.msg)
        
        # # after all tool calls finish, pass input event back, restart agent loop
        return InputEvent()

# Add this debug function
def debug_print(message, level="info"):
    colors = {
        "info": "cyan",
        "error": "red",
        "success": "green",
        "warning": "yellow"
    }
    print(colored(message, colors.get(level, "white")))

# Modify the OpenAI key setup
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    debug_print("ERROR: OPENAI_API_KEY not found in environment variables!", "error")
    debug_print("Please create a .env file with your OpenAI API key:", "info")
    debug_print("OPENAI_API_KEY=your_openai_api_key_here", "info")
    sys.exit(1)

debug_print(f"Using OpenAI API key: {OPENAI_API_KEY[:6]}...{OPENAI_API_KEY[-4:]}", "info")

# Update the OpenAI settings
debug_print("Initializing OpenAI...", "info")
try:
    Settings.llm = OpenAI(api_key=OPENAI_API_KEY, model="gpt-3.5-turbo")
    debug_print("✅ OpenAI initialized successfully", "success")
except Exception as e:
    debug_print(f"❌ Failed to initialize OpenAI: {str(e)}", "error")
    sys.exit(1)

async def main():
    debug_print("Initializing workflow...", "info")
    wf = RouterOutputAgentWorkflow(tools=[sql_tool, llama_cloud_tool], verbose=True, timeout=120)
    
    try:
        queries = [
            "Which city has the highest population?",
            "What state is Houston located in?",
            "Where is the Space Needle located?",
            "List all of the places to visit in Miami.",
            "How do people in Chicago get around?",
            "What is the historical name of Los Angeles?"
        ]
        
        for query in queries:
            try:
                debug_print(f"\n📝 Processing query: {query}", "info")
                result = await wf.run(message=query)
                debug_print(f"✅ Result: {result}\n", "success")
            except Exception as e:
                debug_print(f"❌ Error processing query '{query}': {str(e)}", "error")
                
    except Exception as e:
        debug_print(f"❌ An error occurred: {str(e)}", "error")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

def validate_api_key(api_key: str) -> bool:
    """Validate OpenAI API key format."""
    if not api_key:
        return False
    # OpenAI API keys start with 'sk-' and are ~51 characters long
    return api_key.startswith('sk-') and len(api_key) > 40

# After load_dotenv()
debug_print("Checking API keys...", "info")

# OpenAI API Key validation
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not validate_api_key(OPENAI_API_KEY):
    debug_print("❌ Invalid OpenAI API key!", "error")
    debug_print("OpenAI API keys should:", "info")
    debug_print("  1. Start with 'sk-'", "info")
    debug_print("  2. Be approximately 51 characters long", "info")
    debug_print("  3. Be obtained from: https://platform.openai.com/api-keys", "info")
    debug_print("\nPlease update your .env file with:", "warning")
    debug_print("OPENAI_API_KEY=sk-...your-key-here...", "warning")
    sys.exit(1)

debug_print(f"✅ Valid OpenAI API key format detected: {OPENAI_API_KEY[:5]}...{OPENAI_API_KEY[-4:]}", "success")