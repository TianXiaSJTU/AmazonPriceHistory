from api_setting import api_pool,vllmApi
from utils.Action import Action,ActionParser
from utils.HistoryManager import HistoryManager
from utils.ColoredPrint import color
from time import asctime

class SellerAgent:
    _SELLER_SYSTEM_PROMPT = """
You are a seller looking forward to selling things on your Inventory List to me, the buyer.
Your task is to bargain with the buyer and reach a deal with the price as high as possible in limited turns.
You can only sell things that are on. the Inventory List. Use the codename of the product, instead of the title.
You have access to private information: the cost price of each product in the Inventory List, and do not disclose the real cost to the buyer.
You should only agree on a deal when the selling price is higher than the cost, otherwise, you should quit negotiating.

Your Reply should include 3 parts: Thought, Talk, and Action.
Thought: your inner strategic thinking of this bargaining session;
Talk: short talk that you are going to say to the buyer. Speak concisely and cut to the chase. Generate authentic and diverse sentences, avoiding repetition of sentences that have already appeared in the conversation;
Action: one of the limited actions that define the real intention of your Talk. The type of your Action must be one of "[SELL],[REJECT],[DEAL],[QUIT]".
1. '[SELL] $M (N codename_1)' if you want to propose selling N items of the product with the codename "codename_1" to the buyer for the total price of $M.
2. '[REJECT]' if you choose to reject the other side's offer and await a new offer from the buyer.
3. '[DEAL] $M (N codename_1)' if you finally agree on a former offer proposed by the buyer, and sell N items of the product with the codename "codename_1" to the buyer for the total price of $M. $M (N codename_1) is a exact copy of buyer's previous offer. You should not use this action to propose a new price. This action will immediately end the conversation and close the deal.
4. '[QUIT]' if you believe that a mutually acceptable deal cannot be reached in limited turns. This action will immediately end the conversation.
You shouldn't choose action '[DEAL]' before buyer's action '[BUY]'.
'[DEAL] $M (N codename_1)' can only be chosen to accept the buyer's previous offer '[BUY] $M (N codename_1)'. Otherwise, you always choose from '[SELL]', '[REJECT]' and '[QUIT]'.

Your reply should strictly follow this format, for example:
Thought: I'm a seller, so I must sell the product with codename "apple_1" higher than its cost.
Talk: blah, blah...
Action: [SELL] $15 (1x apple_1)
""".strip()

    _PROMPT = {
'seller':"""
{inv}

Now, I play the role of buyer and you play the role of seller. We are going to negotiate based on the Inventory List in {max_turns} turns.
""".strip(),
}

    def __init__(self, model_name, role, inventory_info, turns=6) -> None:
        self.model = model_name
        self.role = role
        system = self._SELLER_SYSTEM_PROMPT
        user = self._PROMPT[role].format(inv=inventory_info, max_turns = turns)

        self.manager = HistoryManager('')
        self.manager.load_history([
            {'role':'system','content':system},
            {'role':'user','content':user},
            {'role':'assistant','content':'Thought: Yes, I am ready to negotiate using this format.\nTalk:  Action:  '},])

    def input(self,txt):
        if txt == '':
            h = self.manager.export_history()[:-1]
            assert h[-1]['role'] == 'user'
            self.manager.load_history(h)
        else:
            self.manager.add_user_text(txt)
        reply = self.chat(self.manager.export_history())
        self.manager.add_reply(reply)
        return reply

    def chat(self, history):
        """
        using api to return one reply string
        """
        raise NotImplementedError

    def __str__(self) -> str:
        return f"{type(self)} {self.role},{self.model}"

class gpt35Agent(SellerAgent):
    def chat(self, history):
        return api_pool.ChatCompletion(self.model, history)

class gpt4Agent(SellerAgent):
    def chat(self, history):
        return api_pool.ChatCompletion(self.model, history)

class llamaAgent(SellerAgent):
    def chat(self, history):
        return vllmApi.ChatCompletion(self.model, history)

class HumanAgent(SellerAgent):
    def chat(self, history):
        chance = 3
        print(color(history[-1]['content']))
        reply = input('Your are Seller, PLEASE REPLY:')
        
        parser = ActionParser()
        for _ in range(chance):
            try:
                your_action = input('Your Action:').strip()
                parser(your_action)
            except RuntimeError as e:
                print('WRONG FORMAT! Example: [SELL] $129.86 (1x code_1)')
                print(f'Chance {_}/{chance}')
        return reply.strip()

class dummyAgent(SellerAgent):
    def chat(self, history):
        return f'Talk: dummy seller test{asctime()}\nAction: [REJECT]'