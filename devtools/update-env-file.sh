#!/bin/bash
source ~/miniconda3/bin/activate
conda env export --name opifex | sed '/^prefix:/d' > ../environment.yml
