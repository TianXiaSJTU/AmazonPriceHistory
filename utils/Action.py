from dataclasses import dataclass
from typing import List,Union
import re

ACTION_TYPE_WITH_MONEY = ['BUY','SELL','DEAL']
ACTION_TYPE_WO_MONEY = ['REJECT','QUIT']
@dataclass
class Action:
    """
    Defines a Action: type, (money, objects)
    (Object of type Action is not JSON serializable)
    """
    action_type:str
    money:Union[float, None] = None
    objects:Union[dict, None] = None
    
    def __post_init__(self):
        """Range checking, checking the relationship between actions, money and objects"""
        if self.action_type in ACTION_TYPE_WITH_MONEY:
            if self.money is None:
                raise ValueError("Action: field money is None")
            if self.money < 0:
                raise ValueError("Action: field money is Negative")
            self.money = round(self.money, 2)

            if not self.objects:
                raise ValueError("Action: field objects is None/empty dict")
            for k,v in self.objects.items():
                if v <= 0:
                    raise ValueError(f"Not Positive Object: {v} {k} ")
        elif self.action_type in ACTION_TYPE_WO_MONEY:
            if self.money is not None or self.objects is not None:
                raise ValueError("Action Type and other fields (Not None) not fitted")
        else:
            raise ValueError("Action Type not seen")
        
    def __str__(self):
        if self.money is None or self.objects is None:
            return f"[{self.action_type}]"
        
        objects_string = ", ".join([f"{number}x {name}" for name, number in self.objects.items()])
        return f"[{self.action_type}] ${str(self.money).removesuffix('.0')} ({objects_string})"
    
    def __add__(self,other):
        """
        Two actions of the same type can be added together
        """
        def add_dicts(a,b):
            res = a.copy()
            for k,v in b.items():
                res[k] = res.get(k,0) + v
            return res
        
        assert isinstance(other, Action), TypeError('object to be added is not Action')
        if self.action_type == other.action_type:
            if all(i is not None for i in [self.money,self.objects,other.money,other.objects]):
                return Action(self.action_type, self.money+other.money, add_dicts(self.objects,other.objects)) # type: ignore
            else:
                return Action(self.action_type,)
        else:
            raise TypeError("object to be added is not the same type")

    def isBUY(self):
        return self.action_type == 'BUY'
    
    def isSELL(self):
        return self.action_type == 'SELL'

    def isREJECT(self):
        return self.action_type == 'REJECT'
    
    def isDEAL(self):
        return self.action_type == 'DEAL'
    
    def isQUIT(self):
        return self.action_type == 'QUIT'
    
    def isEndingAction(self):
        return self.action_type in ['DEAL','QUIT']
    
    def toDeal(self):
        self.action_type = 'DEAL'
        return self
    
    def hasMoneyAndObjects(self):
        return self.money is not None and self.objects is not None
    
    def isEqualToNeed(self,need):
        """
        whether action.objects == need (not None or empty)
        """
        if not need:
            raise ValueError("input need is empty")
        if not self.objects:
            raise ValueError("self.objects is empty")
        return self.objects == need
    
    def isGreaterThanNeed(self,need):
        """
        whether action objects contains need.
        If action is Greater than need, their intersection is need itself.
        """
        if self.isEqualToNeed(need):
            return False
        
        action_items = self.objects.keys() #type: ignore
        for k,v in need.items():
            if k not in action_items or self.objects[k] < v: #type: ignore
                return False
        return True
    
    def average_price(self):
        assert self.money is not None and self.objects is not None, TypeError('This Action has no price')
        num = sum(self.objects.values())
        assert num > 0, ValueError('This Action has wrong object numbers')
        return self.money/num
    
    def intersection_with_need(self,need):
        """
        It is used to compare with the buyer's need dict. It indicates what the buyer really needs in this action
        """
        if self.isEqualToNeed(need):
            return need
        else:
            if self.objects and need:
                key_intersection_set = self.objects.keys() & need.keys()
                intersection_dict = dict()
                for k in key_intersection_set:
                    intersection_dict[k] = min(self.objects[k], need[k])
                return intersection_dict
            raise ValueError("Empty objects/need")
        
    def replace_type(self, new_type:str):
        """
        switch type among DEAL, BUY, SELL 
        """
        if self.action_type in ACTION_TYPE_WITH_MONEY and new_type in ACTION_TYPE_WITH_MONEY:
            return Action(new_type, self.money, self.objects)

        raise TypeError("old type and new type must are types with money and objects")


    def __iter__(self):
        if self.money is None or self.objects is None:
            return iter([self.action_type,])
        return iter([self.action_type, self.money, self.objects])

class ActionParser:
    """
    identify and parse fields, type check
    Returns the last action instance
    
    `p = ActionParser()`

    `action = p(text)`
    """
    
    __PATTERN = r'\[([A-Z]+)\](?: \$([\d\,]+(?:\.[\d\,]+)?) \(((?:\d+x? .+, )*\d+x? .+?)\))?'

    def __init__(self) -> None:
        self.__ACTION_TYPES = ACTION_TYPE_WITH_MONEY+ACTION_TYPE_WO_MONEY

    def __call__(self,text:str) -> Action:
        """
        The regex matches each action in the text, and the last action instance in the list is returned after the type conversion
        """
        assert isinstance(text,str), TypeError('input is not string')
        try:
            action_tuple_list = self.extract_actions(text)
            # print(action_tuple_list)
            action_fields = self.validate_type(action_tuple_list[-1])
            return Action(*action_fields) # type: ignore
        except Exception as e:
            raise RuntimeError(f"ActionParser: {e}:{text}")
    
    
    def extract_actions(self, text):
        matches = re.findall(self.__PATTERN, text)
        if matches:
            # matches are all actions in the field
            return matches
        else:
            raise RuntimeError("ActionParser: No action in text")
        

    def validate_type(self, action_string_tuple):
        """
        Type conversion and check the range, then return the action tuple"""
        action_type, money_string, objects_string = action_string_tuple

        assert action_type in self.__ACTION_TYPES, TypeError(f'[{action_type}] is a wrong action type')
        
        if money_string == '' or objects_string == '':
            return (action_type,)

        money = float(money_string.replace(',',''))
        assert money >= 0, ValueError(f'offer ${money} is negative number')

        objects = dict()
        for i in objects_string.split(', '):
            match = re.search('(\d+)x? (.+)',i)
            number = match.group(1)
            item = match.group(2)
            objects[item] = objects.get(item, 0) + int(number)

        return (action_type, money, objects)
    
    @staticmethod
    def hasSameMoneyAndObjects(action1:Action,action2:Action) -> bool:
        if action1.hasMoneyAndObjects() and action2.hasMoneyAndObjects():
            if abs(action1.money - action2.money) <= 0.01 and action1.objects == action2.objects:
                return True
        return False



if __name__ == '__main__':
    p = ActionParser()
    print(p("[SELL] $11,129.86 (1x tools-home-improvement_136, 2x to-a_13)"))
    x = Action('BUY',10,{'phones':1})
    z= Action('BUY',10.11,{'phones_2-1':3})
    print(x,z)
    print(p(str(x)),p(str(z)))
    a = p('[DEAL] $32 (1x movies-tv_44 fafaf, 2x dafa da, 3 ffa, 4x 114) + free bonus item (1x cufflinks)')
    print(a.objects)