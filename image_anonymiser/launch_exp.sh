#!/bin/bash

help="Expected [local | docker] [streamlit | gradio] [gpu | cpu] gradio_args"
path="$0"
dir_path=$(dirname "$path")
config=
deployment=$1
engine=$2
mode=$3
all=( "$@" )
args=( "${all[@]:3}" ) # for the time being only used for gradio
args_length="${#args[@]}"

if [ "$mode" = "cpu" ]; then
    config=config.yml
elif [ "$mode" = "gpu" ]; then
    config=config_gpu.yml
else
    echo "$help"
    echo "3rd parameter should be gpu or cpu"
    exit 1
fi

if [ "$deployment" = "local" ]; then
    if [ "$engine" = "streamlit" ]; then
        python -m streamlit run "$dir_path"/app_streamlit/1__Home.py --server.maxUploadSize=5 --server.port=8888 -- --bconfig="$config" 
    elif [ "$engine" = "gradio" ]; then
        if [ "$args_length" -ge 1 ]; then
            python "$dir_path"/app_gradio/app.py --bconfig="$config" "${args[@]}"
        else
            python "$dir_path"/app_gradio/app.py --bconfig="$config"
        fi
    else
        echo "$help"
        echo "2nd parameter should be streamlit or gradio"
        exit 1
    fi
elif [ "$deployment" = "docker" ]; then
    if [ "$engine" = "streamlit" ]; then
        python -m streamlit run "$dir_path"/app_streamlit/1__Home.py --server.maxUploadSize=5 --server.port=8888 -- --bconfig="$config" 
    elif [ "$engine" = "gradio" ]; then
        if [ "$args_length" -ge 1 ]; then
            python "$dir_path"/app_gradio/app.py --bconfig="$config" --server=0.0.0.0 "${args[@]}"
        else
            python "$dir_path"/app_gradio/app.py --bconfig="$config" --server=0.0.0.0
        fi
    else
        echo "$help"
        echo "2nd parameter should be streamlit or gradio"
        exit 1
    fi
else
    echo "$help"
    echo "1st parameter should be local or docker"
    exit 1
fi