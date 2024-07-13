# %%
import os
import csv,json,jsonlines
import requests
# convert to xml
from lxml import etree
import collections
collections.Iterable = collections.abc.Iterable
from dicttoxml import dicttoxml
from xml.dom.minidom import parseString

# %% [markdown]
# ## Functions

# %%
# read file https://raw.githubusercontent.com/STEPBible/STEPBible-Data/master/TIPNR%20-%20Translators%20Individualised%20Proper%20Names%20with%20all%20References%20-%20STEPBible.org%20CC%20BY.txt
def load_tipnr_data():
    '''
    Load TIPNR data from https://raw.githubusercontent.com/STEPBible/STEPBible-Data/master/TIPNR%20-%20Translators%20Individualised%20Proper%20Names%20with%20all%20References%20-%20STEPBible.org%20CC%20BY.txt if it does not exist yet
    and convert to list of dictionaries
    '''
    if os.path.isfile('/home/stockhausen/Dokumente/projekte/tipnr_data/TIPNR.txt'):
        contents = open('/home/stockhausen/Dokumente/projekte/tipnr_data/TIPNR.txt', "r")
    else:
        url = 'https://raw.githubusercontent.com/STEPBible/STEPBible-Data/master/TIPNR%20-%20Translators%20Individualised%20Proper%20Names%20with%20all%20References%20-%20STEPBible.org%20CC%20BY.txt'
        r = requests.get(url, allow_redirects=True)
        with open('/home/stockhausen/Dokumente/projekte/tipnr_data/TIPNR.txt', 'wb') as tipnr:
            tipnr.write(r.content)
        contents = open('/home/stockhausen/Dokumente/projekte/tipnr_data/TIPNR.txt', "r")
    return contents

# %%
def load_openbibleinfo_data():
    '''Load Bible-Geocoding-Data (ancient.jsonl) data from https://github.com/openbibleinfo/Bible-Geocoding-Data/raw/main/data/ancient.jsonl if it does not exist yet'''
    if os.path.isfile('/home/stockhausen/Dokumente/projekte/tipnr_data/openbibleinfo.jsonl'):
        part = open('/home/stockhausen/Dokumente/projekte/tipnr_data/openbibleinfo.jsonl', "r").read() 
    else:
        url = 'https://github.com/openbibleinfo/Bible-Geocoding-Data/raw/main/data/ancient.jsonl'
        r = requests.get(url, allow_redirects=True)
        with open("/home/stockhausen/Dokumente/projekte/tipnr_data/openbibleinfo.jsonl", 'wb') as openbibleinfo:
            openbibleinfo.write(r.content)
        part = open('/home/stockhausen/Dokumente/projekte/tipnr_data/openbibleinfo.jsonl', "r").read() 
    data = [json.loads(str(item)) for item in part.strip().split('\n')]
    return data

# %%
def convert_openbibleinfo():
    entries = load_openbibleinfo_data()
    list_of_openbibleplaces = []
    for entry in entries:
        openbibleplace = {}
        openbibleplace["id"] = entry["id"]
        openbibleplace["name"] = entry["friendly_id"]
        openbibleplace["pleiades"] = ""
        openbibleplace["tipnr"] = ""
        openbibleplace["wikidata"] = ""
        try:
            for key, value in entry["linked_data"].items():
                if key == "s2428ed":
                    openbibleplace["pleiades"] = value.get("url")
                elif key == "s3b25cf":
                    openbibleplace["tipnr"] = value.get("id").replace("@","_")
                elif key == "s7cc8b2":
                    openbibleplace["wikidata"] = "http://www.wikidata.org/entity/"+value.get("id")
        except:
            pass
        list_of_openbibleplaces.append(openbibleplace)
    return list_of_openbibleplaces

# %%
def get_unique_name(entry):
    suffix = entry.split("@")[1]
    if "-" in suffix:
        suffix = suffix.split("-")[0]
    elif "=" in suffix:
        suffix = suffix.split("=")[0]
    else:
        pass
    name = entry.split("@")[0]
    unique_name = "_".join([name,suffix])
    return unique_name

# %%
def convert_persons_dict():
    contents = load_tipnr_data()
    # getting the relevant parts of the file
    part = "".join(contents.readlines()[114:13380]) # line number start and end -1
    # some data cleaning
    #part = part.replace("@","_") # remove @ from IDs and replace with _
    part = part.replace("#","") # remove "#"
    part = part.replace("<br>","") # remove "<br>"
    part = part.replace(">","") # remove ">"
    entries = part.split("$========== PERSON(s)\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\n")[1:] # split by person, remove everything before first entry
    list_of_persons = []
    # conversion
    for entry in entries:
        lines = []
        clean = entry.split("\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\n")
        subrecord = {}
        for line in clean:
            number = "n"+str(clean.index(line))
            if clean.index(line) == 0:
                # if main record
                line = line.split("\t")
                biblical_person = {}
                biblical_person["unique_name"] = get_unique_name(line[0])
                biblical_person["uStrong"] = line[0].split("=")[1]
                #biblical_person["short_description"] = line[1]
                #biblical_person["ext_description"] = line[7]
                try:
                    biblical_person["father"] = get_unique_name(line[2].split(" + ")[0])
                except:
                    biblical_person["father"] = ""
                try:
                    biblical_person["mother"] = get_unique_name(line[2].split(" + ")[1])
                except:
                    biblical_person["mother"] = ""
                try:
                    biblical_person["siblings"] = [get_unique_name(x) for x in line[3].split(", ")]
                except:
                    biblical_person["siblings"] = line[3].split(", ")
                try:
                    biblical_person["partners"] = [get_unique_name(x) for x in line[4].split(", ")]
                except:
                    biblical_person["partners"] = line[4].split(", ")
                try:
                    biblical_person["offspring"] = [get_unique_name(x) for x in line[5].split(", ")]
                except:
                    biblical_person["offspring"] = line[5].split(", ")
                biblical_person["tribe"] = line[6]
                biblical_person["sex"] = line[8]
            elif clean.index(line) > 0 and clean.index(line) < len(clean)-2:
                # if sub_record
                line = line.split("\t")
                this_record = {}
                this_record["unique_tag"] = get_unique_name(line[1])
                if "=" in line[2]:
                    strongs = line[2].split("=")[0].split("«")
                    origname = line[2].split("=")[1]
                else:
                    strongs = ["-","-"]
                    origname = ""
                this_record["dStrong"] = strongs[0]
                try:
                    this_record["Strong"] = strongs[1]
                except:
                    this_record["Strong"] = ""
                this_record["orig_name"] = origname
                this_record["translated_name"] = line[3]
                this_record["link"] = line[4].replace("version=KJV","version=LXX|version=SBLG")
                this_record["references"] = ",".join(line[5].split("; ")) # join by comma, not by semicolon as in data
                subrecord[number] = this_record
                biblical_person["subrecord"] = subrecord
            elif clean.index(line) > 0 and clean.index(line) < len(clean)-1:
                line = line.split("\t")
                biblical_person["short_description"] = line[6].split("@Short= ")[1]
                biblical_person["ext_description"] = line[7].split("@Article= ")[1]
        list_of_persons.append(biblical_person)
    return list_of_persons

# %%
def convert_places_dict():
    contents = load_tipnr_data()
    # getting the relevant parts of the file
    part = "".join(contents.readlines()[13380:18071]) # line number start and end -1
    # some data cleaning
    #part = part.replace("_","-") # reserve _ for ID separator only
    #part = part.replace("@","_") # remove @ from IDs and replace with _
    entries = part.split("$========== PLACE\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\n")[1:] # split by place, remove everything before first entry
    list_of_places = []
    # conversion
    for entry in entries:
        lines = []
        clean = entry.split("\n")
        subrecord = {}
        for line in clean:
            number = "n"+str(clean.index(line))
            if clean.index(line) == 0:
                # if main record
                line = line.split("\t")
                biblical_place = {}
                biblical_place["unique_name"] = get_unique_name(line[0])
                biblical_place["uStrong"] = line[0].split("=")[1]
                # clean openbible name
                openbible_ref = line[1]
                if "= " in openbible_ref:
                    openbible_ref = openbible_ref.split("= ")
                    name = openbible_ref[0]
                    identification = openbible_ref[1].split(" (")[0]
                    openbible_ref = name+" ("+identification+")"
                else:
                    pass
                # replace _ with " "
                biblical_place["openbible_name"] = openbible_ref.replace("_"," ")
                try:
                    biblical_place["lonlat"] = line[5].split("@")[1]
                except:
                    biblical_place["lonlat"] = ""
            elif clean.index(line) > 0 and clean.index(line) < len(clean)-2:
                # if sub_record
                line = line.split("\t")
                this_record = {}
                this_record["unique_tag"] = get_unique_name(line[1])
                if "=" in line[2]:
                    strongs = line[2].split("=")[0].split("«")
                    origname = line[2].split("=")[1]
                else:
                    strongs = ["-","-"]
                    origname = ""
                this_record["dStrong"] = strongs[0]
                try:
                    this_record["Strong"] = strongs[1]
                except:
                    this_record["Strong"] = ""
                this_record["orig_name"] = origname
                this_record["translated_name"] = line[3]
                this_record["link"] = line[4].replace("version=KJV","version=LXX|version=SBLG")
                this_record["references"] = ",".join(line[5].split("; ")) # join by comma, not by semicolon as in data
                subrecord[number] = this_record
                biblical_place["subrecord"] = subrecord
            elif clean.index(line) > 0 and clean.index(line) < len(clean)-1:
                line = line.split("\t")
                biblical_place["short_description"] = line[6].split("@Short= ")[1]
                biblical_place["ext_description"] = line[7].split("@Article= ")[1]
        list_of_places.append(biblical_place)
    return list_of_places

# %%
def enrich_places_data():
    openbible = convert_openbibleinfo()
    tipnr = convert_places_dict()
    '''Enrich tipnr data with openbible pleiades links'''
    enriched_data = []
    for result in tipnr:
        enriched = {}
        try:
            place = next(item for item in openbible if item["tipnr"] == result["unique_name"])
            enriched = result
            enriched["pleiades"] = place["pleiades"]
            enriched["wikidata"] = place["wikidata"]
        except:
            enriched = result
            enriched["pleiades"] = ""
            enriched["wikidata"] = ""
        enriched_data.append(enriched)
    return enriched_data

# %%
def convert_others_dict():
    contents = load_tipnr_data()
    # getting the relevant parts of the file
    part = "".join(contents.readlines()[18071:18629]) # line number start and end -1
    # some data cleaning
    #part = part.replace("@","_") # remove @ from IDs and replace with _
    part = part.replace("#","") # remove "#"
    part = part.replace("<br>","") # remove "<br>"
    part = part.replace(">","") # remove ">"
    entries = part.split("$========== OTHER\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\n")[1:] # split by person, remove everything before first entry
    list_of_persons = []
    # conversion
    for entry in entries:
        lines = []
        clean = entry.split("\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\n")
        subrecord = {}
        for line in clean:
            number = "n"+str(clean.index(line))
            if clean.index(line) == 0:
                # if main record
                line = line.split("\t")
                biblical_person = {}
                biblical_person["unique_name"] = get_unique_name(line[0])
                biblical_person["uStrong"] = line[0].split("=")[1]
                #biblical_person["ext_description"] = line[1]
            elif clean.index(line) > 0 and clean.index(line) < len(clean)-2:
                # if sub_record
                line = line.split("\t")
                this_record = {}
                this_record["unique_tag"] = get_unique_name(line[1])
                if "=" in line[2]:
                    strongs = line[2].split("=")[0].split("«")
                    origname = line[2].split("=")[1]
                else:
                    strongs = ["-","-"]
                    origname = ""
                this_record["dStrong"] = strongs[0]
                this_record["Strong"] = strongs[1]
                this_record["orig_name"] = origname
                this_record["translated_name"] = line[3]
                this_record["link"] = line[4].replace("version=KJV","version=LXX|version=SBLG")
                this_record["references"] = ",".join(line[5].split("; ")) # join by comma, not by semicolon as in data
                subrecord[number] = this_record
                biblical_person["subrecord"] = subrecord
            elif clean.index(line) > 0 and clean.index(line) < len(clean)-1:
                line = line.split("\t")
                biblical_person["short_description"] = line[6].split("@Short= ")[1]
                biblical_person["ext_description"] = line[7].split("@Article= ")[1]
        list_of_persons.append(biblical_person)
    return list_of_persons

# %% [markdown]
# ## Write TIPNR data to file (json, xml)

# %% [markdown]
# ### Persons
# 
# containing PERSON(s) and OTHER categories

# %%
tipnr_persons = convert_persons_dict()+convert_others_dict()

# %%
# Write places according to text to file
with open('/home/stockhausen/Dokumente/projekte/tipnr_data/tipnr_persons.json', 'w') as fout:
# Ergebnisse werden in eine json-Datei geschrieben
    json.dump(tipnr_persons, fout, indent=4, ensure_ascii=False)

# %%
# convert json2 xml
xml = dicttoxml(tipnr_persons, attr_type=False)
dom = parseString(xml)
with open("/home/stockhausen/Dokumente/projekte/tipnr_data/tipnr_persons.xml", 'w') as file_open:
    file_open.write(dom.toprettyxml())

# %% [markdown]
# ### Places

# %%
tipnr_places = enrich_places_data()

# %%
# Write places according to text to file
with open('/home/stockhausen/Dokumente/projekte/tipnr_data/tipnr_places.json', 'w') as fout:
# Ergebnisse werden in eine json-Datei geschrieben
    json.dump(tipnr_places, fout, indent=4, ensure_ascii=False)

# %%
# convert json2 xml
xml = dicttoxml(tipnr_places, attr_type=False)
dom = parseString(xml)
with open("/home/stockhausen/Dokumente/projekte/tipnr_data/tipnr_places.xml", 'w') as file_open:
    file_open.write(dom.toprettyxml())

