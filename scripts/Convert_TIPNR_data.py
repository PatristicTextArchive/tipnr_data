#!/usr/bin/env python
# coding: utf-8

import os,sys,glob,re,string,unicodedata
import csv,json,jsonlines
import requests
# convert to xml
from lxml import etree
from dicttoxml import dicttoxml
from xml.dom.minidom import parseString


# ## Functions

# read file https://raw.githubusercontent.com/STEPBible/STEPBible-Data/master/TIPNR%20-%20Translators%20Individualised%20Proper%20Names%20with%20all%20References%20-%20STEPBible.org%20CC%20BY.txt
def load_tipnr_data():
    '''
    Load TIPNR data from https://raw.githubusercontent.com/STEPBible/STEPBible-Data/master/TIPNR%20-%20Translators%20Individualised%20Proper%20Names%20with%20all%20References%20-%20STEPBible.org%20CC%20BY.txt if it does not exist yet
    and convert to list of dictionaries
    '''
    if os.path.isfile('/home/stockhausen/Dokumente/projekte/tipnr_data/TIPNR.txt'):
        contents = open('/home/stockhausen/Dokumente/projekte/tipnr_data/TIPNR.txt', "r").read() 
    else:
        url = 'https://raw.githubusercontent.com/STEPBible/STEPBible-Data/master/TIPNR%20-%20Translators%20Individualised%20Proper%20Names%20with%20all%20References%20-%20STEPBible.org%20CC%20BY.txt'
        r = requests.get(url, allow_redirects=True)
        with open('/home/stockhausen/Dokumente/projekte/tipnr_data/TIPNR.txt', 'wb') as tipnr:
            tipnr.write(r.content)
        contents = open('/home/stockhausen/Dokumente/projekte/tipnr_data/TIPNR.txt', "r").read()
    return contents


def load_openbibleinfo_data():
    '''Load Bible-Geocoding-Data (ancient.jsonl) data from https://github.com/openbibleinfo/Bible-Geocoding-Data/raw/main/data/ancient.jsonl if it does not exist yet'''
    if os.path.isfile('/home/stockhausen/Dokumente/projekte/openbibleinfo.jsonl'):
        contents = open('/home/stockhausen/Dokumente/projekte/openbibleinfo.jsonl', "r").read() 
    else:
        url = 'https://github.com/openbibleinfo/Bible-Geocoding-Data/raw/main/data/ancient.jsonl'
        r = requests.get(url, allow_redirects=True)
        with open("/home/stockhausen/Dokumente/projekte/openbibleinfo.jsonl", 'wb') as openbibleinfo:
            openbibleinfo.write(r.content)
        contents = open('/home/stockhausen/Dokumente/projekte/openbibleinfo.jsonl', "r").read() 
    data = [json.loads(str(item)) for item in contents.strip().split('\n')]
    return data


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
                    openbibleplace["wikidata"] = value.get("id")
        except:
            pass
        list_of_openbibleplaces.append(openbibleplace)
    return list_of_openbibleplaces


def convert_persons_dict():
    contents = load_tipnr_data()
    # some data cleaning
    contents = contents.replace("@","_") # remove @ from IDs and replace with _
    contents = contents.replace("#","") # remove "#"
    contents = contents.replace("<br>","") # remove "<br>"
    contents = contents.replace(">","") # remove ">"
    # getting the relevant parts of the file
    part = contents.split("\n#\t\t\t\t\t\t\t\t\n#==========================================================================================================\t\t\t\t\t\t\t\t\n#PLACE") # split after last person entry
    entries = part[0].split("$========== PERSON(s)\t\t\t\t\t\t\t\t\n")[2:] # split by person, remove everything before first entry
    list_of_persons = []
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
                biblical_person = {}
                biblical_person["unique_name"] = line[0].split("=")[0]
                biblical_person["uStrong"] = line[0].split("=")[1]
                biblical_person["short_description"] = line[1]
                biblical_person["ext_description"] = line[7]
                biblical_person["father"] = line[2].split(" + ")[0]
                biblical_person["mother"] = line[2].split(" + ")[1]
                biblical_person["siblings"] = line[3].split(", ")
                biblical_person["partners"] = line[4].split(", ")
                biblical_person["offspring"] = line[5].split(", ")
                biblical_person["tribe"] = line[6]
            elif clean.index(line) > 0 and clean.index(line) < len(clean)-1:
                # if sub_record
                line = line.split("\t")
                this_record = {}
                this_record["unique_tag"] = line[1]
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
                this_record["references"] = ",".join(line[5].split("; ")[:-1]) # join by comma, not by semicolon as in data; remove semicolon at end
                subrecord[number] = this_record
            biblical_person["subrecord"] = subrecord
        list_of_persons.append(biblical_person)
    return list_of_persons


def convert_places_dict():
    contents = load_tipnr_data()
    # some data cleaning
    contents = contents.replace("@","_") # remove @ from IDs and replace with _
    # getting the relevant parts of the file
    part = contents.split("\t\t\t\t\t\t\t\t\n\t\t\t\t\t\t\t\t\n#\t\t\t\t\t\t\t\t\n#==========================================================================================================\t\t\t\t\t\t\t\t\n#OTHER") # split after last place entry
    entries = part[0].split("$========== PLACE\t\t\t\t\t\t\t\t\n")[2:] # split by place, remove everything before first entry
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
                biblical_place["unique_name"] = line[0].split("=")[0]
                biblical_place["uStrong"] = line[0].split("=")[1]
                biblical_place["openbible_name"] = line[1]
                try:
                    biblical_place["lonlat"] = line[5].split("_")[1]
                except:
                    biblical_place["lonlat"] = ""
            elif clean.index(line) > 0 and clean.index(line) < len(clean)-1:
                # if sub_record
                line = line.split("\t")
                this_record = {}
                this_record["unique_tag"] = line[1]
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
                this_record["references"] = ",".join(line[5].split("; ")[:-1]) # join by comma, not by semicolon as in data; remove semicolon at end
                subrecord[number] = this_record
            biblical_place["subrecord"] = subrecord
        list_of_places.append(biblical_place)
    return list_of_places


def enrich_places_data():
    '''Enrich tipnr data with openbible pleiades links'''
    openbible = convert_openbibleinfo()
    tipnr = convert_places_dict()
    enriched_data = []
    for result in tipnr:
        enriched = {}
        try:
            place = next(item for item in openbible if item["tipnr"] == result["unique_name"])
            enriched = result
            enriched["pleiades"] = place["pleiades"]
        except:
            enriched = result
            enriched["pleiades"] = ""
        enriched_data.append(enriched)
    return enriched_data


def convert_others_dict():
    contents = load_tipnr_data()
    # some data cleaning
    contents = contents.replace("@","_") # remove @ from IDs and replace with _
    contents = contents.replace("#","") # remove "#"
    contents = contents.replace("<br>","") # remove "<br>"
    # getting the relevant parts of the file
    part = contents.split("\n\t\t\t\t\t\t\t\t\n\t\t\t\t\t\t\t\t\n\t\t\t\t\t\t\t\t\n\t\t\t\t\t\t\t\t\n\t\t\t\t\t\t\t\t\n\t\t\t\t\t\t\t\t\n\t\t\t\t\t\t\t\t\n\t\t\t\t\t\t\t\t\n\t\t\t\t\t\t\t\t\n\t\t\t\t\t\t\t\t\n\t\t\t\t\t\t\t\t\n\t\t\t\t\t\t\t\t\nANNOTATED EXAMPLES\t") # split after last person entry
    entries = part[0].split("$========== OTHER\t\t\t\t\t\t\t\t\n")[2:] # split by person, remove everything before first entry
    list_of_persons = []
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
                biblical_person = {}
                biblical_person["unique_name"] = line[0].split("=")[0]
                biblical_person["uStrong"] = line[0].split("=")[1]
                biblical_person["ext_description"] = line[1]
            elif clean.index(line) > 0 and clean.index(line) < len(clean)-1:
                # if sub_record
                line = line.split("\t")
                this_record = {}
                this_record["unique_tag"] = line[1]
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
                this_record["references"] = ",".join(line[5].split("; ")[:-1]) # join by comma, not by semicolon as in data; remove semicolon at end
                subrecord[number] = this_record
            biblical_person["subrecord"] = subrecord
        list_of_persons.append(biblical_person)
    return list_of_persons


# ## Write TIPNR data to file (json, xml)

# ### Persons
# 
# containing PERSON(s) and OTHER categories

tipnr_persons = convert_persons_dict()+convert_others_dict()

# Write places according to text to file
with open('/home/stockhausen/Dokumente/projekte/tipnr_data/tipnr_persons.json', 'w') as fout:
# Ergebnisse werden in eine json-Datei geschrieben
    json.dump(tipnr_persons, fout, indent=4, ensure_ascii=False)

# convert json2 xml
xml = dicttoxml(tipnr_persons, attr_type=False)
dom = parseString(xml)
with open("/home/stockhausen/Dokumente/projekte/tipnr_data/tipnr_persons.xml", 'w') as file_open:
    file_open.write(dom.toprettyxml())


# ### Places

tipnr_places = enrich_places_data()

# Write places according to text to file
with open('/home/stockhausen/Dokumente/projekte/tipnr_data/tipnr_places.json', 'w') as fout:
# Ergebnisse werden in eine json-Datei geschrieben
    json.dump(tipnr_places, fout, indent=4, ensure_ascii=False)

# convert json2 xml
xml = dicttoxml(tipnr_places, attr_type=False)
dom = parseString(xml)
with open("/home/stockhausen/Dokumente/projekte/tipnr_data/tipnr_places.xml", 'w') as file_open:
    file_open.write(dom.toprettyxml())

