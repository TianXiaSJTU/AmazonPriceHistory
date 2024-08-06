import os
import threading
import jsonlines
from tqdm import tqdm
from product import Inventory
import BuyerAgent
import SellerAgent
from utils.Action import ActionParser
import time
import re
import traceback

def parseReply(reply:str):
    if not reply:
        raise ValueError('parse Reply got empty reply')

    thought_matches = re.search(r'Thought: (.+)',reply)
    thought = thought_matches.group(1) if thought_matches else ''
    
    talk_matches = re.search(r'Talk: (.+)',reply)
    talk = talk_matches.group(1) if talk_matches else ''
    
    action_matches = re.search(r'Action: (.+)',reply)
    action = action_matches.group(1) if action_matches else ''
    
    message = f"Talk: {talk}\nAction: {action}"
    return thought,talk,action,message
    

class Agent2AgentSession:
    def __init__(self, idx:int, filelock:threading.Lock, inventory:Inventory, savepath:str, 
                 budget_ratio:float, buyer_agent, buyer_model_name, buyer_role, seller_agent, seller_model_name, seller_role, max_turns) -> None:
        """
        The agent determines the underlying method, model_name determines the specific model and version, 
        role determines the strategy/prompt used by the agent, and the default role is buyer/seller
        """

        needs,string = self.shopping_list(inventory,budget_ratio)
        if buyer_agent == 'OGNarratorAgent':
            buyer = BuyerAgent.OGNarratorAgent(buyer_model_name, inventory.public_list(), inventory.catalog(), needs, turns=max_turns,
                                        strategy = buyer_role,
                                        start_factor = 0.5, end_factor = 1, showNarrator=False)
        else:
            buyer = getattr(BuyerAgent, buyer_agent)(buyer_model_name, buyer_role, inventory.public_list(),need=string, turns=max_turns)
        
        seller = getattr(SellerAgent, seller_agent)(seller_model_name, seller_role, inventory.list(), turns=max_turns)
        
        loop = tqdm(range(max_turns),desc=f'{buyer_role}-{seller_role},inv{idx}',ncols=0,leave=False,unit='turn')
        result = self.agents_talk_with_action(buyer, seller, loop, idx, inventory, needs)
        filelock.acquire()
        dirname = os.path.dirname(savepath)
        if not os.path.exists(dirname):
            os.mkdir(dirname)
            print(dirname)
        with jsonlines.open(savepath,'a') as f:
            f.write(result)
        filelock.release()
        
    def isDealOrQuit(self,action_text:str)->str:
        parser = ActionParser()
        try:
            action = parser(action_text)
        except RuntimeError:
            return 'action error'
        
        if action.isDEAL():
            return 'deal'
        elif action.isQUIT():
            return 'quit'
        else:
            return ''

    def shopping_list(self,inventory:Inventory, budget_ratio:float):
        """For BuyerAgent, create a shopping list for the Inventory items and return a dictionary and a string. The dictionary is used to save records, and the string is used to prompt the Agent.
        The bugdet in needs is calculated directly based on the unit price, so it is independent of the quantity. The total budget needs to be multiplied by the quantity.
        """
        needs = list()
        for codename,info in inventory.catalog().items():
            needs.append({'codename':codename,
                        'title':info[0],
                        'quantity':1,
                        'budget':info[2] * budget_ratio})
        # return res
        string = '\n'.join([f"""
codename: {need['codename']}
quantity: {need['quantity']}
budget: ${need['budget']}
""".strip() for need in needs])
        # print(string)
        return needs,string

    def agents_talk_with_action(self,buyer,seller,loop:tqdm, idx, inventory, needs):
        """The main loop"""
        history = []
        errormsg= ''
        # buyer_input_message = 'Talk: Welcome! Buy what you want please.\nAction:  '
        buyer_input_message = ''
        try:
            for step in loop:
                loop.set_postfix_str('buyer thinking')
                raw_text_b = buyer.input(buyer_input_message)
                thought_b, talk_b, action_b, seller_input_message = parseReply(raw_text_b)
                buyer_record = {'turn':step, 'role':'buyer','thought':thought_b, 'talk':talk_b, 'action':action_b,'input_message':buyer_input_message,'raw_text':raw_text_b}
                errormsg = self.isDealOrQuit(action_b)
                if errormsg in ['deal','quit','action error']:
                    errormsg = 'BUYER:'+errormsg
                    history.append([buyer_record])
                    break

                loop.set_postfix_str('seller thinking')
                raw_text_s = seller.input(seller_input_message)
                thought_s, talk_s, action_s, buyer_input_message = parseReply(raw_text_s)
                seller_record = {'turn':step, 'role':'seller','thought':thought_s, 'talk':talk_s, 'action':action_s,'input_message':seller_input_message,'raw_text':raw_text_s}
                
                history.append([buyer_record,seller_record])
                errormsg = self.isDealOrQuit(action_s)
                if errormsg in ['deal','quit','action error']:
                    errormsg = 'SELLER:'+errormsg
                    break

        except KeyboardInterrupt as e:
            # Manual interruption will still save existing records
            print('stop')
        except EOFError as e:
            # Do not saving results
            raise EOFError('ManuallyHalt')
        except RuntimeError as e:

            if loop.postfix == 'buyer thinking':
                errormsg = 'BUYER:'+repr(e)
                if 'Narrator action2text error' not in errormsg:
                    # parser error, still save it in history
                    history.append([buyer_record])
            else:
                errormsg = 'SELLER:'+repr(e)
            
        except Exception as e:
            traceback.print_exc()
            errormsg = repr(e)

        if errormsg == '':
            errormsg = 'turn limit'

        tqdm.write(errormsg)
        return {
                'memo':'', # memo is not used
                'time':time.asctime(),
                'index':idx,
                'errormsg':errormsg,
                'history':history,
                'buyer':str(buyer),
                'seller':str(seller),
                'inv':inventory._catalog(),
                'need':needs,
            }