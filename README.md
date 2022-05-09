# CS1470_Final_Project

USAGE: 

pip install -r requirements.txt
In main directory, call `python3 /LSTM/experiment_1.py` with either --wavenet or --lstm, and then --train or --produce
Examples:
To train:
python3 /LSTM/experiment_1.py --lstm --train
python3 /LSTM/experiment_1.py --wavenet --train
For just music:
python3 /LSTM/experiment_1.py --lstm --produce
python3 /LSTM/experiment_1.py --wavenet --produce

To get data, download and unzip 'midis_v1.2.zip' from https://drive.google.com/drive/folders/1Stz3CAvMoplo79LR5I3onMWRelCugBYS in the main directory (outside LSTM)