

import copy

from auditMeth import nameCheck
from auditMeth import printColor


import auditMeth

import re



class ApplicationService:
    def __init__(self):
        self.services = {
            'api':{'rx':auditMeth.rs_2, 'owner':'Brian', 'ref':self}
        }


    @staticmethod
    def getServices():
        c=ApplicationService()
        return c.services

    ##############################
    ###   API GATEWAY METHODS  ###
    ##############################
    def apiLists(self,current, aconnect):
        client = aconnect.__get_client__('apigateway')
        rawItems=client.get_rest_apis(limit=100)['items']
        renamedItems=[]
        for item in rawItems:
            stages = client.get_stages(restApiId=item['id'])['item']
            for stage in stages:
                cItem = copy.copy(item)
                cItem['name']='%s[-%s]'%(cItem['name'],stage['stageName'])
                cItem['stage']=stage
                renamedItems.append(cItem)
        return renamedItems

    def apiMissing(self,current, aconnect, itemlist,lfound):
        objs = []
        objs.append(['Name', 'Audit', 'Owner','Id','Description', 'StageName', 'CacheClstrEnabled','CacheClstrStatus', 'CacheClstrSize','last_Modified' ])
        for unit in itemlist:
            name = unit['name']
            if name in lfound:
                continue
            objs = self.apiDefine(current,aconnect,objs,unit,name)
            printColor(['[E] apiGateway [%s] Missing correct naming....in .%s'%(name,aconnect._region)])
        return objs
    def apiItem(self,current, aconnect, itemlist):
        added=False
        printColor(['_____LISTING apiGateway [] now....in .%s'%(aconnect._region)])
        objs = []
        rows=[]
        lfound =[]
        nEnv = aconnect._env
        for unit in itemlist:
            name = unit['name']
            account = ''
            if nEnv in name or aconnect._useAccounts:
                lfound.append(name)
                if not added:
                    added=True
                    objs.append(['Name[%s]'%(current.svc), 'Audit', 'Owner','Id','Description', 'StageName', 'CacheClstrEnabled','CacheClstrStatus', 'CacheClstrSize','last_Modified' ])
                objs,row = self.apiDefine(current,aconnect,objs,unit,name)
                rows.append(row)
        return (lfound,objs, rows)
    def apiDefine(self,current,aconnect,objs,unit,name):
        print current.regx
        audit,owner=nameCheck(current.owner,name.split('[')[0], current.regx, aconnect._env)
        api_id = unit['id']
        sname = unit['stage']['stageName']
        ccenabled=unit['stage']['cacheClusterEnabled']
        ccstatus=unit['stage']['cacheClusterStatus']
        ccsize=''
        if unit['stage'].has_key('cacheClusterSize'):
            ccsize=unit['stage']['cacheClusterSize']
        des=''
        if unit.has_key('description'):
            des = unit['description']
            pattern = re.compile('[\W_]+')
            des=pattern.sub('', des)

        dd = unit['stage']['lastUpdatedDate']
        mod = dd.strftime('%M,%d %Y')
        nt=[name,audit,owner,api_id,des,sname,ccenabled,ccstatus,ccsize,mod]
        objs.append(nt)
        row={'Name':name,'Audit':audit,'Owner':owner,'Id':api_id,'Description':des,'StageName':sname,'CacheEnabled':ccenabled,'CacheStatus':ccstatus,'CacheSize':ccsize,'Last_Modified':mod}
        return (objs,row)


