import jsonlines
import shutil
import os
import fire
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
            if 'Error' not in line['errormsg']:
                writer.write(line)
            else:
                cnt += 1
    print(f'erase {cnt} lines')
if __name__ == '__main__':
    fire.Fire(main)