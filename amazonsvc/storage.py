
import copy


from auditMeth import nameCheck
from auditMeth import printColor
from auditMeth import sizeof_fmt


from datetime import datetime, timedelta

import auditMeth




class Storage:
    def __init__(self):
        self.services = {
            's3': {'rx': auditMeth.rs_4, 'owner': 'Kathy','ref':self}
        }
        self.global_accounts=None

    @staticmethod
    def getServices():
        c = Storage()
        return c.services



    ##############################
    #####   S3 METHODS   #####
    ##############################
    def s3Lists(self,current, aconnect):
        #aws_rsrc['a_%s_%s'%(svc,envs)] = awsClient(self.parent.getCredential(),'s3',region)
        client = aconnect.__get_client__(current.svc)
        #joinRecordList( aws_rsrc,svc,envs, aws_rsrc['a_%s_%s'%(svc,envs)].list_functions()['Functions'])
        rawItems=client.list_buckets()['Buckets']
        renamedItems=[]
        for item in rawItems:
            cItem = copy.copy(item)
            #cloudwatch = awsClient(self.parent.getCredential(),'cloudwatch',current.region)
            cloudwatch = aconnect.__get_client__('cloudwatch')
            response = cloudwatch.get_metric_statistics(Namespace="AWS/S3",MetricName="BucketSizeBytes",
                        Dimensions=[{"Name": "BucketName","Value": item['Name']},
                        {"Name": "StorageType","Value": "StandardStorage"}],
                        StartTime=datetime.now() - timedelta(days=1),
                        EndTime=datetime.now(),Period=86400,Statistics=['Average']
                        )
            bucket_size_bytes=0
            if len(response['Datapoints'])>0:
                if response['Datapoints'][-1].has_key('Average'):
                    bucket_size_bytes = response['Datapoints'][-1]['Average']
            cItem['size']=bucket_size_bytes
            renamedItems.append(cItem)
        return renamedItems

    def s3Missing(self,current, aconnect, itemlist,lfound):
        objs=[]
        objs.append(['Name', 'Audit', 'Owner','Size'])
        for unit in itemlist:
            name = unit['Name']
            if name in lfound:
                continue
            objs = self.s3Define(current,aconnect, objs, unit, name)
            printColor(['[E] s3 [%s] Missing correct naming....in .%s'%(name,aconnect._region)])
        return objs

    def s3Item(self,current, aconnect, itemlist):
        added=False
        printColor(['_____LISTING s3 [] now....in .%s'%(aconnect._region)])
        lfound =[]
        objs = []
        rows = []
        nEnv = aconnect._env
        for unit in itemlist:
            name = unit['Name']
            account = ''#unit['StackId'] cleint.get_bucket_policy(Bucket=l['Name'])['Policy']['Statement']
            if nEnv in name or aconnect._useAccounts:
                lfound.append(name)
                if not added:
                    added=True
                    objs.append(['Name[%s]'%(current.svc),'Audit', 'Owner', 'Size'])
                objs,row = self.s3Define(current,aconnect, objs, unit, name)
                rows.append(row)
        return (lfound,objs,rows)

    def s3Define(self,current,aconnect,objs,unit,name):
        audit,owner=nameCheck(current.owner,name,current.regx,aconnect._env)
        size = sizeof_fmt(unit['size'])
        nt=[name,audit,owner,size]
        objs.append(nt)
        row ={'Name':name,'Audit':audit,'Owner':owner,'Size':size}
        return (objs,row)



