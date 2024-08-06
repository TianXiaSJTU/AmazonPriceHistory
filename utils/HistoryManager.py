import jsonlines
import time
import sys
from utils.ColoredPrint import color

class HistoryManager:
    """
    Responsible for saving and loading historical message records
    """
    def __init__(self,system_prompt,savepath=None):
        if savepath is None:
            self.filepath = sys.path[0]
        else:
            self.filepath = savepath

        self.history = [{'role': 'system', 'content': system_prompt}]
    
    def add_reply(self,reply):
        reply_message = {'role': 'assistant', 'content': reply}
        self.history.append(reply_message)

    def add_user_text(self,user_text):
        user_message = {'role': 'user', 'content': user_text}
        self.history.append(user_message)

    def load_history(self,history):
        self.history = history

    def clear_history(self):
        self.history.clear()

    def export_history(self):
        return self.history
    
    def show_history(self,history=None):
        if history is None:
            history = self.history
        print('History:')
        for message in history:
            if 'name' in message:
                role = message['name']
            else:
                role = message['role']
            if 'user' in role:
                content = color(message['content'],"BLUE")
            elif 'assistant' in role:
                content = color(message['content'],"RED")
            else:
                content = message['content']
            print(f'{role}|{content}')
 
    def save_history_jsonl(self,memo:str=''):
        # JSONLINES defaults to UTF 8. Use \n line breaks to split the object
        all_info = {
            "memo":memo,
            "time":time.asctime(),
        }
        history =  {'info':all_info,'history':self.history}
        with jsonlines.open(self.filepath,'a') as writer:
            writer.write(history)

