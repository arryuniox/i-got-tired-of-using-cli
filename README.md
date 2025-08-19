ok twins if yall ever get tired of using linux cli scripts for annotating genomes yall can use my very amazing web application!!!

a few things to note is that this was built in WSL so if you wanna run this you gotta run it in WSL, i dont make the rules here but in order to set yall up for success, ill give yall the instructions

so github is very stinky and doesn't allow for files >100MB so you gotta go on the InterPro website to download the Pfam-A.hmm

then you put it into the data folder

go into ubuntu bash terminal and run the two following commands

cd data

hmmpress Pfam-A.hmm

but in order to do that you also have to download prodigal and hmmer which is a lot simpler, you just go

sudo apt update
sudo apt-get install -y hmmer prodigal

and wait like a trillion years or smth like that

everything in the venv should already be set up so you just gotta go select your interpreter and select the venv and activate it with

source venv/bin/activate

and run

python app.py

and everything should be bing chilling
