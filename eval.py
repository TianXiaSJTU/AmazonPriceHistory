from utils.Action import Action, ActionParser
import jsonlines
import os
import json
import traceback
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import fire

class Evaluate:
    """
    Evaluate by calculating metrics on all lines in .jsonl
    """
    def __init__(self,filepath:str, save=True) -> None:
        self.filepath = filepath
        self.all_session_metrics = []
        self.total_lines = 0
        self.save = save
        with jsonlines.open(filepath,'r') as f:
            for line in f:
                self.total_lines += 1
                # for turn in line['history']:
                #     print(f"\n{json.dumps(turn, indent=2)}\n")
                m = Metrics(line, row = self.total_lines).output()
                # There are some empty histories, which have no metric.
                if m['turns'] > 0:
                    self.all_session_metrics.append(m)

    def compute(self):
        wrongAct_num = sum([i['wrongAction'] for i in self.all_session_metrics])
        validSession = [i for i in self.all_session_metrics if i['wrongAction'] == 0]
        deal_metrics = [i for i in self.all_session_metrics if i['closeADeal'] == 1 and i['wrongAction'] == 0]


        mutual_session = [i for i in self.all_session_metrics if i['costGTbudget'] == 0 and i['wrongAction'] == 0]
        conflicting_session = [i for i in self.all_session_metrics if i['costGTbudget'] == 1 and i['wrongAction'] == 0]

        mutual_deal = [i for i in mutual_session if i['closeADeal'] == 1]
        conflicting_deal = [i for i in conflicting_session if i['closeADeal'] == 1]
        
        if self.total_lines:
            print('\n\n',self.filepath)
            print(f'valid sessions, valid MI sessions, valid CI sessions')
            print(f'{len(validSession)}\n{len(mutual_session)}\n{len(conflicting_session)}')
            print('deals, deal rate')
            print(f'{len(deal_metrics)}\n{len(deal_metrics)/self.total_lines*100:.2f}%')
            print('MI deals, MI deal rate')
            print(f'{len(mutual_deal)}\n{len(mutual_deal)/ len(mutual_session) *100 if len(mutual_session) else 0 :.2f}%')
            print('CI deals, CI deal rate')
            print(f'{len(conflicting_deal)}\n{len(conflicting_deal)/ len(conflicting_session) *100 if len(conflicting_session) else 0 :.2f}%')

        def average_dict(l):
            res ={'buyer_bargained_profit':[],
                'seller_bargained_profit':[],
                'buyer_bargained_ratio':[],
                'seller_bargained_ratio':[],}

            for i in l:
                for k in res:
                    res[k].append(i[k])
            average = dict()
            s = dict()
            for k in res:
                s[k] = sum(res[k])
                if len(res[k]):
                    average[k] = sum(res[k])/len(res[k])
                else:
                    average[k] = 0
                # print(f'{average[k]:.4f}')
                # print(f'{s[k]:.4f}')
            return average,s
        
        average_mutual,s_mutual = average_dict(mutual_deal)
        average_conflict,s_conflict = average_dict(conflicting_deal)
        average_all,s_all = average_dict(deal_metrics)
        saving_result = {
            'valid_session_num':len(validSession),
            'average_mutual': average_mutual,
            'sum_mutual': s_mutual,
            'average_conflicting': average_conflict,
            'sum_conflicting': s_conflict,
            'average_all':average_all,
            'sum_all': s_all,
            'deal_metrics':deal_metrics,
            'mutual_deal':mutual_deal,
            'conflicting_deal':conflicting_deal,
            'all_metrics_output':self.all_session_metrics,
        }

        if self.save:
            self.saveEvalResult_and_plot(saving_result)

        return [len(validSession),f'{len(validSession)/self.total_lines *100 if self.total_lines else 0 :.2f}%',len(mutual_session),len(conflicting_session),
                f'{len(mutual_deal)/ len(mutual_session) *100 if len(mutual_session) else 0 :.2f}%', 
                s_mutual['buyer_bargained_profit'],average_mutual['buyer_bargained_ratio'],s_mutual['buyer_bargained_ratio'],
                s_mutual['seller_bargained_profit'],average_mutual['seller_bargained_ratio'],s_mutual['seller_bargained_ratio'],
                f'{len(conflicting_deal)/ len(conflicting_session) *100 if len(conflicting_session) else 0 :.2f}%',
                s_conflict['buyer_bargained_profit'],average_conflict['buyer_bargained_ratio'],s_conflict['buyer_bargained_ratio'],
                s_conflict['seller_bargained_profit'],average_conflict['seller_bargained_ratio'],s_conflict['seller_bargained_ratio'],
                f'{len(deal_metrics)/len(validSession)*100 if len(validSession) else 0 :.2f}%',
                f'{len(deal_metrics)/self.total_lines*100 if self.total_lines else 0 :.2f}%', 
                s_all['buyer_bargained_profit'],average_all['buyer_bargained_ratio'],s_all['buyer_bargained_ratio'],
                s_all['seller_bargained_profit'],average_all['seller_bargained_ratio'],s_all['seller_bargained_ratio'],
                ]

    def saveEvalResult_and_plot(self,saving_result):
        # stored in Eval_filename.json in the folder with the same name in the same directory.
        dirpath = os.path.splitext(self.filepath)[0]
        os.makedirs(dirpath,exist_ok=True)
        _,filename = os.path.split(dirpath)
        eval_filepath = os.path.join(dirpath,'Eval_'+filename+'.json')

        with open(eval_filepath,'w') as f:
            json.dump(saving_result,f,ensure_ascii=False)

        # plot
        b_profit_a = [i["buyer_bargained_profit"] for i in saving_result['mutual_deal']]
        b_profit_b = [i["buyer_bargained_profit"] for i in saving_result['conflicting_deal']]
        s_profit_a = [i["seller_bargained_profit"] for i in saving_result['mutual_deal']]
        s_profit_b = [i["seller_bargained_profit"] for i in saving_result['conflicting_deal']]

        b_ratio_a = [i["buyer_bargained_ratio"] for i in saving_result['mutual_deal']]
        b_ratio_b = [i["buyer_bargained_ratio"] for i in saving_result['conflicting_deal']]
        

        # plt.subplot(1,2,1)
        plt.figure(figsize=(4.3,2.5),dpi=1200)
        plt.scatter(s_profit_a, b_profit_a,marker='.',color='blue',label='Mutual Interest',linewidth=0.25)
        plt.scatter(s_profit_b, b_profit_b,marker='.',color='red',label='Conflicting Interest',linewidth=0.25)
        # some outliers may be outside of the range
        plt.xlim(-400,700)
        plt.ylim(-300,300)
        plt.axhline(0, color='black', linestyle='dashed', linewidth=0.5) 
        plt.axvline(0, color='black', linestyle='dashed', linewidth=0.5) 
        plt.xlabel(r'$P_s$')
        plt.ylabel(r'$P_b$')
        plt.legend(fontsize=8)
        plt.tight_layout()
        plt.savefig(dirpath+'/profit_'+filename+'.pdf')
        plt.close()
        
        plt.figure(2)
        plt.figure(figsize=(4.3,2.5),dpi=1200)
        # The blue one is the normal situation when cost < budget
        bw = 0.6
        sns.kdeplot(b_ratio_a, bw_adjust=bw,fill = True,color='blue',label='Mutual Interest')
        sns.kdeplot(b_ratio_b, bw_adjust=bw,fill = True,color='red',label='Conflicting Interest')
        plt.xlabel(r'$P_b^{\prime}$')
        plt.xlim(-10,10)
        plt.axvline(0.5, color='blue', linestyle='dashed',linewidth=0.5)
        plt.axvline(0, color='grey', linestyle='dashed',linewidth=0.5)
        plt.axvline(-0.5, color='red', linestyle='dashed',linewidth=0.5) 
        plt.legend(fontsize=8)
        plt.tight_layout()
        plt.savefig(dirpath+'/buyerkde_'+filename+'.pdf')
        plt.close()

class Metrics:
    """Handle the history of a single line"""
    def __init__(self,line,row = -1):
        self.row = row
        self.index = line['index']
        self.inv = line['inv']
        self.product = list(line['inv'].keys())[0] # Because there is only one inv, the codename of the product can be given directly for the time being.
        self.need = {d['codename']:d['quantity'] for d in line['need']}
        self.cost = line['inv'][self.product][3]
        self.budget = line['need'][0]['budget']
        self.history = line['history']
        self.turns = len(self.history)
        if len(self.history):
            self.parser = ActionParser()
            self.buyer_offers = []
            self.seller_offers = []
            self.seller_reject_num = 0
            try:
                # print('eval>>>')
                self.evaluate()
            except Exception as e:
                print(f'Metrics Quit Evaluating: {e}')
            
    # def compute(self, action:Action):
    #     """Calculate the total price and total cost of the action's items"""
    #     listing_price = 0
    #     cost = 0
    #     budget = 0
    #     for k,v in action.objects.items():
    #         listing_price += self.inv[k][2] * v
    #         cost += self.inv[k][3] * v
    #         budget += self.budgets[k] * v
    #     return listing_price, cost, budget

    def evaluate(self):
        self.closeADeal = 0
        self.wrongAction = 0
        self.costGTbudget = 1 if self.cost > self.budget else 0
        # self.costGTbudget = 1 if self.inv[self.product][3] > self.budgets[self.product] else 0
        for index,turn in enumerate(self.history):
            try:
                # Iterate over the buyer and seller
                for speech in turn:
                    action = self.parser(speech['action'])
                    
                    if action.isBUY() and speech['role']=='buyer':
                        self.buyer_offers.append([action,index])
                    if action.isSELL() and speech['role']=='seller':
                        self.seller_offers.append([action,index])
                    if action.isDEAL():
                        # when inv has only one product, Action must be equal to need. Its quantity cannot exceeds 1, and its codename must exists.
                        if not Action.isEqualToNeed(action, self.need):
                            raise RuntimeError('Deal not equal to need')

                        # It is required that this deal is an existing offer made by the other party (the difference <= 0.01)
                        if speech['role']=='buyer':
                            if not any([ActionParser.hasSameMoneyAndObjects(offer[0],action) for offer in self.seller_offers]):
                                raise RuntimeError('Fake deal')
                        elif speech['role']=='seller':
                            if not any([ActionParser.hasSameMoneyAndObjects(offer[0],action) for offer in self.buyer_offers]):
                                raise RuntimeError('Fake deal')
                        
                        self.closeADeal = 1

                        cost = self.cost
                        budget = self.budget

                        # Prevent ZeroDivisionError
                        if 0 <= budget - cost < 1:
                            room = 1
                            budget = cost + 1
                        elif -1 < budget - cost < 0:
                            room = 1
                            budget = cost - 1
                        else:
                            room = abs(budget - cost)

                        self.B = budget
                        self.C = cost
                        self.D = action.money
                        self.buyer_bargained_profit = budget - action.money
                        self.seller_bargained_profit = action.money - cost
                        self.buyer_bargained_ratio = (self.buyer_bargained_profit)/room
                        self.seller_bargained_ratio = (self.seller_bargained_profit)/room
                        break
                    if action.isQUIT():
                        break
            except (KeyError,RuntimeError) as e:
                # If Parser cannot parse a valid action text, a runtime error will occur;
                # If there is an wrong codename, key error will occur during compute calculation.

                # print('WrongAction')
                # print(e)
                self.wrongAction = 1
                break

            except Exception as e:
                traceback.print_exc()

        # print(self.buyer_offers,self.seller_offers)
        self.buyer_offer_num = len(self.buyer_offers)
        self.seller_offer_num = len(self.seller_offers)

    def output(self):
        result = dict()
        attr = ['row','index','turns', 'closeADeal','wrongAction', 'costGTbudget',
                'B','C','D',
                'buyer_bargained_profit', 'buyer_bargained_ratio',
                'seller_bargained_profit', 'seller_bargained_ratio',
                'buyer_offer_num', 'seller_offer_num', 
            ]

        for a in attr:
            try:
                result[a] = getattr(self,a)
            except AttributeError as e:
                pass
        return result
    
def eval_all_jsonl(dir='./results',savename = 'eval_results.csv'):
    """
    dir: the dirpath your use in run_2stages.sh
    savename: the csv name where you save all the eval results of all experiments in this dir.
    we don't eval those files with 'Eval_','_copy','test' in their names.
    """
    data = []
    for a,b,c in os.walk(dir):
        for file in c:
            if '.jsonl' in file and 'Eval_' not in file and '_copy' not in file and 'test' not in file:
                # print(a,b,c)
                filepath = os.path.join(a,file)
                buyer,seller,budget_factor = file.split('+')[:3]
                buyer=buyer.split(':')[-1]
                buyer = f'OG({buyer})' if 'OGNarratorAgent' in a else buyer
                seller=seller.split(':')[-1]
                budget_factor = budget_factor.removeprefix('F')
                data.append([os.path.split(a)[1], file, filepath, buyer,seller,budget_factor, 
                             *Evaluate(filepath, save=True).compute()])
    df = pd.DataFrame(data)
    df.to_csv(os.path.join(dir,savename),
              header=['type','filename','path','buyer','seller','budget_factor',
                      'validNum','validRate','mutualNum','conflictNum',
                    'MI_deal_rate','MI_BUYER_sum_profit','MI_BUYER_avg_ratio','MI_BUYER_sum_ratio',
                    'MI_SELLER_sum_profit','MI_SELLER_avg_ratio','MI_SELLER_sum_ratio',
                    'CI_deal_rate','CI_BUYER_sum_profit','CI_BUYER_avg_ratio','CI_BUYER_sum_ratio',
                    'CI_SELLER_sum_profit','CI_SELLER_avg_ratio','CI_SELLER_sum_ratio',
                    'valid_deal_rate','ALL_deal_rate','ALL_BUYER_sum_profit','ALL_BUYER_avg_ratio','ALL_BUYER_sum_ratio',
                    'ALL_SELLER_sum_profit','ALL_SELLER_avg_ratio','ALL_SELLER_sum_ratio',
                    ])
    print(f'result saved to {savename}')

def eval_file(file):
    if '.jsonl' in file and 'Eval_' not in file and '_copy' not in file and 'test' not in file:
        return Evaluate(file, save=True).compute()
    return None
if __name__ == '__main__':
    fire.Fire(eval_all_jsonl)