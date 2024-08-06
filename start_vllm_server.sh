# YOUR_MODEL_DIR=../models/Llama-2-70b-chat-hf
# YOUR_GPU_NUM=4
YOUR_MODEL_DIR=$1
YOUR_GPU_NUM=$2
python -m vllm.entrypoints.api_server --model $YOUR_MODEL_DIR --tensor-parallel-size $YOUR_GPU_NUM --max-num-seqs 500
# you can adjust the max-num-seqs according to your GPU Memory