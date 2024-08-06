from matplotlib import pyplot as plt
import os
import json
DIRPATH = os.path.split(__file__)[0]
def main(dir='../data/AmazonHistoryPrice',budget_factor=0.8):
    dir = os.path.join(DIRPATH,dir)
    count = dict()
    price_cost = dict()
    cost_price_ratio = []

    def amazonDescInfo(p,idx):
        title = p['title']
        features = p.get('features','')
        desc = p.get('description','')
        if len(desc) < 5 and len(desc) < len(features):
            desc = features
        listPrice = float(p['list_price'].removeprefix('$').replace(',','')) 
        highPrice = float(p['highest_price'].removeprefix('$').replace(',',''))
        price = max(highPrice, listPrice)
        cost = float(p['lowest_price'].removeprefix('$').replace(',',''))
        codename = f"{p['category']}_{idx+1}"
        return (title, desc, price, cost, codename)
    for file in os.listdir(dir):
        count[file] = 0
        with open(os.path.join(dir,file)) as f:
            products = json.load(f)
            for idx,p in enumerate(products):
                title, desc, price, cost, codename = amazonDescInfo(p,idx)
                # if price > 5000:
                #     print(codename)
                #     print(p)
                assert price > 0
                cost_price_ratio.append(cost/price)
                count[file] += 1
                price_cost[codename] = (price, cost)
    
    if cost_price_ratio:
        print('The number of all sessions:',len(cost_price_ratio))
        print(f'Let budget factor={budget_factor}, there will be {sum([i <= budget_factor for i in cost_price_ratio])} MI sessions, {sum([i > budget_factor for i in cost_price_ratio])} CI sessions')

        print('avg. cost_price_ratio:',sum(cost_price_ratio)/len(cost_price_ratio))
        print('min. cost_price_ratio:',min(cost_price_ratio))
        print('max. cost_price_ratio:',max(cost_price_ratio))
    

    ### category, price GridSpec
    fig = plt.figure(figsize=(11.5, 3.2))
    gs = plt.GridSpec(1,2,fig,width_ratios=[1,1],left=0.05, right=0.99, bottom=0.30, top=0.98)
    # Create the Axes.
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])

    plotBar(ax1,count)
    plotScatter(ax2,price_cost)

    # plt.show()
    plt.savefig(os.path.join(DIRPATH,'overview.pdf'))
    plt.close()

    ### price_cost Hist
    plotHist(price_cost)
    plt.savefig(os.path.join(DIRPATH,'./cost_price_ratio.pdf'))
    plt.close()
    
    
def plotScatter(ax,price_cost):
    price = []
    cost = []
    ratio = []
    for k,v in price_cost.items():
        price.append(v[0])
        cost.append(v[1])
        ratio.append(v[1]/v[0])
        
    # fig, ax = plt.subplots(figsize=(8,5))
    ax.scatter(price,cost,s=3)
    # x = range(1,10)
    ax.plot(price, price,color='black',linestyle='-',linewidth=0.5)
    # Impact the grid plot!
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    # ax.set_aspect('equal')
    
    ax.set_xlabel('Highest Price ($)')
    ax.set_ylabel('Lowest Price ($)')

def plotBar(ax,count):
    
    tuplelist = sorted(count.items(),key=lambda x:x[1])
    
    
    names = [t[0].removesuffix('.json') for t in tuplelist]
    values = [t[1] for t in tuplelist]
    shift_x = [i+0.5 for i in range(len(values))]
    print(names,values)
    # plt.bar
    ax.bar(names,values,label = '')
    # ax.bar(shift_x, values, tick_label=names)
    for i, value in enumerate(values):
        ax.text(i, value + 0.1, str(value), ha='center', va='bottom',fontsize=9)
    ax.set_xticks(names)
    ax.set_xticklabels(names,rotation=25, ha='right')
    ax.set_ylabel('Count')
    ax.set_xlim(left=-3.3,right=18)
    ax.set_ylim(top=315)

def plotHist(price_cost):
    """
    plot low high price ratio
    """
    price = []
    cost = []
    ratio = []
    for k,v in price_cost.items():
        price.append(v[0])
        cost.append(v[1])
        ratio.append(v[1]/v[0])
    
    plt.figure(figsize=(3.8,2.3))
    plt.hist(ratio,[i/20 for i in range(20+1)])
    plt.axvline(x=0.8,color='black')
    plt.text(0.84,80,r'$f=0.8$',fontsize=10)
    plt.xlabel('the Proportion of Cost to List Price')
    plt.ylabel('Number of Sessions')
    # Displays a numeric value on each bar
    # for i, value in enumerate(values):
    #     plt.text(i, value + 0.1, str(value), ha='center', va='bottom')
    # plt.xticks(rotation=30, ha='right')
    plt.tight_layout()

if __name__ == '__main__':
    main()