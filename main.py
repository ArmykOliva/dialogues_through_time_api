import uvicorn, os, uuid, asyncio, redis,json
import openai
from fastapi import FastAPI, Query,Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from dataclasses import dataclass, field
from time import sleep
from pydantic import BaseModel
from traceback import print_exc
from dataclasses import dataclass, field, asdict

from prompts import *
load_dotenv()

TROLLING_LIMIT = 5

REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
openai.api_key = os.getenv("API_KEY")

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Connect to Redis
r = redis.StrictRedis(host='msai.redis.cache.windows.net', port=6380, password=REDIS_PASSWORD, ssl=True)

#this is a class that stores the whole state of the game.
@dataclass
class ChatState:
    processing: bool = False #if openai is currently replying, dont allow new requests
    current_state: str = "introduction" #current state of the conversation flow json
    current_scene: str = "entity" #the current person to talk to = scene in unity that should be active
    previous_scene: str = "" #the previous scene
    user_msg: str = "" #the last message the user sent
    ai_msg: str = "" #the last message the ai sent
    system_msg: str = "" 
    memory: str = "" #the memory of the ai about the player
    jazyk: str = "EN" 
    chat_history: list = field(default_factory=list) #current conversation history
    previous_chat_history: list = field(default_factory=list) #the chat history from last scene
    render_chat_history: list = field(default_factory=list) #chat history but where user messages are without the prompt templastes. for rendering in unity
    generated_states: dict = field(default_factory=dict) #whne the entity_ai needs to generate states in the flow itself for the testing questions
    trolling: int = 0
    end_reason: str = "" #the reason the conversation ended, for example "end_conversation" (will start scene change), "needs_input" (stop generation, wait for user message), "trolling" (the user didnt answer), "forward" (the ai is still going to generate)
    print_response: bool = True
    streaming: bool = False # just for the unity client to know that streaming stopped when he sees this

    def reset_state(state):
        default_state = ChatState()
        return ChatState(**asdict(default_state))


    def to_json(self):
        return json.dumps(self.__dict__)

    @staticmethod
    def from_json(json_data):
        data = json.loads(json_data)
        return ChatState(**data)
    
# Function to retrieve or initialize chat state
def get_chat_data(unique_id):
    json_data = r.get(unique_id)
    if json_data:
        return ChatState.from_json(json_data)
    else:
        return None
    
def create_chat_data(unique_id):
    chat_state = ChatState()
    set_chat_state(unique_id, chat_state)
    return chat_state 
    
def set_chat_state(unique_id, chat_state):
    r.set(unique_id, chat_state.to_json())

##gpt calling
async def gpt_call(messages,temperature=0.4):
    while True:
        try:
            response = ""
            for chunk in openai.ChatCompletion.create(
                #engine="gpt-4",
                model="gpt-4-1106-preview",
                messages = messages,
                temperature=temperature,
                max_tokens=2000,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,
                stream=True,
            ):
                if (chunk["choices"]):
                    content = chunk["choices"][0].get("delta", {}).get("content")
                    if content is not None:
                        response += content
                        yield response
                        await asyncio.sleep(0.00001)
            break
        except openai.error.RateLimitError:
            print("Rate limit exceeded, waiting")
            print_exc()
            sleep(10)
        except openai.error.InvalidRequestError:
            print_exc()
            print("Content policy violation")
            yield None
            break

#chat flow
async def handle_chat(c:ChatState,request_body:dict):
    usr_msg_sent = request_body.get("user_msg", "")
    if ("end_conversation" in request_body and request_body["end_conversation"]):
        c.end_reason = "end_conversation"
        c.previous_chat_history = c.chat_history.copy()
        c.chat_history = []
        c.ai_msg = ""
        c.user_msg = ""
        c.current_state = "introduction"
        c.previous_scene = c.current_scene
        c.current_scene = CONFIGS[c.current_scene]["exit_scene"]
        return

    #get flow
    print(c.current_state)
    flow = FLOWS[c.current_scene][c.current_state]
    c.system_msg = SYSTEM_MSGS[c.current_scene] + "\n" + c.memory
    if (c.jazyk): c.system_msg += "\n" + LANGUAGES[c.jazyk]

    #trolling too much
    if ("trolling_up" in flow):
        c.trolling += max(0,flow["trolling_up"])

    #if (c.trolling >= TROLLING_LIMIT):
    #    print("Trolling too much. BYE. DONT COME BACK.")
    #    c.ai_msg = "Sorry, we will have to start over..."
    #    yield
    #    await asyncio.sleep(2)
    #    c.end_reason = "trolling"
    #
    #    return

    #get input
    needs_input = "needs_user_input" in flow and flow["needs_user_input"]
    if (needs_input and c.end_reason != "needs_input"):
        c.end_reason = "needs_input"
        return
    else:
        print("got new input",usr_msg_sent)
        c.user_msg = usr_msg_sent
    
    #get gpt response
    c.print_response = "print_response" in flow and flow["print_response"]
    prompt = flow["prompt"].replace("{{user_msg}}",c.user_msg).replace("{{ai_msg}}",c.ai_msg)
    c.ai_msg = ""

    #handle chat send
    system_msg_dict = {"role":"system","content":c.system_msg}
    user_msg_dict = {"role":"user","content":prompt}
    chat_history_dict = c.chat_history.copy()
    chat_history_dict.append(user_msg_dict)

    async for response in gpt_call([system_msg_dict] + chat_history_dict):        
        c.ai_msg = response
        yield

    if (not response):
        print("response whas null")
        raise Exception("Response was null")

    #save to chat history
    if ("save_prompt" in flow and flow["save_prompt"]):
        c.chat_history.append({"role":"user","content":prompt})

    if ("save_ai_msg" in flow and flow["save_ai_msg"]):
        c.chat_history.append({"role":"assistant","content":response})

    #save render chat history
    if ("print_response" in flow and flow["print_response"]):
        c.render_chat_history.append({"role":"assistant","content":response})

    #save extracted ai thing to memory
    if ("permanent_memory" in flow):
        c.memory += f"\n{flow['permanent_memory'].replace('{{ai_msg}}',response)}"

    #end conversation - scene will change, so clear history etc and load new character
    #when end conversation in flow there must also be a scene change
    if ("end_conversation" in flow and flow["end_conversation"]):
        c.end_reason = "end_conversation"
        c.previous_chat_history = c.chat_history.copy()
        c.chat_history = []
        c.render_chat_history = []
        c.ai_msg = ""
        c.user_msg = ""
        c.previous_scene = c.current_scene
        c.current_state = "introduction"
        c.current_scene = flow["scene_change"]
        return
    
    #get next state
    for key, value in flow["choices"].items():
        if (len(key) == 0 or key.lower() in response.lower()):
            c.current_state = value
            break

    c.end_reason = "forward"

## get unique id for saving
@app.get("/get_unique_id")
def get_unique_id():
    unique_id = str(uuid.uuid4())  # Generate a random UUID
    create_chat_data(unique_id)
    return {"id": unique_id}

## Stream the response of gpt
async def stream_generator(request_body:dict):
    unique_id = request_body.get("unique_id", None)
    
    if (not unique_id):
        raise Exception("Unique id is none")

    chat_state = get_chat_data(unique_id)
    if (chat_state.processing):
        print("processing and accessing again????")
        #raise Exception("processing and got a streaming call")
    
    try:
        #init
        chat_state.processing = True
        set_chat_state(unique_id, chat_state)

        #set chatrender user msg
        chat_state.render_chat_history.append({"role":"user","content":request_body.get("user_msg", "")})
        
        i = 0
        while (i == 0 or chat_state.end_reason == "" or chat_state.end_reason == "forward"):
            i += 1
            async for response in handle_chat(chat_state,request_body):
                response_data = json.dumps({"ai_speaking": chat_state.ai_msg})
                print(response_data) #TODO: fix bug where when entity says two messages at a time, it then first first shows firs buubble, then second and then both at a time
                if (chat_state.print_response):
                    yield f"data: {response_data}\n\n"  # Ensure SSE format


        chat_state.processing = False
        set_chat_state(unique_id, chat_state)
        response_data = chat_state.to_json()
        await asyncio.sleep(0.5)
        yield response_data.encode('utf-8') 

        #reset chat if trolling
        if (chat_state.end_reason == "trolling"):
            chat_state.reset_state()

    #reset processing
    except Exception as e:
        chat_state.processing = False
        set_chat_state(unique_id, chat_state)
        print("exception")
        print_exc()
        raise e
        
class UserMessage(BaseModel):
    user_msg: str
        
@app.get("/chat")
async def read_stream(unique_id: str = Query(None), user_msg: str = Query(None)):
    request_body = {'unique_id': unique_id, 'user_msg': user_msg}
    return StreamingResponse(stream_generator(request_body), media_type="text/event-stream")

async def test_stream_debug():
    for i in range(5):
        yield f"data: {i}\n\n"
        await asyncio.sleep(1)

@app.get("/test_stream")
async def test_stream():
    return StreamingResponse(test_stream_debug(),media_type="text/event-stream")

@app.post("/test_stream_post")
async def test_stream_post():
    return StreamingResponse(test_stream(),media_type="text/event-stream")

@app.get("/chat_history/{unique_id}")
def get_chat_history(unique_id: str):
    chat_state = get_chat_data(unique_id)
    return chat_state.__dict__ if chat_state else None

if __name__ == "__main__":
    #ts
    port = os.environ.get("PORT",80)
    uvicorn.run("main:app",host="0.0.0.0",port=port,reload=False)