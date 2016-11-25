

from auditMeth import nameCheck
from auditMeth import printColor



import auditMeth




class Management:
    def __init__(self):
        self.services = {
            'cloudformation': {'rx': auditMeth.rs_4, 'owner': 'philip','ref':self}
                }
        self.global_accounts=None

    @staticmethod
    def getServices():
        c = Management()
        return c.services

    #########################################
    #####   CLOUD FORMATION   METHODS   #####
    #########################################
    def cloudformationLists(self,current, aconnect):
        client = aconnect.__get_client__(current.svc)
        #aws_rsrc['a_%s_%s'%(svc,envs)] = awsClient(self.parent.getCredential(),'cloudformation',region)
        #joinRecordList( aws_rsrc,svc,envs, aws_rsrc['a_%s_%s'%(svc,envs)].list_functions()['Functions'])
        rawItems=client.list_stacks()['StackSummaries']
        renamedItems=[]
        for item in rawItems:
            if item.has_key('DeletionTime'):
                continue
            renamedItems.append(item)
        #aws_rsrc['l_%s'%(svc)]=renamedItems
        return renamedItems

    def cloudformationMissing(self,current, aconnect, itemlist,lfound):
        objs=[]
        objs.append(['Name', 'Audit', 'Owner', 'Account','Status', 'Description', 'last_Modified'])
        for unit in itemlist:
            name = unit['StackName']
            if name in lfound:
                continue
            objs = self.cloudformationDefine(current,aconnect, objs, unit, name)
            printColor(['[E] ELB [%s] Missing correct naming....in .%s'%(name,aconnect._region)])
        return objs

    def cloudformationItem(self,current, aconnect, itemlist):
        added=False
        printColor(['_____LISTING CloudFORMATION [] now....in .%s'%(aconnect._region)])
        nEnv = aconnect._env
        objs = []
        lfound =[]
        rows =[]
        for unit in itemlist:
            name = unit['StackName']
            account = unit['StackId']
            if nEnv in name or aconnect._useAccounts:
                lfound.append(name)
                if not added:
                    added=True
                    objs.append(['Name[%s]'%(current.svc), 'Audit', 'Owner', 'Account','Status', 'Description', 'last_Modified'])
                objs,row = self.cloudformationDefine(current,aconnect, objs, unit, name)
                rows.append(row)
        return (lfound,objs,rows)

    def cloudformationDefine(self,current,aconnect,objs,unit,name):
        #global global_accounts
        audit,owner=nameCheck(current.owner,name,current.regx,aconnect._env)
        status = unit['StackStatus']
        stackid = unit['StackId']
        account=''
        for acct in self.global_accounts:
            if acct in stackid:
                account="%s:%s"%(self.global_accounts[(acct)]['all'],acct)
                break
        mod='N/A'
        if unit.has_key('LastUpdatedTime'):
            dd = unit['LastUpdatedTime']
            mod = dd.strftime('%m,%d %Y')
        des='None'
        if unit.has_key('TemplateDescription'):
            des= unit['TemplateDescription']
        nt=[name,audit,owner,account, status, des, mod ]
        objs.append(nt)
        row={'Name':name,'Audit':audit,'Owner':owner,'Account':account, 'Status':status, 'Description':des, 'last_Modified':mod}
        return (objs,row)


