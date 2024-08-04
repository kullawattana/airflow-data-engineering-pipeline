import json
from pathlib import Path

p = Path(__file__).with_name('sample.json')

# Data to be written
dictionary = {
	"name": "Peter",
	"age": 20
}

with p.open("w") as outfile:
	json.dump(dictionary, outfile)

with p.open('r') as openfile:
    json_object = json.load(openfile)
 
print(json_object)
print(type(json_object))
