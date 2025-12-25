source ~/miniconda3/bin/activate
conda activate opifex
cp generate-readme-table.py ../generate-readme-table.py
cd ..
python3 generate-readme-table.py
rm generate-readme-table.py
