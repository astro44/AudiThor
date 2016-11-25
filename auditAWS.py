#!/usr/bin/env python27
#sumo2 astro_sk$ zip -r9 ../SUMO3.zip *

#MAIN ENTRY POINT
import sys, os, platform
import time
import boto3
import json

import auditMeth
import amazonsvc.awsconnect
from amazonsvc.awsconnect import awsConnect
import multiprocessing.dummy as mp

## *** DO NOT DELETE THE BELOW IMPORTS  THEY ARE REFERENCED DYNAMICALY *** ##
from amazonsvc.applicationsvc import ApplicationService
from amazonsvc.compute import Compute
from amazonsvc.database import Database
from amazonsvc.management import Management
from amazonsvc.storage import Storage

from botocore.exceptions import ClientError



class AudiThor():
    #def main(self):
        #global aws_key,aws_secret, region
        #self.listLambdas

    currentCredential=None 
    def getCredential(self):
        return self.currentCredential



    ###################################################
    ##### MAIN audit method FOR ALL RESOURCES   #######
    ###################################################
    def awsResources(self,region, useAccounts=False, acct=None, multiThread=False):

       # regular expressions needed for each service type


       # regx = Compute.getServices().copy()
       # regx.update(ApplicationService.getServices())
       # regx.update(Database.getServices())
       # regx.update(Management.getServices())
       # regx.update(Storage.getServices())
        #regx = Database.getServices().copy()
        ## FINAL ##
        regx = Compute.getServices().copy()
        regx.update(ApplicationService.getServices())
        regx.update(Database.getServices())
        regx.update(Storage.getServices())
        regx.update(Management.getServices())

        ## TESTING ##
        #regx = ApplicationService.getServices().copy()
        #regx.update(Compute.getServices())

        aws_rsrc={}
        amazonsvc.awsconnect.stsClient_init()
        sts_client = amazonsvc.awsconnect.stsClient
        #sts_client.

        objs = []
        pyObj={}
        print 'mthread==',multiThread


        #pyObj[stitle] = {'account': str(k), 'tables': None}
        # Used to determine if using Accounts or Names for Environment based Listing
        if useAccounts:
            if acct is not None:
                envs =acct
            else:
                current,envs = auditMeth.loadConfig(configPath, None)
                region = current.mRegion
            #print 'THAT WAS environments....'
            #return {'a':'test one','b':'test2'}
            for aID, e in envs.items():
                titleIN ="%s : [%s]"%(e['title'],aID)
                aconnect = awsConnect( aID, e['eID'],e['role'], sts_client, region, True, multiThread )
                aconnect.connect()
                objs.append([titleIN])
                pyObj[titleIN]={}
                #aconnect._session
                print ("Environment: %s" % e['title'])
                for svc, exp in regx.items():
                    svcDomain = exp['ref']
                    svcDomain.global_accounts= envs
                    current = type('obj', (object,), {'owner': exp['owner'], 'regx': regx[(svc)]['rx'], 'svc':svc})
                    lst = getattr(svcDomain, '%sLists'%(svc)) (current, aconnect)
                    #aconnect.__get_client__(svc)
                    auditMeth.joinRecordList( aws_rsrc, svc, aID, lst)
                    aws_rsrc['%sfound'%(svc)], items,rows = \
                        getattr( svcDomain, '%sItem'%(svc) )( current, aconnect, lst  )
                    pyObj[titleIN]['%s'%(svc)]=rows
                    #print items
                    #break
                    objs = objs + items
                    objs.append(["       ","          ","       ","        "])
            objs.append("       ")

        else:
            for aID, e in envs.items():
                titleIN ="%s : [%s]"%(e['title'],aID)
                aconnect = awsConnect( aID, e['eID'],e['role'], sts_client, region )
                #aconnect.connect()
                objs.append([titleIN])
                #aconnect._session
                print ("Environment: %s" % e['title'])
                for svc, exp in regx.items():
                    svcDomain = exp['ref']
                    svcDomain.global_accounts= self.global_accounts
                    current = type('obj', (object,), {'owner': exp['owner'], 'regx': exp[(svc)]['rx'], 'svc':svc})
                    lst = getattr(svcDomain, '%sLists'%(svc)) (current, aconnect)
                    #aconnect.__get_client__(svc)
                    auditMeth.joinRecordList( aws_rsrc, svc, aID, lst)
                    aws_rsrc['%sfound'%(svc)], items = \
                        getattr( svcDomain, '%sItem'%(svc) )( current, aconnect, lst  )
                    objs = objs + items
                objs.append(["       ","          ","       ","        "])
            objs.append("       ")

            objs.append(["ORPHANS (missing label for environment)"])
            for svc in regx:
                svc_rx=regx[(svc)]['rx']
                owner=regx[(svc)]['owner']
                if len(aws_rsrc['%sfound'%(svc)]) < len(aws_rsrc['l_%s_%s'%(svc, '')]):
                    objs.append(["-----%s-%s~~~INVALID~~~"%('[MM]',svc),"---------------","---------------","---------------"])
                    objs = getattr(regx[(svc)]['classin'],  '%sMissing'%(svc))(
                            owner, aws_rsrc['%sfound'%(svc)],
                            objs,aws_rsrc['a_%s_%s'%(svc,'')],
                            aws_rsrc['l_%s_%s'%(svc, '')],
                            svc_rx,region)
        return (objs,pyObj)



    ###################################################################################################
    ###################################################################################################
    ###################################################################################################
    ##  AUDITING for each service requires 4 functions <svc>Lists <svc>Item <svc>Define and <svc>Missing
    ## make sure these functions are in the appropriate aws domain (compute, storage..etc..) 
    ## DON'T FORGET TO ADD THE IMPORT AT THE TOP OF THIS PAGE!!!! 

    ####  <svc>Lists loops to find all records for a given environment e['all'] or envs[i]['all'] for loose types
    ####  <svc>Item loops to find each record for a given environment e['all'] or envs[i]['all'] for loose types
    ####  <svc>Define adds the values for each attribute given the <svc>Item record and appends it to the objs array
    ####  <svc>Missing behaves the same as <svc>Item only that the list looped are exceptions that don't belong to any one env

    ######### (auditNetwork.py[VPC subnets ACLs etc...] auditStored.py[rds,dyn,elcache,S3] auditAccess.py[Roles,policies, etc..] auditProcess.py[Ec2, lambda ..] ...etc.)



def executeLambda( ploadin,que=None):
    global Main_bucket, threadEvent, Main_method, mRegion
    if threadEvent is None:
        event = 'RequestResponse'
    else:
        event = threadEvent
    print ('     ***  NNEEWW **** MASTER EXECUTE LAMDA  ***  ***  ', event)
    pload = {'defined':ploadin}
    session = boto3.session.Session()
    client = session.client('lambda', mRegion)

    response = client.invoke(
            FunctionName= Main_method,
            InvocationType = event,
            Payload        = json.dumps(pload)
            #Payload        = pload
        )
    if (event=='Event'):
        return None
    minionData =json.loads(response['Payload'].read())
    if minionData.has_key("stackTrace"):
        return (['ERROR OCCURED',ploadin.keys()[0]],
                {ploadin.keys()[0]:{'other':[{'effect':'ERROR','message':minionData}]  } } )
    else:
        print "  COMPLETE "
    if que is not None:
        que.put(( minionData['objs'], minionData['pyObj']))
    return ( minionData['objs'], minionData['pyObj'])

Main_method=None
Main_bucket=None
threadEvent=None
mRegion = None
configPath='auditCONFIG.yaml'
inLambda=True

#requires roles setup for full s3 bucket permission
#requires s3 bucket to exist
#requires lambda execution permission

def lambda_handler(event,context):
    global mRegion, Main_bucket,Main_method, threadEvent
    current, envs = auditMeth.loadConfig(configPath, None)
    print envs
    mRegion = current.mRegion
    vendor =current.vendor
    Main_bucket=current.Main_bucket
    Main_method =current.method
    threadEvent = current.threadEvent
    if not auditMeth.bucketExists(Main_bucket):
        return '[E] bucket needed to proceed %s'%(Main_bucket)
    s3Enabled = True
    payLoad = None
    vname = vendor.lower()
    start_time = time.time()
    keyMaster = current.s3_keyMaster%(vname)
    keyFolder=current.s3_keyFolder
    print '......START NEW LAMBDA.......'
    lists = AudiThor()
    useAccountID=True
    upload2S3=True
    isThreaded = True   #lambda will choke if this is not setup correctly
    print event
    if event.has_key('defined'):
        payLoad = event['defined']
    elif event.has_key('Records'):
        print 'RECORDS FOUND'
        if 'complete.json' in event['Records'][0]['s3']['object']['key']:
            print ' got results'
            listReady = lambda_s3Match( Main_bucket, '%s/%s'%(keyFolder,keyMaster),current.s3_keyComplete )
            if listReady:
                mlist,objs, pyObj = listReady
                #print pyObj
                auditMeth.lambda_writeResult(upload2S3, pyObj, Main_bucket,current.sumoName, current.SUMOPOINT)
                auditMeth.s3Cleanup(keyMaster,Main_bucket,mlist,keyFolder, current.s3_keyComplete, current.s3_key)
                #print("--- %s seconds A---" % (time.time() - start_time))
                return 'Completed Process... cleanup in progress....'
            else: #NOT READY KILL process. NEXT EVENT will CHECK
                return listReady
    if len(envs) <2:
        print '  ONLY ONE ACCOUNT FOUND --->'
        objs, pyObj = lists.awsResources(region, useAccountID, envs, threaded  )
        auditMeth.lambda_writeResult(upload2S3, pyObj, Main_bucket,current.sumoName)
        print("--- %s seconds A---" % (time.time() - start_time))
    else:
        s3 = boto3.resource('s3')
    # MASTER LAMBDA push all execution to each lambda per Account
        if payLoad is None:  #MASTER------------------
            masterFile = '/tmp/%s' % (keyMaster)
            auditMeth.writeToJSON(masterFile, [a for a in envs])
            try:
                s3.Object(Main_bucket, '%s/%s'%(keyFolder,keyMaster) ).load()
                print ('[W] STOP MASTER redundant client:%s'%(vendor))
                return None
            except ClientError as e:
                if e.response['Error']['Code'] == "404":
                    s3c= boto3.client('s3')
                    s3c.upload_file(masterFile, Main_bucket, '%s/%s'%(keyFolder,keyMaster) )
            return lambda_multiMaster(start_time,isThreaded,envs,s3Enabled)
    # CHILD LAMBDA  make sure no others working on same account before continuing
        else:                 #CHILD------------------
            if s3Enabled:
                acct=payLoad.keys()[0]
                key = current.s3_key % (acct)
                keyComplete = current.s3_keyComplete%(acct)
                try:
                    s3.Object(Main_bucket, '%s/%s'%(keyFolder, keyComplete)).load()
                    print ('[W] STOP CHILD finished %s',acct)
                    return None
                except ClientError as e:
                    try:
                        s3.Object(Main_bucket, '%s/%s'%(keyFolder, key)).load()
                        print ('[W] STOP CHILD redundant %s',acct)
                        return None
                    except ClientError as e:
                        if e.response['Error']['Code'] == "404":
                            #create file before continuing
                            childFile = '/tmp/%s' % (key)
                            auditMeth.writeToJSON(childFile,{'acct':acct,'start':start_time})
                            s3c = boto3.client('s3')
                            s3c.upload_file(childFile, Main_bucket, '%s/%s'%(keyFolder, key) )

                #child now read message one at a time
                result =lambda_multiChild(start_time,lists, payLoad, isThreaded, useAccountID)
                #now add results to S3
                childResult = '/tmp/%s' % (keyComplete)
                auditMeth.writeToJSON( childResult, result )

                s3c = boto3.client('s3')
                s3c.upload_file( childResult, Main_bucket, '%s/%s'%(keyFolder, keyComplete) )

                print result
                ##add to json file for later consumption
            else:
                return lambda_multiChild(start_time,lists, payLoad,isThreaded,useAccountID )
    return None


def lambda_s3Match(bucket,keyMaster, keyComplete):
    s3 = boto3.resource('s3')
    client = boto3.client('s3')
    mainList = s3.Object(bucket, keyMaster).get()
    mlist = json.loads(mainList['Body'].read().decode('utf-8'))
    files = client.list_objects(Bucket=bucket)
    found=[]
    for acct in mlist:
        aname = keyComplete%(acct)
        for file in files.get('Contents'):
            key = file['Key']
            if aname in key :
                found.append(key)
                break
    if len(found) == len(mlist):
        #collect total files and aggregate
        objs=[]
        pObjs={}
        for o in found:
            print o
            s3File = s3.Object(bucket,o).get()
            datain = s3File['Body'].read().decode('utf-8')
            data = json.loads(datain)
            obj=data['objs']
            pyObj=data['pyObj']
            objs= objs+obj
            pObjs.update(pyObj)


        return (mlist,objs, pObjs)
    else:
        return False



def lambda_multiChild(start_time,lists, payLoad, isThreaded, useAccountID):
    print ' .NNEEWW. minion ..'
    objs,pyObj=lists.awsResources(mRegion, useAccountID, payLoad, isThreaded)
    minionData = {'objs':objs,'pyObj':pyObj}
    print("--- %s seconds C---" % (time.time() - start_time))
    return minionData


def lambda_multiMaster(start_time,isThreaded, envs, s3Enabled):
    global threadEvent
    objs = []
    q = None
    if isThreaded:
        threadEvent = 'Event' if s3Enabled else None
        print 'is THREADED mode'
        totalItems = len(envs)
        pools = auditMeth.poolThreadNumber(totalItems, mp.cpu_count())

        p = mp.Pool(1 if pools == 0 else pools)
        testing = False

        if not testing:
            xx = ({aID: e} for aID, e in envs.items())
            print xx
            results = p.map(executeLambda, ( {aID: e} for aID, e in envs.items() ) )
        # results = None
        return results
    else:
        print 'is multi PROCESSOR mode'
        p = mp.Pool()
        m = mp.Manager()
        q = m.Queue()
        for aID, e in envs.items():
            # client = aconnect.__get_client__('lambda')
            pload = None
            pload = {aID: e}
            print pload
            results=p.apply_async(executeLambda, (pload, q))

    p.close()
    p.join()
    pyObj = {}
    if isThreaded:  ### WORKS IN AWS LAMBDA  ###
        for que in results:
            newobjs, newPyObj = que
            objs = objs + newobjs
            pyObj.update(newPyObj)
    else:
        while not q.empty():
            newobjs, newPyObj = q.get()
            objs = objs + newobjs
            pyObj.update(newPyObj)

    # lambda_writeResult(upload2S3, pyObj, Main_bucket,sumoName)

    print("--- %s seconds B---" % (time.time() - start_time))
    return results




if os.isatty(sys.stdin.fileno()):
    print " NOOOO  --->  OS ISATTY  ENTRY......."
    #DEBUG MODE RUNNING FROM TERMINAL
    prompt = sys.argv[1]
    if 'help' in prompt:
            print "used to get list of resources from dest regions use Account ID's for environments"
            print "python awsAuditCSV.py us-east-1,True"
            print "use False if only looking at Names to distinguish between 'environments' "
            print "python awsAuditCSV.py us-east-1,False"
            ## 'ap-southeast-2'  'us-west-1' 
    else:
            values = prompt.split(',')
            lists = AudiThor()
            #awscredent = getAWSCredentials()
            #aws_key=awscredent[0]
            #aws_secret=awscredent[1]
            useAccountID=False
            if 'True' in values[1]:
                useAccountID=True
            lists.awsResources(values[0],useAccountID)
            #lists.main()
else:
    # RUN AS LAMBDA SCRIPT or CRON
    print '         LAMBDA or CRON....'
    print platform.release()
    if 'amzn' in platform.release():
        print '       AMAZON ENVIRONMENT'
        threaded = True
    else:
        print '          NOT AMAZON'
        inLambda=False
    pass





if __name__ == '__main__':
    if not inLambda:
        print '....--NOOOOO--...IN MAIN..TEST......'
        start_time = time.time()
        testLambda=True
        threaded=True
        if testLambda:
            lambda_handler({'sweet':None},None)
        else:
            lists = AudiThor()
            useAccountID=True
            objs,pyObj=lists.awsResources('us-east-1', useAccountID,None,threaded)

            auditMeth.writeToCSV('auditLists%s.csv' % ('_all_'), objs)
            #auditMeth.writeToJSON('auditLists%s.json' % ('_all_'), pyObj)
            #auditMeth.writeToJSONSUMO('sumo-audit-silver.json', pyObj,True)
        print("--- %s seconds ---" % (time.time() - start_time))


