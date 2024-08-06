modelname=$1 # llama-2-70b
dirpath=$2 # ./results
experimentName=$3 # testrun_1

mkdir -p $dirpath

python run_session.py $dirpath $experimentName 0.8\
 llamaAgent $modelname buyer\
 gpt35Agent gpt-3.5-turbo-1106 seller

python run_session.py $dirpath $experimentName 0.8\
 gpt35Agent gpt-3.5-turbo-1106 buyer\
 llamaAgent $modelname seller