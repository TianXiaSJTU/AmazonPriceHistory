import re
from api_setting import api_pool,vllmApi
from utils.ActionNarrator import ActionNarrator
from utils.Action import Action, ActionParser
from utils.HistoryManager import HistoryManager
from utils.ColoredPrint import color
from utils.Strategy import Strategy
from time import asctime
"""
The Agent base class implements init (loading different System Prompts according to different roles, etc.), Input (User prompt format), and history maintenance.
Each subclass implements its own implementation to obtain the reply string
"""

class BuyerAgent:
    _BUYER_SYSTEM_PROMPT = """
You are a buyer looking forward to buying things on your Shopping List from me, the seller.
You have access to the seller's Inventory List and you can bargain about the prices.
Your task is to bargain with the seller and reach a deal with the price as low as possible in limited turns.
You can only buy things on the Shopping List in the limited quantity. Use the codename of the product, instead of the title.
You can only buy things that cost less than your budget, otherwise, you should quit negotiating.

Your Reply should include 3 parts: Thought, Talk, and Action.
Thought: your inner strategic thinking of this bargaining session;
Talk: short talk that you are going to say to the seller. Speak concisely and cut to the chase. Generate authentic and diverse sentences, avoiding repetition of sentences that have already appeared in the conversation;
Action: one of the limited actions that define the real intention of your Talk. The type of your Action must be one of "[BUY],[REJECT],[DEAL],[QUIT]".
1. '[BUY] $M (N codename_1)' if you wish to offer the seller $M to purchase all N items of the product with the codename "codename_1".
2. '[REJECT]' if you choose to reject the other side's offer and await a new offer from the seller.
3. '[DEAL] $M (N codename_1)' if you finally accept on a former offer proposed by the seller. $M (N codename_1) is a exact copy of seller's previous offer. You should not use this action to propose a new price. This action will immediately end the conversation and close the deal.
4. '[QUIT]' if you believe that a mutually acceptable deal cannot be reached in limited turns. This action will immediately end the conversation.
You shouldn't choose action '[DEAL] $M' before seller's action '[SELL] $M'. Your first action should be '[BUY] $M (N codename_1)' or '[REJECT]'.
'[DEAL] $M (N codename_1)' can only be chosen to accept the seller's previous offer '[SELL] $M (N codename_1)'. Otherwise, you always choose from '[BUY]', '[REJECT]' and '[QUIT]'.

Your reply should strictly follow this format, for example:
Thought: I'm a buyer and I want to bargain. The listing price of codename "apple_1" is $15, which is too expensive, so I try to buy an apple for $10.
Talk: Hello, I'm tight on budget. can you sell it for 10$?
Action: [BUY] $10 (1x apple_1)
""".strip()

    _PROMPT = {
    'buyer':"""
{inv}

Shopping List
{need}

Now, I play the role of seller and you play the role of buyer. We are going to negotiate based on the Inventory List in {max_turns} turns.
""".strip(),
}

    def __init__(self, model_name, role, inv_pub_list, need='',turns=6) -> None:
        self.model = model_name
        self.role = role
        assert need is not None
        self.need_codes = [i.replace('codename:','').strip() for i in need.splitlines() if 'codename:' in i]
        system = self._BUYER_SYSTEM_PROMPT
        user = self._PROMPT[role].format(inv=inv_pub_list, need=need, max_turns = turns)

        self.manager = HistoryManager('')
        self.manager.load_history([
            {'role':'system','content':system},
            {'role':'user','content':user},
            {'role':'assistant','content':'Thought: Yes, I am ready to negotiate using this format.\nTalk:  Action:  '},])

    def input(self,txt):
        """If the txt is empty, remove the last assistant message in the manager, and then chat
        The user text saved by the manager is the result of the raw reply minus the Thought line, and the complete raw text of the reply contains the Thought Thinking Action."""
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

class gpt35Agent(BuyerAgent):
    def chat(self, history):
        return api_pool.ChatCompletion(self.model, history)

class gpt4Agent(BuyerAgent):
    def chat(self, history):
        return api_pool.ChatCompletion(self.model, history)

class llamaAgent(BuyerAgent):
    def chat(self, history):
        return vllmApi.ChatCompletion(self.model, history)

class HumanAgent(BuyerAgent):
    def input(self,txt):
        if txt == '':
            h = self.manager.export_history()[:-1]
            assert h[-1]['role'] == 'user'
            # SHOWING SYSTEM PROMPT
            print(color(h[0]['content']))
            self.manager.load_history(h)
        else:
            self.manager.add_user_text(txt)
        reply = self.chat(self.manager.export_history())
        self.manager.add_reply(reply)
        return reply
    
    def chat(self, history):
        chance = 3
        print()
        print(color(history[-1]['content'], text_color='YELLOW'))
        
        
        parser = ActionParser()
        for _ in range(chance):
            try:
                # thought = input('Your strategy thinking (you can skip):').strip()
                thought = ''
                reply = input('Your are buyer, PLEASE REPLY:').strip()
                your_action = input('Your Action:').strip() # buy,sell,reject,deal,q
                d = {'b':'[BUY] ${money} (1x {codename})',
                     's':'[SELL] ${money} (1x {codename})',
                     'd':'[DEAL] ${money} (1x {codename})',
                     'r':'[REJECT]',
                     'q':'[QUIT]',}
                if your_action[0] in d:
                    if your_action[0] in ['r','q']:
                        your_action = d[your_action[0]]
                    else:
                        your_action = d[your_action[0]].format(money = your_action[1:], codename = self.need_codes[0])

                action = parser(your_action)

                # Record all successful inputs to the local log
                with open('./humanInput.log','a') as f:
                    f.write(f'{asctime()};{thought};{reply};{your_action}\n')

                return f'Thought: {thought}\nTalk: {reply}\nAction: {your_action}'
            except RuntimeError as e:
                print('WRONG FORMAT! Example: [SELL] $129.86 (1x code_1)')
                print(f'Chance {_}/{chance}')
        raise ValueError('HUMAN INVALID INPUT')
    
class dummyAgent(BuyerAgent):
    def chat(self, history):
        return f'Talk: dummy buyer test{asctime()}\nAction: [REJECT]'

class OGNarratorAgent(BuyerAgent):
    """
    init needs to contain all Buyer meta-information, such as budget, strategy, start_factor, end_factor;
    In addition, the need is initialized based on the inventory. The buyer will generate demand based on the information of the specific item, including need, item, and weight.
    These variables fix an initial buyer.
    
    `strategy`: OG’s bargaining strategy, including linear, exp, swish, random
    `start_factor,end_factor`: It is the upper and lower bounds of the factor generated by the strategy. The factor is used to multiply the item budget budget to calculate the offer price.

    Only generate Action and accept the Action sent by the other party.
    The other party’s offer will be recorded internally
    """

    def __init__(self, model:str, inv_pub_list:str, catalog:dict, need:dict, turns:int,
                 strategy:str, start_factor:float, end_factor:float, showNarrator:bool):
        # need == [{codename,title,quantity,budget}]
        self.shoppinglist = need
        self.need = {d['codename']:d['quantity'] for d in need}
        self.total_budgets = sum([d['budget']*d['quantity'] for d in need])
        # codename: (title, desc, list price, cost)
        self.catalog = catalog
        # init all Strategy functions in f_strategies
        self.f_strategies = Strategy(turns,start_factor,end_factor) 
        # the strategy it used in every steps
        self.strategy = strategy
        
        self.turns = turns
        self.start_factor = start_factor
        self.end_factor = end_factor
        
        # memory records all offers and their effectivenesses
        self.memory = []
        
        self.narrator = ActionNarrator(role = 'buyer', method=model, inventory_public_list=inv_pub_list,showNarrator=showNarrator)
        # history saved for Narrator
        # [{role, talk, action}]
        self.talk_action_history = []
        
        # 0-indexed steps
        self.step = 0
        
        # 0 for active, 1 for deal, 2 for quit
        self.state = 0

    def __str__(self) -> str:
        return f"{type(self)} {self.strategy}, factor:[{self.start_factor}, {self.end_factor}]"
    
    def input(self, txt):
        # The input text comes from the other party, we need to parse it and call opposing_action
        # But when step is 0, the buyer starts first. OGNarrator don't need the txt to start.
        talk_matches = re.search(r'Talk: (.+)',txt)
        talk = talk_matches.group(1) if talk_matches else ''
        
        action_matches = re.search(r'Action: (.+)',txt)
        action = action_matches.group(1) if action_matches else ''
        
        if self.step > 0:
            self.opposing_action(txt)
            self.talk_action_history.append({'role':'seller', 'talk':talk, 'action':action})
        
        
        bot_action = self.think_action(self.step)
        bot_talk = self.narrator.speak(bot_action, history = self.talk_action_history, temperature=0.3)
        self.talk_action_history.append({'role':'buyer', 'talk':bot_talk, 'action':bot_action})
        self.step += 1
        return f"Talk: {bot_talk}\nAction: {bot_action}"

    def opposing_action(self, opposingAction = ''):
        if opposingAction != '':
            parser = ActionParser()
            try:
                action = parser(opposingAction)
                # print(action)
                if action.isDEAL():
                    self.state = 1
                elif action.isQUIT():
                    self.state = 2
                elif action.isSELL():
                    self.memory.append((action, self.compute_effectiveness(action)))
            except RuntimeError:
                pass
    
    def compute_utility(self, offer:Action) -> float:
        """
        There is currently only one product, so only 1.0 is returned.
        """
        return 1.0
        

    def compute_effectiveness(self,offer:Action) -> float:
        """
        For offers of multiple objects, calculate Effectiveness = (utility / money) / (1.0 / total budget)
        The highest utility is 1.0, and money can be any positive number. Effectiveness is a positive number, increasing with utility and decreasing with money.
        """
        assert offer.money, ValueError(f'{offer} has no price')
        utility = self.compute_utility(offer)
        return self.total_budgets * utility / offer.money

    def sum_budget(self, objects:dict) -> float:
        """
        For action objects, calculate the budget that can be used by these objects.
        """
        return sum([d['budget']*objects[d['codename']] for d in self.shoppinglist if d['codename'] in objects])
    
    def find_best_offer(self,mode:int):
        """
        Find the best offer we are currently responding to.
        mode=1, means the higher effectiveness the better; otherwise, choose the most recent offer.
        """
        if self.memory:
            if mode==1:
                best_offer, effectivenes = max(self.memory,key=lambda x: x[1])
                target_objects = best_offer.objects

            else:
                best_offer, effectivenes = self.memory[-1]
                target_objects = best_offer.objects
        else:
            best_offer, effectivenes = [None, 0]
            target_objects = self.need

        return target_objects, best_offer, effectivenes

    def deal_condition(self, action:Action, best_offer:Action, best_eff) -> bool:
        return self.compute_effectiveness(action) < best_eff and best_offer.money <= self.total_budgets
    
    def think_action(self, step) -> Action:
        """
        Offer Generator that generates actions
        """
        if step >= self.turns:
            # If you have reached the last step, consider trying DEAL for the best offer in Memory
            target_objects, best_offer, best_eff = self.find_best_offer(mode=1)
            if best_offer is not None and best_offer.money <= self.total_budgets:
                self.state = 1
                return best_offer.toDeal()
            else:
                self.state = 2
                return Action('QUIT')
        else:
            factor = self.f_strategies(self.strategy, step)
            if self.strategy == 'random':
                # The random strategy always bids randomly for self.need and will not DEAL in advance.
                target_objects = self.need
                draft_action = Action('BUY', factor * self.sum_budget(target_objects), target_objects)
                return draft_action
            else:
                # The non-random strategy calculates a best offer and drafts the next action based on the objects of the best offer.
                target_objects, best_offer, best_eff = self.find_best_offer(mode=1)
                draft_action = Action('BUY', factor * self.sum_budget(target_objects), target_objects)
                # It is necessary to compare the next Action and the best offer to determine whether it is necessary to DEAL in advance for the best offer.
                if best_offer is not None and self.deal_condition(draft_action, best_offer, best_eff):
                    self.state = 1
                    return best_offer.toDeal()
            return draft_action
