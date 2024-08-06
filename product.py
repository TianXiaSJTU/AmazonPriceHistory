from dataclasses import dataclass
import json
import os


@dataclass
class Product:
    title:str
    description:str
    price:float
    # cost is private information of seller. invisible to buyer
    cost:float

    # Consider a conversation with multiple items: the names/codenames/codes given by the seller are used as the codename field.
    # There should be no duplicate codenames
    codename:str = 'product'

    def info(self):
        return (self.title, self.description, self.price, self.cost)
    
    def public_info(self):
        return (self.title, self.description, self.price)

    def codename_string(self):
        return self.codename
    
    def string(self):
        """
        Returns 5 pieces of product information in string form. Ends with \\n\\n
        """
        return """
Title: "{}"
Description: "{}"
List Price: ${}
Cost: ${}

""".format(self.title,self.description,self.price,self.cost).lstrip()
    
    def public_string(self):
        """
        Returns 4 pieces of product information (No Cost) in string form. Ends with \\n\\n
        """
        return """
Title: "{}"
Description: "{}"
List Price: ${}

""".format(self.title,self.description,self.price).lstrip()


class Inventory:
    """
    Inventory saves all the products of the seller in a session.
    """
    string_format = "Product{}\nCodename: {}\n"
    def __init__(self,products) -> None:
        self.products = products

    def catalog(self):
        """
        returns a dict of the inventory for the buyer
        """
        return {p.codename:p.public_info() for p in self.products}

    def _catalog(self):
        """
        returns a dict of the inventory for the seller that contains cost.
        """
        return {p.codename:p.info() for p in self.products}
    
    def public_list(self):
        """
        the string format of the inventory for the buyer
        """
        strings = ['Inventory List:\n']
        for idx,p in enumerate(self.products):
            strings.append(''.join([self.string_format.format(idx+1, p.codename), p.public_string()]))
        return ''.join(strings).strip()
    
    def list(self):
        """
        the string format of the inventory for the seller
        """
        strings = ['Inventory List:\n']
        for idx,p in enumerate(self.products):
            strings.append(''.join([self.string_format.format(idx+1, p.codename), p.string()]))
        return ''.join(strings).strip()
    
    def titles(self):
        return '/'.join([p.title.strip() for p in self.products])

def CamelAmazon(dir='./data/AmazonHistoryPrice'):
    inv = []
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

    for file in sorted(os.listdir(dir)):
        with open(os.path.join(dir,file)) as f:
            products = json.load(f)
            for idx,p in enumerate(products):
                inv.append(Inventory([Product(*amazonDescInfo(p,idx))])) # Each inventory contains only a single product

    return inv

if __name__ =='__main__':
    INVENTORIES = CamelAmazon()
    for inv in INVENTORIES[:10]:
        print(inv.public_list())
        print(inv.list())