#!/bin/bash

code_dir=/path/to/code
script=$1

mkdir -p ${code_dir}/logs
for sub in $(awk -F, 'NR>1 && $3=="True"{print $1}' ${code_dir}/subSesList.txt | sort -u); do
    sbatch -c 24 -N 1 --mem=40G -t 01:30:00 \
        -J ${script%.py}-${sub} \
        -o ${code_dir}/logs/${script%.py}_${sub}.o \
        -e ${code_dir}/logs/${script%.py}_${sub}.e \
        --wrap "python3 ${code_dir}/${script} -subject ${sub}"
done
