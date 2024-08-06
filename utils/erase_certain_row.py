import jsonlines
import shutil
import os

def remove_condition(line):
    return 'Error' in line['errormsg']# or line['errormsg'] == 'turn limit'

def detect(filepath):
    cnt = 0
    with jsonlines.open(filepath,'r') as reader:
        for line in reader:
            if remove_condition(line):
                # print(list(line['inv'].keys()),'one erase')
                print(line['errormsg'],cnt)
                cnt += 1
    print(cnt)
    return True if cnt > 0 else False
    
def main(filepath):
    name, ext = os.path.splitext(filepath)
    cnt = 0
    for cnt in range(10):
        copy = name+'_copy'+str(cnt)+ext
        if not os.path.exists(copy):
            break
    print(copy)
    shutil.copy(filepath, copy)
    with jsonlines.open(copy,'r') as reader:
        lines = [line for line in reader]
    with jsonlines.open(filepath,'w') as writer:
        for line in lines:
            # if 'home-kitchen_2' not in list(line['inv'].keys()):
            if not remove_condition(line):
                writer.write(line)
            else:
                print('erase',line['errormsg'])
                cnt += 1
    print(f'"Error" lines {cnt}')

if __name__ == '__main__':
    dir = "/" # fill here
    for a,b,c in os.walk(dir):
        for file in c:
            if '.jsonl' in file and 'Eval_' not in file and '_copy' not in file and 'yi' in file:
                filepath = os.path.join(a,file)
                print(filepath)
                if detect(filepath) and input('y/n:') == 'y':
                    main(filepath)