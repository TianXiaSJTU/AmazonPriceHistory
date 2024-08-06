from typing import Literal
from utils.Action import Action,ActionParser
from utils.ColoredPrint import color
from api_setting import api_pool,vllmApi

class ActionNarrator:
    def __init__(self, role:Literal['buyer','seller'],
                 method:str,
                 inventory_public_list:str='',
                 showNarrator:bool=False # Present intermediate information of Narrator
                 ):

        self.parser = ActionParser()
        self.role = role
        self.method = method
        self.inventory_public_list = inventory_public_list
        self.showNarrator = showNarrator
        self.PROMPTS = [
# system prompt user instruction
"""
You are good at business negotiating. You can fully understand the meaning of the Actions.
Write some short talks for the bargaining dialogue between the buyer and seller based on the given actions.
You should generate authentic and diverse sentences, avoiding repetition of sentences that have already appeared in the dialogue.
Speak concisely and cut to the chase. The talks must align with the intention of the corresponding Action.

Action: one of the limited actions that define your actual intention. The type of an Action must be one of "[BUY],[SELL],[REJECT],[DEAL],[QUIT]".
1. '[BUY] $M (N codename_1)' if you wish to offer the seller $M to purchase N items of the product with the codename "codename_1".
2. '[SELL] $M (N codename_1)' if you want to propose selling N items of the product with the codename "codename_1" to the buyer for $M or you propose a new discounted offer $M for N codename_1 to the buyer.
3. '[REJECT]' if you choose to reject the other side's offer and await a new offer from the seller.
4. '[DEAL] $M (N codename_1)' if you finally agree on a former offer proposed by the seller to exchange N items of the product with the codename "codename_1" for $M. Keep in mind that this action will immediately end the conversation and close the deal. You should make sure both sides have agreed on this price.
5. '[QUIT]' if you believe that a mutually acceptable deal cannot be reached. This action will immediately end the conversation.

Given Dialogue, Final Role and Final Action, generate the corresponding sentences for the Final Role and Final Action.
Utilize the information from the Inventory List. Don't involve products that are not in the actions. Focus on the specific product in the Final Action.

Response format: Repeat given Final Action and Final Role, and then generate reasonable sentences. For example:

Final Role: "BUYER"
Final Action: "[REJECT]"
Sentences: "I can't afford that price."
""".strip(),

# buyer one-shot demo (user)
"""
Inventory List:
Product1 (codename: charger_1)
Title: "Verizon Car Charger with Dual Output Micro USB and LED Light"
Description: "Charge two devices simultaneously on the go. This vehicle charger with an additional USB port delivers enough power to charge two devices at once. The push-button activated LED connector light means no more fumbling in the dark trying to connect your device. Auto Detect IC Technology automatically detects the device type and its specific charging needs for improved compatibility. And the built-in indicator light illuminates red to let you know the charger is receiving power and the power socket is working properly."
Available Quantity: 1
Listing Price: $10 per item

Dialogue:
"[BUY] $5 (1 charger)": "BUYER: Hi, not sure if the charger would work for my car. Can you sell it to me for $5?",
"[SELL] $8 (1 charger)": "SELLER: I think the lowest I would want to go is 8. ",
"[BUY] $6 (1 charger)": "BUYER: How about $6 and I pick it up myself? It'll save you shipping to me.",
"[SELL] $7 (1 charger)": "SELLER: At least $7.",

Final Role: "BUYER"
Final Action: "[DEAL] $7 (1 charger)"
""".strip(),

# one-shot demo (assistant)
"""
Final Role: "BUYER"
Final Action: "[DEAL] $7 (1 charger)"
Sentences: "Eh, fine. Deal, $7, here you are."
""".strip(),

# request template
"""
{inventory}

Dialogue:
{action_and_text}

Final Role: "{role}"
Final Action: "{final_action}"
""".strip()]

    
    def speak(self,action:Action,history,temperature=0):
        # history list is [{role,talk,action}]

        dialogue = ''
        for i in history:
            dialogue += f'"{i["action"]}": "{i["role"].upper()}: {i["talk"]}",\n'
        # dialogue += last_action_string
        messages = [
            {'role':'system', 'content':self.PROMPTS[0]},
            {'role':'user', 'content':self.PROMPTS[1]},
            {'role':'assistant', 'content':self.PROMPTS[2]},
            {'role':'user', 'content':self.PROMPTS[3].format(
                inventory = self.inventory_public_list,
                action_and_text = dialogue,
                role = self.role.upper(),
                final_action = str(action)
            )},
        ]

        for _ in range(3):
            response = self.request(messages,self.method,temperature=temperature)
            if self.showNarrator:
                print(color(messages,'GREEN'))
                print(color("action2text response:\n"+response,'YELLOW'))

            for line in response.strip().splitlines()[::-1]:
                if 'Sentences: "' in line:
                    return line.split('Sentences: "')[-1].strip().removesuffix('"')

        raise RuntimeError(f"Narrator action2text error on: {action}")
    
    def request(self,messages,method,temperature,max_tokens=500):
        if 'gpt' in method:
            model_name = "gpt-3.5-turbo-1106"
            # don't use stream
            return api_pool.ChatCompletion(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        else:
            return vllmApi.ChatCompletion(method,messages,tokens=max_tokens,temperature=temperature)
