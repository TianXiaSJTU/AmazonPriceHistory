import openai
import time
from queue import Queue
import requests
import json
from utils.format_tokens import *

openai_keys = [
    # FILL HERE
]
api_base_url = "https://api.openai.com/v1"

class API:
    def __init__(self,temperature = 0.0) -> None:
        self.t = temperature
        self.client = openai.OpenAI(api_key='', base_url=api_base_url)
        self.key_queue = Queue()
        for k in openai_keys:
            self.key_queue.put(k)

    def models(self):
        k = self.key_queue.get()
        self.client.api_key = k

        return self.client.models.list().data

    def ChatCompletion(self,model,messages,temperature=None,**kwargs) -> str:
        if temperature == None:
            temperature = self.t
        key = self.key_queue.get()

        retry_count = 3
        retry_interval = 0.5

        errormsg=''
        for _ in range(retry_count):
            try:
                self.client.api_key = key
                response = self.client.chat.completions.create(
                            model=model,
                            messages=messages,
                            temperature=temperature,
                            **kwargs
                        )
                reply = response.choices[0].message.content
                if reply == '':
                    raise ValueError('EMPTY RESPONSE CONTENT')
                # After success request, return the key
                self.key_queue.put(key)
                return reply

            except (openai.RateLimitError,openai.APIError,openai.OpenAIError,openai.PermissionDeniedError) as e:
                if "quota" in e.message or "exceeded" in e.message or "balance" in e.message: # type: ignore
                    # Discard the old one and find a new key
                    errormsg=e
                    with open('RanOutKeys.txt','a') as f:
                        f.write(f'{key}\n')
                    key = self.key_queue.get()
                else:
                    errormsg=e
                    retry_interval *= 5
                    # cool down time
                    time.sleep(retry_interval)
            except (ValueError,Exception) as e:
                errormsg=e
                retry_interval *= 5
                # cool down time
                time.sleep(retry_interval)
        # Repeated retry failed to return the key
        self.key_queue.put(key)
        raise ConnectionError(f"ChatCompletion Retries Failure {key[-5:]}-{errormsg}")

    def dummyChat(self):
        key = self.key_queue.get()
        print(f"Dummy get [{key[-5:]}] at {time.time()}")
        self.key_queue.put(key)

class vllmAPI:
    def __init__(self,temperature = 0.0) -> None:
        self.api_url = "http://localhost:8000/generate"
        self.t = temperature

    def post_http_request(self, prompt: str,
                        api_url: str,
                        tokens:int,
                        t:float,
                        stream: bool = False) -> requests.Response:
        headers = {"User-Agent": "Test Client"}
        pload = {
            "prompt": prompt,
            "n": 1,
            "use_beam_search": False,
            "stop": ["<|im_end|>","</s>","[/INST]","<|user|>","<|assistant|>","<reserved_106>","<reserved_107>"],
            "temperature": t,
            "max_tokens": tokens,
            "stream": stream,
        }
        response = requests.post(api_url, headers=headers, json=pload)
        return response
    
    def ChatCompletion(self, model, messages,temperature=None,tokens=300) -> str:
        if temperature == None:
            temperature = self.t
        # print(f"{prompt}\n", flush=True)
        if isinstance(messages,list) and isinstance(messages[0],dict):
            # prompt = '\n\n'.join([m['content']for m in messages])
            # print(messages)
            if 'yi' in model:
                prompt = format_tokens_yi(dialog=messages)
            elif 'mistral' in model or 'mixtral' in model:
                prompt = format_tokens_mistral(dialog=messages)
            elif 'phi' in model:
                prompt = format_tokens_phi(dialog=messages)
            elif 'chatglm' in model:
                prompt = format_tokens_chatglm(dialog=messages)
            elif 'qwen' in model:
                prompt = format_tokens_qwen(dialog=messages)
            elif 'baichuan2' in model:
                prompt = format_tokens_baichuan(dialog=messages)
            else:
                prompt = format_tokens_llama(dialog=messages)
            # print(prompt)
        else:
            prompt = str(messages)
        # print(f"[USER] {prompt}\n")
        for _ in range(3):
            response = self.post_http_request(prompt, self.api_url, tokens, temperature)
            if response.status_code == 200:
                # Reply is the completion of prompt, so delete the previous prompt in reply.
                reply = json.loads(response.content)["text"][0].removeprefix(prompt).strip()
                # print(f"{color(reply,'YELLOW')}")
                return reply
        raise ConnectionError('SERVER DO NOT RESPOND')


api_pool = API(temperature=0.0)
vllmApi = vllmAPI(temperature=0.0)

if __name__ == '__main__':
    message = [{'role':'system','content':'You are my maid.'},
               {'role':'user','content':'How is the weather today?'},
               {'role':'assistant','content':'A bright sunny day, sir.'},
                {'role':'user','content':'What is my schedule today?'},
               ]
    print(api_pool.ChatCompletion('gpt-3.5-turbo-1106',message, 0.0))

    print(api_pool.ChatCompletion('gpt-4-0125-preview',message, temperature=0.0))
