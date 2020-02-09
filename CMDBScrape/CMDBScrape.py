import csv
import requests
import json

#import function for warranty exp date
from DateFormat import date_format

#import api key
from APIKey import api_key

#functions for requests
def get_json_data(url):
    #get response - for possible future error handling
    response = requests.get(url)

    #get data from dell's website
    data = requests.get(url).text

    #print(json.dumps(json_data, indent=2))

    json_data = json.loads(data)
    return json_data

#functions for getting computer information
def get_expiration_date(computer, json_data):
    expiration_Dates = []
    #get asset entitlement data (warranty information)
    for item in json_data['AssetWarrantyResponse'][0]['AssetEntitlementData']:

        #ignore dell digital delivery which seems to be the upgrade option
        if(item['ServiceLevelDescription'] != "Dell Digitial Delivery"):
            expiration_Dates.append(item['EndDate'])

    #if first date in expiration_Dates[] is always used
    computer.exp_date = date_format(expiration_Dates[0])
    print(computer.exp_date)

def get_accidental_damage(computer, json_data):
    warranty_Types = []
    #get asset entitlement data (warranty information)
    for item in json_data['AssetWarrantyResponse'][0]['AssetEntitlementData']:
        warranty_Types.append(item['ServiceLevelDescription'])
                    
    #if accidental damage was found
    if any("Accidental Damage" in container for container in warranty_Types):
        computer.accidental_damage = "TRUE"
    else:
        computer.accidental_damage = "FALSE"

def get_ship_date(computer, json_data):
    ship_date = json_data['AssetWarrantyResponse'][0]['AssetHeaderData']['ShipDate']
    computer.ship_date = date_format(ship_date)
    print(computer.ship_date)

def get_model(computer, json_data):
    computer.model = json_data['AssetWarrantyResponse'][0]['AssetHeaderData']['MachineDescription']
    print(computer.model)

#class for each computer
class Computer:
    exp_date = ""
    accidental_damage = ""
    ship_date = ""
    model = ""
    uanet_id = ""

#open SCCMReport to be read
with open('SCCMReport.csv', 'r') as sccm_csv:
    sccm_reader = csv.reader(sccm_csv)
    computer = Computer()

    #skip first line in the reader which is the header
    next(sccm_reader)

    #url info
    dell_web_address = "https://api.dell.com/support/assetinfo/v4/getassetwarranty/"

    #open new file to write to for footprints import
    with open('CMDB.csv', 'w', newline='') as cmdb:
        cmdb_writer = csv.writer(cmdb)

        #header for cmdb writing
        header = ['id', 'status_1', 'created_by', 'criticality', 'created_on', 'ci_number', 'name_1', 'updated_by', 'soft_delete_id', 'version', 'icon_name', 'updated_on', 'asset_id', 'color', 'ci_number_fx_rev', 'room', 'model', 'building', 'serial_number', 'manufacturer', 'operating_system', 'university_owned_', 'uanet_id', 'machine_name', 'warranty_type', 'lab_computer', 'date_warranty_expires', 'date_shipped', 'owned_by', 'building_list', 'accidental_damage']
        cmdb_writer.writerow(header)

        #empty row for future cmdb writing
        row = [''] * 31
            
        #for each computer in csv file - get necessary information
        for line in sccm_reader:
            if (line[4] == "Dell Inc."):
                #get url
                serial_number = line[3]
                url = dell_web_address + serial_number + api_key

                #get json data
                json_data = get_json_data(url)
                #print(json.dumps(json_data, indent=2))

                #check for invalid format (Bad Serial Number/ BIL Assets / Excess Tags)
                invalid_format = json_data['InvalidFormatAssets']['BadAssets']
                invalid_BIL_assets = json_data['InvalidBILAssets']['BadAssets']
                excess_tags = json_data['ExcessTags']['BadAssets']

                #get warranty expiration date, acc dmg, ship date, and model for valid warranty,
                if not invalid_format and not invalid_BIL_assets and not excess_tags:
                    get_expiration_date(computer, json_data)
                    get_accidental_damage(computer, json_data)
                    get_ship_date(computer, json_data)
                    get_model(computer, json_data)
                else:
                    computer.exp_date = ""
                    computer.accidental_damage = ""
                    computer.ship_date = ""
                    computer.model = ""

                #write new row to cmdb.csv
                #operating system
                row[20] = line[2]

                #uanet id
                if(line[1] != "Unknown"):
                    split_id = line[1].split("\\")
                    row[22] = split_id[1]

                #deployed
                row[1] = "Deployed"

                #computer name
                row[23] = line[0]

                row[27] = computer.ship_date
                row[26] = computer.exp_date
                row[30] = computer.accidental_damage
                row[18] = serial_number
                cmdb_writer.writerow(row)

            #write new row as a string
            #
            #rowString = ''.join(row)
            #cmdb.write(rowString + '\n')
