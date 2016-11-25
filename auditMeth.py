#!/usr/bin/env python27

import csv
import colorama
import os.path
from colorama import Fore, Back, Style
import re, string
import  json
from decimal import *
import datetime
import boto3
from botocore.client import ClientError

from botocore.vendored import requests
from zlib import compress
import yaml



#used for coloured output  !!not needed in cron
colorama.init()


rs_chr=r'[^\w\d-]'
rs_2=r'(.*)-(.*)-(.*?)$'
rs_3=r'(.*)-(.*)-(.*)-(.*?)$'
rs_4=r'(.*)-(.*)-(.*)-(.*)-(.*?)$'
rs_5=r'(.*)-(.*)-(.*)-(.*)-(.*)-(.*?)$'
rs_ec2=r'(.*)-(.*)-(.*)-\[(.*)\]-(.*)-(.*?)$'
rs_rds=r'(.*)-(.*)-(.*)-\[(.*)\]$'
rs_rgrps=r'(.*)-(.*)-\[(.*)\]-(.*?)$'

def poolThreadNumber(totalItems, cpucount = 1):
    cpucount
    print '-->',totalItems
    pools = 0 if totalItems < 2 else totalItems
    pools = 12 if totalItems > 12 else pools
    return pools

def upCase(string):
    is_uppercase_letter = True in map(lambda l: l.isupper(), string)
    if not is_uppercase_letter:
        m = re.findall( rs_chr, string)
        if len(m)>0:
            is_uppercase_letter = True

    return is_uppercase_letter
#### checks agains the rs_<segments> above returns total groups(.*) found and a list of each group in order 
#### most cases the first group is the {entity} and the second is the {buisness Unit}
def conforms2Naming(string, regX,env):
    m = re.match( regX, string, re.M)
    #s = re.findall( regX, string)
    namesIn=()
    total=4
    if m:
        num=len(m.groups())
        if m.group(1) is not env and m.group(2) is not env and m.group(3) is not env:
            if num is 2:
                namesIn= (m.group(1),m.group(2))
            if num is 3:
                namesIn= (m.group(1),m.group(2),m.group(3))
            if num is 4:
                namesIn= (m.group(1),m.group(2),m.group(3),m.group(4))
            if num is 5:
                namesIn= (m.group(1),m.group(2),m.group(3),m.group(4),m.group(5))
                total=5
            if num is 6:
                namesIn= (m.group(1),m.group(2),m.group(3),m.group(4),m.group(5),m.group(6))
                total=6
            if num is 7:
                namesIn= (m.group(1),m.group(2),m.group(3),m.group(4),m.group(5),m.group(6),m.group(7))
                total=7
            return (total,namesIn)
    total=0
    return (total,None)
def namingError(errorInt):
    switcher = {
        1: "[E] Caps",
        2: "[E] Segment",
        3: "[E] Caps/Segment",
        4: "[E] VPC",
        7: "[E] Caps/Segment/VPC"
    }
    return str(switcher.get(errorInt, "CLEAR"))
def printColor(a_msg):
    spacer="  "
    for msg in a_msg:
        if ('[E]' in msg):
            print(Fore.RED + msg + Style.RESET_ALL)
        elif '-----' in msg:
            print(Fore.BLACK +Back.WHITE + msg + Style.RESET_ALL)
        elif '_____' in msg:
            print(spacer+Fore.BLACK +Back.CYAN + msg + Style.RESET_ALL)
        elif '.....' in msg:
            print(spacer+spacer+Fore.BLACK +Back.GREEN + msg + Style.RESET_ALL)
        else:
            print (msg)

def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)
def writeToFile(pathandfile, inputmessagestr):
    stream = open(pathandfile, 'w')
    stream.write(inputmessagestr)
    stream.close()

def writeToCSV(pathfile, objects):
    with open(pathfile, 'wb') as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
        writer.writerows(objects)

def lambda_writeResult(upload2S3, pyObj, bucket, completedName, SumoEndPoint):
    sname = completedName
    sumoFile = '/tmp/%s' % (sname)
    print ('    @@@@  file2upload::%s  to %s' % (sumoFile, bucket))
    texts =writeToJSONSUMO(sumoFile, pyObj, upload2S3)
    if upload2S3:
        s3 = boto3.client('s3')
        s3.upload_file(sumoFile, bucket, 'final_%s' % sname)
    headers = {'Content-Encoding': 'deflate'}
    requests.post(SumoEndPoint, compress('\n'.join(texts)), headers=headers)


def writeToJSON(pathfile, objects):
    with open(pathfile, 'wb') as outfile:
        json.dump(objects, outfile, cls=CommonEncoder)
        #json.dump(objects, outfile, cls=CommonEncoder, indent=4)
def writeToJSONSUMO(pathfile, objects,writeFile):
    #reduce to line by line to mimic log entries
    txt=[]
    for account,obj in objects.items():
        for svc,records in obj.items():
            for row in records:
                rowIN =row
                rowIN['dept']=account
                rowIN['svc']=svc
                txt.append(json.dumps(rowIN, cls=CommonEncoder))
    if writeFile:
        with open(pathfile, 'wb') as outfile:

            for t in txt:
                outfile.write("%s\n"% t)
            #json.dump(objects, outfile, cls=CommonEncoder)
            #json.dump(objects, outfile, cls=CommonEncoder, indent=4)
    return txt

def s3Cleanup(keyMaster,bucket,mlist,folder, keyComplete,keyin):
    s3 = boto3.client('s3')
    keys=[]
    keys.append({'Key':folder+'/'+keyMaster})
    for acct in mlist:
        name_end = keyComplete%(acct)
        name=keyin % (acct)
        keys.append({'Key':folder+'/'+name }  )
        keys.append({'Key':folder+'/'+name_end }  )
    result=s3.delete_objects(Bucket=bucket,Delete={'Objects':keys} )
    print result

def joinRecordList(aws_rsrc,svc,e,data):

    if  aws_rsrc.has_key('l_%s_%s'%(svc,e)):
         aws_rsrc['l_%s_%s'%(svc,e)]+=data
    else:
         aws_rsrc['l_%s_%s'%(svc,e)]=data
    return aws_rsrc['l_%s_%s'%(svc,e)]



def loadConfig(fullpath,s3bucket=None):
    if s3bucket:
        # dad
        print 's3 is on'
    else:
        if not os.path.isfile(fullpath):
            return None
        with open(fullpath, 'ru') as stream:
            exp=yaml.load(stream)
    config=exp['auditConfig']
    global_accts = exp['globalAccounts']
    print global_accts

    current = type('obj', (object,), {
                'Main_bucket': config['main_bucket'],
                'method': config['method'],
                's3_key': config['key'],
                's3_keyComplete': config['key_complete'],
                's3_keyMaster': config['key_master'],
                's3_keyFolder': config['key_folder'],
                'threadEvent': config['thread_event'],
                'threaded': config['threaded'],
                'mRegion': config['region'],
                'vendor': config['vendor'],
                'sumoName': config['sumo_file'],
                'SUMOPOINT': config['sumo_endpoint']  }
            )
    return (current, global_accts)



def nameCheck(owner,name,regX,env):        
    total,validName=conforms2Naming(name,regX,env)
    upCase(name)
    validCaps=upCase(name)
    audit="PASS2"
    if owner is "":
        owner="NA"
    errorInt=0
    if upCase(name):
        errorInt=1
    if not validName:
        if errorInt is 1:
            errorInt=3
        else:
            errorInt=2
    audit=namingError(errorInt)
    #print audit
    return audit,owner

def bucketExists(name):
    s3  = boto3.resource('s3')
    try:
        s3.meta.client.head_bucket(Bucket=name)
        return True
    except ClientError:
        return False


class CommonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.isoformat()
        if isinstance(o,(tuple,set)):
            return list(o)
        if isinstance(o,Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(CommonEncoder, self).default(o)


ec2_hrs_month=640
ec2_prices={'m1.small':{'cost':.044},
            'm1.medium':{'cost':.087},
            'm1.large':{'cost':.175},
            'm1.xlarge':{'cost':.35},
            'c1.medium':{'cost':.13},
            'c1.xlarge':{'cost':.52},
            'cc2.8xlarge':{'cost':2},
            'cg1.4xlarge':{'cost':2.1},
            'm2.xlarge':{'cost':.245},
            'm2.2xlarge':{'cost':.49},
            'm2.4xlarge':{'cost':.98},
            'cr1.8xlarge':{'cost':3.5},
            'hi1.4xlarge':{'cost':3.1},
            'hs1.8xlarge':{'cost':4.6},
            't1.micro':{'cost':.02},

            't2.nano': {'cost': .0065},
            't2.micro': {'cost': .013},
            't2.small': {'cost': .026},
            't2.medium': {'cost': .052},
            't2.large': {'cost': .104},

            'm4.large': {'cost': .12},
            'm4.xlarge': {'cost': .239},
            'm4.2xlarge': {'cost': .479},
            'm4.4xlarge': {'cost': .958},
            'm4.10xlarge': {'cost': 2.394},
            'm4.16xlarge': {'cost': 3.83},

            'm3.medium': {'cost': .067},
            'm3.large': {'cost': .133},
            'm3.xlarge': {'cost': .266},
            'm3.2xlarge': {'cost': .532},

            'c4.large': {'cost': .105},
            'c4.xlarge': {'cost': .209},
            'c4.2xlarge': {'cost': .419},
            'c4.4xlarge': {'cost': .838},
            'c4.8xlarge': {'cost': 1.675},

            'c3.large': {'cost': .105},
            'c3.xlarge': {'cost': .21},
            'c3.2xlarge': {'cost': .42},
            'c3.4xlarge': {'cost': .84},
            'c3.8xlarge': {'cost': 1.68},

            'p2.xlarge': {'cost': .9},
            'p2.8xlarge': {'cost': 7.2},
            'p2.16xlarge': {'cost': 14.4},

            'g2.xlarge': {'cost': .65},
            'g2.8xlarge': {'cost': 2.6},

            'x2.16xlarge': {'cost': 6.669},
            'x2.32xlarge': {'cost': 13.338},

            'r3.large': {'cost': .166},
            'r3.xlarge': {'cost': .333},
            'r3.2xlarge': {'cost': 0.665},
            'r3.4xlarge': {'cost': 1.33},
            'r3.8xlarge': {'cost': 2.66},

            'i2.xlarge': {'cost': .853},
            'i2.2xlarge': {'cost': 1.705},
            'i2.4xlarge': {'cost': 3.41},
            'i2.8xlarge': {'cost': 6.82},

            'd2.large': {'cost': .69},
            'd2.2xlarge': {'cost': 1.38},
            'd2.4xlarge': {'cost': 2.76},
            'd2.8xlarge': {'cost': 5.52},

        }