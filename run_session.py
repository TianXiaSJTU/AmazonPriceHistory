from tqdm import tqdm
import os
import fire
import jsonlines
from session import Agent2AgentSession
from threading import Thread,Lock
from product import CamelAmazon
INVENTORIES = CamelAmazon()
# (title, description, quantity, Listing Unit Price(unit:$), Unit Cost(invisible to buyer))
def main(dirpath:str,filename:str, budget_factor:float, 
         buyer_agent, buyer_model_name, buyer_role, 
         seller_agent, seller_model_name, seller_role, 
         quota:int=1e9,
         # When quota > 0, only access the limited number of products in inv
         max_turns=6):
    
    
    # thread require fileLock to save jsonl
    fileLock = Lock()
    savepath = f"{dirpath.removesuffix('/')}/{buyer_agent}-{seller_agent}/{buyer_role}:{buyer_model_name}+{seller_role}:{seller_model_name}+F{budget_factor:.1f}+{filename}.jsonl"

    def run(index,inventory):
        Agent2AgentSession(index, fileLock, inventory, savepath, budget_factor, 
         buyer_agent, buyer_model_name, buyer_role, 
         seller_agent, seller_model_name, seller_role,
         max_turns)
        pbar.update()

    
    # Detect duplicate results
    if not os.path.exists(savepath):
        os.makedirs(os.path.dirname(savepath), exist_ok=True)
        threads = [Thread(target=run,args = (j, inventory)) for j,inventory in enumerate(INVENTORIES) if j < quota]
    else:
        with jsonlines.open(savepath,mode='r') as reader:
            DoneList = [line['index'] for line in reader]
        print(f'FILENAME.jsonl EXISTS! {len(DoneList)} lines')

        threads = [Thread(target=run,args = (j, inventory)) for j,inventory in enumerate(INVENTORIES) if j not in DoneList and j < quota]
        print('GenerateThreads:',len(threads))

    if threads:
        pbar = tqdm(threads,desc=f'{buyer_agent}-{seller_agent}/F{budget_factor:.1f}/{buyer_role}:{buyer_model_name}/{seller_role}:{seller_model_name}/{filename}',dynamic_ncols=True)
        for t in threads:
            t.start()

        for t in threads:
            t.join()
        pbar.close()
        
        
if __name__ == '__main__':
    fire.Fire(main)