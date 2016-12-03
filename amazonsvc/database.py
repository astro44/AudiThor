


from auditMeth import nameCheck
from auditMeth import printColor
import datetime


import multiprocessing.dummy as mp
from awsconnect import awsConnect as Connector

import auditMeth





awsConnect=awsCurrent=None



class Database:
    def __init__(self):
        self.services = {
            'dynamo': {'rx': auditMeth.rs_3, 'owner': 'Javier','ref':self},
            'rds': {'rx': auditMeth.rs_rds, 'owner': 'James', 'ref':self}
         }
        #self.services = {
         #   'dynamo': {'rx': auditMeth.rs_3, 'owner': 'Ralph','ref':self}
         #}

    @staticmethod
    def getServices():
        c = Database()
        return c.services


    ##############################
    #####   RDS METHODS   #####
    ##############################
    def rdsLists(self,current, aconnect):
        global awsConnect, awsCurrent
        awsConnect=aconnect
        awsCurrent=current
        client = aconnect.__get_client__(current.svc)
        rawItems = client.describe_db_instances(MaxRecords=100)['DBInstances']
        return rawItems

    def rdsMissing(self,current, aconnect, itemlist,lfound):
        objs=[]
        objs.append(['Name', 'Audit', 'Owner', 'Engine','Size (GB)','Instance','MutliAZ','VPC', 'last_Modified'])
        for unit in itemlist:
            name = unit['DBInstanceIdentifier']
            if name in lfound:
                continue
            objs = self.rdsDefine(current,aconnect,objs,unit,name)
            printColor(['[E] RDS [%s] Missing correct naming....in .%s'%(name,aconnect._region)])
        return objs

    def rdsItem(self,current, aconnect, itemlist):
        added=False
        printColor(['_____LISTING RDS [] now....in .%s'%(aconnect._region)])
        threaded = aconnect.getMultiThread()
        nEnv = aconnect._env
        lfound = []
        objs=[]
        rows=[]

        pools = 2  # 171.35 seconds  #168 seconds
        totalItems = len(itemlist)
        q = None
        if threaded:
            pools= auditMeth.poolThreadNumber(totalItems, mp.cpu_count())

            p = mp.Pool(1 if pools == 0 else pools)

        else:
            p = mp.Pool()
            m = mp.Manager()
            q = m.Queue()
        if totalItems > 0:
            objs.append(['Name[%s]'%(current.svc), 'Audit', 'Owner', 'Engine','Size (GB)','Instance','MutliAZ','VPC', 'last_Modified', 'connections','cost'])
        if not threaded:
            for unit in itemlist:
                name = unit['DBInstanceIdentifier']
                #sg=unit['VpcSecurityGroups'][0]['VpcSecurityGroupId']
                #ec2 = aconnect.__get_client__('ec2')
                #sgUnit = ec2.describe_security_groups(GroupIds=[sg])['SecurityGroups'][0]
                #account = sgUnit['OwnerId']
                if nEnv in name or aconnect._useAccounts:
                    if pools == 0:
                        objs, row = rdsDefine(unit,name,q)
                    else:
                        getit = p.apply_async(rdsDefine, (unit,name,q))
                    #getit.get()
                    lfound.append(name)

                    #objs,row = self.rdsDefine(current,aconnect,objs,unit,name)
                    #rows.append(row)
        else:
            #print itemlist
            lfound = [unit['DBInstanceIdentifier'] for unit in itemlist]
            results = p.map(rdsDefine,  ( unit for unit in itemlist )  )


        if pools > 0:
            p.close()
            p.join()
            if threaded:
                for que in results:
                    newobjs, row = que
                    #print ' DYNAMO --got[C] result', row
                    objs = objs + newobjs
                    rows.append(row)
            else:
                while not q.empty():
                    newobjs, row = q.get()
                    objs = objs + newobjs
                    # print newobjs
                    rows.append(row)
        print objs
        return (lfound,objs,rows)



    ##############################
    #####   DYNAMO METHODS   #####
    ##############################
    def dynamoLists(self,current, aconnect):
        global awsConnect, awsCurrent
        awsConnect=aconnect
        awsCurrent=current
        client = aconnect.__get_client__('dynamodb')
        rawItems = client.list_tables(Limit=100)['TableNames']
        return rawItems
    def dynamoMissing(self,current, aconnect, itemlist, lfound):
        objs =[]
        objs.append(['Name', 'Audit','Owner', 'Status', 'Partition key', 'indexes', 'totalRead', 'totalWrite'])

        client = aconnect.__get_client__(current.svc)
        for name in itemlist:
            unit=client.describe_table(TableName=name)['Table']
            if name in lfound:
                continue
            objs=self.dynamoDefine(current,aconnect,objs,unit,name)
            printColor(['[E] DynamoDB [%s] Missing correct naming....in .%s'%(name,aconnect._region)])
        return objs

    def dynamoItem(self,current, aconnect, itemlist):
        added=False
        printColor(['_____LISTING DynamoDB [] now....in .%s'%(aconnect._region)])
        threaded = aconnect.getMultiThread()
        nEnv = aconnect._env
        lfound =[]
        objs = []
        rows=[]

        pools = 2  # 171.35 seconds  #168 seconds
        totalItems = len(itemlist)
        if threaded:
            pools= auditMeth.poolThreadNumber(totalItems, mp.cpu_count())
            if pools >0:
                p = mp.Pool(pools)
            elif pools == 0:
                threaded=False
        else:
            p = mp.Pool()
            m = mp.Manager()
            q = m.Queue()
        if totalItems > 0:
            objs.append(['Name[%s]'%(current.svc), 'Audit', 'Owner', 'Status', 'PartitionKey', 'indexes', 'totalRead', 'totalWrite'])

        client = aconnect.__get_client__('dynamodb')
        if not threaded:
            for name in itemlist:
                unit=client.describe_table(TableName=name)['Table']
                #account = dunit['TableArn']
                if nEnv in name or aconnect._useAccounts:
                    if pools == 0:
                        objs, row = dynamoDefine(unit,name,q)
                    else:
                        getit = p.apply_async(dynamoDefine, (unit,name,q))
                    #getit.get()
                    lfound.append(name)
                    #objs,row=self.dynamoDefine(current,aconnect,objs,unit,name)
                    #rows.append(row)
        else:
            #print itemlist
            lfound = [name for name in itemlist]
            #print lfound
            #print 'client ready?'
            #dd = client.describe_table(TableName='Tags')['Table']
            #print dd
            results = p.map(dynamoDefine,  ( client.describe_table(TableName=name)['Table']  for name in itemlist )  )

        if pools > 0:
            p.close()
            p.join()
            if threaded:
                for que in results:
                    newobjs, row = que
                    #print ' RDS --got[C] result', row
                    objs = objs + newobjs
                    rows.append(row)
            else:
                while not q.empty():
                    newobjs, row = q.get()
                    objs = objs + newobjs
                    # print newobjs
                    rows.append(row)
        return (lfound,objs,rows)
#--- 398.831588984 seconds ---




###########################################################################
##########################  RDS MULTI-THREAD ##############################
##############################  START  ####################################
###########################################################################



def rdsDefine( unit,name=None,que=None):
    if name == None:
        name = unit['DBInstanceIdentifier']
    multiThread = awsConnect.getMultiThread()
    if multiThread:
        #aconnect = Connector.callThreadedService(awsConnect._eID, awsConnect._env, awsConnect._role,)
        sts = Connector.stsClient()
        aconnect = Connector(awsConnect._env, awsConnect._eID, awsConnect._role, sts, awsConnect._region)
        aconnect.connect()
    else:
        aconnect = awsConnect
    current=awsCurrent
    objs=[]
    audit, owner = nameCheck(current.owner, name, current.regx, aconnect._env)
    engine = unit['Engine']
    size = unit['AllocatedStorage']
    itype = unit['DBInstanceClass']
    multiaz = unit['MultiAZ']
    vpc = mod = None
    if unit.has_key('DBSubnetGroup'):
        vpc = unit['DBSubnetGroup']['VpcId']
    if unit.has_key('LatestRestorableTime'):
        dd = unit['LatestRestorableTime']
        mod = dd.strftime('%m,%d %Y')
    multi=1 if multiaz=="FALSE" else 2
    cost = auditMeth.ec2_prices[ itype[3:] ]['cost']*auditMeth.ec2_hrs_month*multi
    hrs = 24 * 7  # to include a week
    connections = rdsConnections(aconnect, name, hrs)
    nt = [name, audit, owner, engine, size, itype, multiaz, vpc, mod, connections]
    objs.append(nt)
    row = {'Name': name, 'Audit': audit, 'Owner': owner, 'Engine': engine, 'SizeHD': size, 'Instance': itype,
           'MultiAZ': multiaz, 'VPC': vpc, 'last_Modified': mod, 'connections': connections,'cost':cost}
    if not multiThread:
        if que is not None:
            que.put((objs, row))
    return (objs, row)


def rdsConnections( aconnect, instance, hrs=1.5):
    end = datetime.datetime.utcnow()
    maxAvg = 2
    period = (hrs * 60 * 60) / 1440
    if period < 300:
        period = 300  # or 5mins
    period_min = period / 60
    minimum_logs_needed = hrs * 60 / period_min - 1  # subract 1 since init is not included time based
    start = end - datetime.timedelta(hours=hrs)
    cw = aconnect.__get_client__('cloudwatch')
    ddx = cw.get_metric_statistics(
        Period=period,
        StartTime=start,
        EndTime=end,
        Unit='Count',
        MetricName='DatabaseConnections',
        Namespace='AWS/RDS',
        Statistics=['Maximum'],
        Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': instance}]
    )

    avg = instanceAvg(ddx, maxAvg)
    if avg > 0:
        print ('-- %s  %s' % (instance, avg))
    return avg


def instanceAvg( avgs, maxAvg):
    total = 0
    lowest = 0
    datapoints = avgs['Datapoints']
    for avg in datapoints:
        av = float(avg['Maximum'])
        if lowest == 0 and av < 1:
            lowest = 1
            continue
        total = total + av

    if total == 0:
        return 0
    return round(total / (len(datapoints) - lowest))









def dynamoDefine(unit,name=None,que=None):
    global awsConnect, awsCurrent
    if name == None:
        name = unit['TableName']
    objs=[]
    multiThread = awsConnect.getMultiThread()
    if multiThread:
        #aconnect = Connector.callThreadedService(awsConnect._eID, awsConnect._env, awsConnect._role,)
        sts = Connector.stsClient()
        aconnect = Connector(awsConnect._env, awsConnect._eID, awsConnect._role, sts, awsConnect._region)
        aconnect.connect()
    else:
        aconnect = awsConnect
    current=awsCurrent

    audit,owner=nameCheck(current.owner,name,current.regx,aconnect._env)
    table = unit
    stat = table['TableStatus']
    pkey = table['KeySchema'][0]['AttributeName']
    indexes=0
    reads=0
    writes=0
    if 'GlobalSecondaryIndexes' in table:
        indexes=len(table['GlobalSecondaryIndexes'])
        reads,writes = getDynamoRU(table['GlobalSecondaryIndexes'])
        reads+=table['ProvisionedThroughput']['ReadCapacityUnits']
        writes+=table['ProvisionedThroughput']['WriteCapacityUnits']
    nt =[name,audit,owner,stat,pkey,indexes,reads,writes]
    objs.append(nt)
    row={'Name':name,'Audit':audit,'Owner':owner,'Status':stat,'PartitionKey':pkey,'indexes':indexes,'totalReads':reads,'totalWrite':writes}
    if not multiThread:
        if que is not None:
            que.put((objs,row))
    return (objs,row)

    ##############################
    ### DYNAMO HELPER METHOD  ####
    ##############################
def getDynamoRU(aUnits):
    writes=0
    reads=0
    for a in aUnits:
        writes+=a['ProvisionedThroughput']['WriteCapacityUnits']
        reads+=a['ProvisionedThroughput']['ReadCapacityUnits']
    return (reads,writes)
        




















        