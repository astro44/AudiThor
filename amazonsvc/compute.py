
import copy

from auditMeth import nameCheck
from auditMeth import printColor
import datetime

import multiprocessing.dummy as mp
from awsconnect import awsConnect as Connector

import auditMeth

import re



#regx = {'api': {'rx': rs_2, 'owner': 'Brian'},
#        'lc': {'rx': rs_3, 'owner': 'Josh'}, 'asg': {'rx': rs_3, 'owner': 'Josh'}, 'sa': {'rx': rs_3, 'owner': 'Josh'},
#        'dynamo': {'rx': rs_3, 'owner': 'Ralph'}, 'rds': {'rx': rs_rds, 'owner': 'Ralph'},
#        'ecc': {'rx': rs_4, 'owner': 'Ralph'},
#        'ebs': {'rx': rs_3, 'owner': 'Josh'}, 'ec2': {'rx': rs_ec2, 'owner': 'Josh'},
#        'elb': {'rx': rs_4, 'owner': 'Josh'}, 'lambda': {'rx': rs_3, 'owner': 'Brian'},
#        'sns': {'rx': rs_3, 'owner': 'Kalpesh'}, 'sqs': {'rx': rs_3, 'owner': 'Kalpesh'},
#        'cloudformation': {'rx': rs_4, 'owner': 'josh'},
#        'rt': {'rx': rs_5, 'owner': 'Josh'}, 'sg': {'rx': rs_4, 'owner': 'Josh'}, 'sn': {'rx': rs_5, 'owner': 'Josh'},
#        'vpc': {'rx': rs_3, 'owner': 'Brian'}, 'igw': {'rx': rs_5, 'owner': 'Brian'},
#        'emrc': {'rx': rs_4, 'owner': 'Josh'},
#        's3': {'rx': rs_4, 'owner': 'Josh'}}

awsConnect=awsCurrent=None
multiThread=False

class Compute:
    def __init__(self):
        self.services = {
            'elb': {'rx': auditMeth.rs_4, 'owner': 'Richard','ref':self},
            'ec2': {'rx': auditMeth.rs_ec2, 'owner': 'Rafaela','ref':self},
            'lambda': {'rx': auditMeth.rs_3, 'owner': 'Simon','ref':self}
                    }
        #self.services = {
        #    'ec2': {'rx': auditMeth.rs_ec2, 'owner': 'Josh','ref':self},
        #    'lambda': {'rx': auditMeth.rs_3, 'owner': 'Chris','ref':self}
        #            }

    @staticmethod
    def getServices():
        c=Compute()
        return c.services




    ##############################
    #####   ELB METHODS   #####
    ##############################
    def elbLists(self,current, aconnect):
        client = aconnect.__get_client__(current.svc)  #elb
        rawItems =client.describe_load_balancers(PageSize=400)['LoadBalancerDescriptions']
        return rawItems

    def elbMissing(self,current, aconnect, itemlist,lfound):
        objs=[]
        objs.append(['Name', 'Audit', 'Owner', 'Total Instances', 'DNS', 'VPC'])
        for unit in itemlist:
            name = unit['LoadBalancerName']
            if name in lfound:
                continue
            objs = self.elbDefine(current,aconnect,objs,unit,name)
            printColor(['[E] ELB [%s] Missing correct naming....in .%s'%(name, aconnect._region)])
        return objs

    def elbItem(self,current, aconnect, itemlist):
        added=False
        printColor(['_____LISTING ELB [] now....in .%s'%(aconnect._region)])
        lfound = []
        objs =[]
        rows=[]
        nEnv = aconnect._env
        for unit in itemlist:
            name = unit['LoadBalancerName']
            account = unit['SourceSecurityGroup']['OwnerAlias']
            if nEnv in name or aconnect._useAccounts:
                lfound.append(name)
                if not added:
                    added=True
                    objs.append(['Name[%s]'%(current.svc), 'Audit', 'Owner', 'TotalInstances', 'VPC', 'DNS'])
                objs,row = self.elbDefine(current,aconnect,objs,unit,name)
                rows.append(row)
        return (lfound,objs,rows)

    def elbDefine(self,current,aconnect,objs,unit,name):
        audit,owner=nameCheck(current.owner,name, current.regx, aconnect._env)
        instances = len(unit['Instances'])
        vpc=None
        if unit.has_key('VPCId'):
            vpc = unit['VPCId']
        dns=unit['DNSName']
        nt=[name,audit,owner,instances,vpc,dns]
        objs.append(nt)
        row={'Name':name,'Audit':audit,'Owner':owner,'Total Instances':instances,'VPC':vpc,'DNS':dns}
        return (objs,row)




    ##############################
    #####   EC2 METHODS   #####
    ##############################
    def ec2Lists(self,current, aconnect):
        global awsConnect, awsCurrent
        awsConnect = aconnect
        awsCurrent = current
        rsrc = aconnect.__get_resource__(current.svc)
        #joinRecordList( aws_rsrc,svc,envs, aws_rsrc['a_%s_%s'%(svc,envs)].describe_instances()['Reservations'])
        #all_res = client.describe_instances()['Reservations']
        renamed = []
        all_ec2 = rsrc.instances.all()
        for i in all_ec2:
            inst = copy.copy(i.meta.data)
            inst['OwnerId'] = current.owner if current.owner != "" else i.image.owner_id
            if not inst.has_key('Platform'):
                inst['Platform'] = 'linux'

            inst['sgroups'] = ','.join([sg['GroupName'] for sg in inst['SecurityGroups']])
            inst_name = inst['InstanceId']
            if len(inst['Tags']) > 0:
                tags = filter(lambda t: t['Key'] == 'Name', inst['Tags'])
                if len(tags) > 0:
                    inst_name = tags[0]['Value']

            inst['Name'] = inst_name
            renamed.append(inst)

        return renamed

    def ec2Missing(self,current, aconnect, itemlist,lfound):
        objs =[]
        objs.append(['Name', 'Audit', 'Owner','type', 'Platform','SecurityGroups','Instance','Zone','VPC', 'State'])
        for unit in itemlist:
            name = unit['Name']
            if name in lfound:
                continue
            objs = self.ec2Define(current,aconnect,objs,unit,name)
            printColor(['[E] EC2 [%s] Missing correct naming....in .%s'%(name,aconnect._region)])
        return objs

    def ec2Item(self,current, aconnect, itemlist):
        printColor(['_____LISTING EC2 [] now....in .%s'%(aconnect._region)])
        threaded = aconnect.getMultiThread()
        objs=[]
        lfound=[]
        rows=[]
        #processes = mp.cpu_count()*2
        #p = mp.Pool(processes)
        #m = mp.Manager(processes=processes*2)
        #q = m.Queue(processes*2)
        #print itemlist
        pools=2  #171.35 seconds  #168 seconds
        totalItems = len(itemlist)
        if threaded:
            pools= auditMeth.poolThreadNumber(totalItems, mp.cpu_count())
            if pools>0:
                p = mp.Pool(pools)
            elif pools==0:
                threaded=False
        else:
            p = mp.Pool()
            m = mp.Manager()
            q = m.Queue()
        nEnv = aconnect._env
        if totalItems>0:
            objs.append(
                ['Name[%s]' % (current.svc), 'Audit', 'Owner', 'type', 'Platform', 'SecurityGroups', 'Instance', 'Zone',
                 'VPC', 'State', 'cpu_week', 'cost','spot'])

        if not threaded:
            for unit in itemlist:
                name = unit['Name']
                account = unit['OwnerId']
                if nEnv in name or aconnect._useAccounts:
                    #p = Process(target=self.ec2Define,args=(current,aconnect,unit,name))
                    if pools==0:
                        newobjs, row = ec2Define( unit, name)
                    else:
                        getit= p.apply_async(ec2Define,(unit, name,q))
                    #getit.get()
                    lfound.append(name)
                    #newobjs,row = ec2Define(current,aconnect,unit,name)
                    #objs = objs+newobjs
                    #rows.append(row)
        else:
            #print itemlist
            lfound = [unit['Name'] for unit in itemlist]
            results = p.map(ec2Define,  ( unit for unit in itemlist )  )

        if pools > 0:
            p.close()
            p.join()
            print results
            if threaded:
                for que in results:
                    newobjs, row = que
                    #print ' compute --got[C] result', row
                    objs = objs + newobjs
                    rows.append(row)
            else:
                while not q.empty():
                    newobjs, row = q.get()
                    objs = objs + newobjs
                    #print row
                    #print newobjs
                    rows.append(row)


        return (lfound,objs,rows)


    ##############################
    #####   LAMBDA METHODS   #####
    ##############################
    def lambdaLists(self,current, aconnect):
        client = aconnect.__get_client__('lambda')
        return client.list_functions(MaxItems=1024)['Functions']

    def lambdaMissing(self,current, aconnect, itemlist,lfound):
        objs = []
        objs.append(['Name', 'Audit', 'Owner','Runtime','Role','CodeSize','MemorySize','VPC', 'Description', 'last_Modified'])
        for unit in itemlist:
            name = unit['FunctionName']
            if name in lfound:
                continue
            objs = self.lambdaDefine(current,aconnect,objs,unit,name)
            printColor(['[E] Lambda [%s] Missing correct naming....in .%s'%(name,aconnect._region)])
        return objs

    def lambdaItem(self,current, aconnect, itemlist):
        added=False
        printColor(['_____LISTING Lambdas [] now....in .%s'%(aconnect._region)])
        nEnv = aconnect._env
        lfound =[]
        objs = []
        rows=[]
        for unit in itemlist:
            name = unit['FunctionName']
            account = unit['FunctionArn']
            if nEnv in name or aconnect._useAccounts:
                lfound.append(name)
                if not added:
                    added=True
                    objs.append(['Name[%s]'%(current.svc), 'Audit', 'Owner', 'Runtime','Role','CodeSize','MemorySize','VPC', 'Description', 'last_Modified'])
                objs,row = self.lambdaDefine(current,aconnect,objs,unit,name)
                rows.append(row)
        return (lfound,objs,rows)

    def lambdaDefine(self,current,aconnect,objs,unit,name):
        audit,owner=nameCheck(current.owner,name, current.regx, aconnect._env)

        runtime = unit['Runtime']
        role = unit['Role']
        code = unit['CodeSize']
        mem = unit['MemorySize']
        vpc='none'
        if 'VpcConfig' in unit:
            if 'VpcId' in unit['VpcConfig']:
                vpc = unit['VpcConfig']['VpcId']
        des = unit['Description']
        pattern = re.compile('[\W_]+')
        des=pattern.sub('', des)
        mod = unit['LastModified']
        nt=[name,audit,owner,runtime,role.split('/')[1],code,mem,vpc,des,mod]
        objs.append(nt)
        row={'Name':name,'Audit':audit,'Owner':owner,'Runtime':runtime,'Role':role.split('/')[1],'CodeSize':code,'MemSize':mem,'VPC':vpc,'Description':des,'last_Modified':mod}
        return (objs,row)




###########################################################################
##########################  EC2 MULTI-THREAD ##############################
##############################  START  ####################################
###########################################################################

def ec2Define(unit, name=None, que=None):#current, aconnect, unit, name):
    global awsConnect, awsCurrent
    if name == None:
        name = unit['Name']
    multiThread = awsConnect.getMultiThread()
    if multiThread:
        #aconnect = Connector.callThreadedService(awsConnect._eID, awsConnect._env, awsConnect._role,)
        sts = Connector.stsClient()
        aconnect = Connector(awsConnect._env, awsConnect._eID, awsConnect._role, sts, awsConnect._region)
        aconnect.connect()
    else:
        aconnect = awsConnect
    current=awsCurrent
    #que,current, unit, name=args
    audit, owner = nameCheck(current.owner, name, current.regx, aconnect._env)
    idinstance = unit['InstanceId']
    objs = []
    os = unit['Platform']
    sgroups = unit['sgroups']
    itype = unit['InstanceType']
    multiaz = unit['Placement']['AvailabilityZone']
    vpc = 'None'
    if unit.has_key('VpcId'):
        vpc = unit['VpcId']
    state = unit['State']['Name']
    hrs = 24 * 7  # to include a week
    cpu = ec2CPU(aconnect, idinstance, hrs)
    cost = auditMeth.ec2_prices[itype]['cost']*auditMeth.ec2_hrs_month if state=='running' else 0
    print unit
    isSpot=False
    if unit.has_key('InstanceLifecycle'):
        isSpot = True if unit['InstanceLifecycle'] == 'spot' else False
    spot = 'FALSE'
    if isSpot:
        cost = cost*.5
        spot='TRUE'

    # cpu=0
    nt = [name, audit, owner, itype, os, sgroups, idinstance, multiaz, vpc, state, cpu, round(cost),spot]
    objs.append(nt)
    row = {'Name': name, 'Audit': audit, 'Owner': owner, 'Instance': idinstance, 'Platform': os,
           'SecurityGroups': sgroups, 'type': itype, 'Zone': multiaz, 'VPC': vpc, 'State': state, 'cpu_week': cpu, 'cost':round(cost),'spot':spot}
    if not multiThread:
        if que is not None:
            que.put((objs,row))
    return (objs, row)


def ec2CPU( aconnect, instance, hrs=1.5):
    end = datetime.datetime.utcnow()
    statType = 'Maximum'
    unit = 'Percent'
    maxAvg = 8
    #  period=1,440/(hrs*60*60)  1,440 = hrs/period
    # hrs=1.5
    period = (hrs * 60 * 60) / 1440
    if period < 300:
        period = 300  # or 5mins
    # period = 1600    #in Seconds no more than datapoints 1,440 can be requested
    #print '  period:: ',period
    period_min = period / 60
    minimum_logs_needed = hrs * 60 / period_min - 1  # subract 1 since init is not included time based
    # print 'min::',minimum_logs_needed
    start = end - datetime.timedelta(hours=hrs)
    cw = aconnect.__get_client__('cloudwatch')
    ddx = cw.get_metric_statistics(
        Period=period,
        StartTime=start,
        EndTime=end,
        Unit='Percent',
        MetricName='CPUUtilization',
        Namespace='AWS/EC2',
        Statistics=['Maximum'],
        Dimensions=[{'Name': 'InstanceId', 'Value': instance}]
    )
    avg = instanceAvg(ddx, maxAvg)
    # print '  >> ',avg
    # print len(ddx['Datapoints'])
    # if len(ddx['Datapoints']) < minimum_logs_needed:
    #    avg = 100
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

#########################
###  EC2 MULTI-THREAD ###
#######   END   #########
#########################



















