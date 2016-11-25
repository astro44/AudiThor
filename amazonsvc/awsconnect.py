
import boto3

stsClient = None
def stsClient_init():
    global stsClient
    stsClient = boto3.client('sts')


class awsConnect:

    def __init__(self, account_id, eID, role, sts_client,region, multiaccounts=True, multiThread=False):
        """

        :type session: boto3.Session
        """
        self._multiThread=multiThread
        self._useAccounts = multiaccounts
        self._credential=None
        self._resources = {}
        self._clients = {}
        self._env = account_id
        self._eID = eID
        self._role = role
        self._sts_client = sts_client
        self._session = None
        #self._session = self.sessionDefault() if eID is None else self.sessionCreate()
        #print '...how are you',self._session
        self._region = region

    def getMultiThread(self):
        return self._multiThread

    def __get_resource__(self, service=""):
        if not self._resources.has_key(service):
            self._resources[service] = self._session.resource(service)
        return self._resources[service]

    def __get_client__(self, service=""):
        if not self._resources.has_key(service):
            self._clients[service] = self._session.client(service)
        return self._clients[service]

    def connect(self):
        self._session = self.sessionDefault() if self._eID is None else self.sessionCreate()
        #print '...srry..==', self._session

    def sessionCreate(self):
        cred = self.getCredential()
        self._session = boto3.Session(aws_access_key_id=cred['AccessKeyId'],
                                aws_secret_access_key=cred['SecretAccessKey'],
                                aws_session_token=cred['SessionToken'])
        return self._session

    def sessionDefault(self):
        self._session = boto3._get_default_session()
        return self._session

    def getCredential(self):
        if self._credential:
            return self._credential
        self._credential = awsConnect.assumedCredentials(self._sts_client, self._eID, self._env, self._role)
        return self._credential



    @staticmethod
    def stsClient():
        return boto3.client('sts')
    @staticmethod
    def assumedCredentials(stsClient, externalID, accountID, role='Cross_Deployer'):
        #print '   ....[IN]  CONNECTION PENDING FOR..',accountID
        #print 'rolein: ',role
        assumedRoleObject = stsClient.assume_role(
            #RoleArn="arn:aws:iam::%s:role/Cross_Deployer" % (str(accountID)),
            RoleArn="arn:aws:iam::%s:role/%s" % (str(accountID), role),
            RoleSessionName="AssumeAdministratorRole",
            ExternalId=externalID)
        # ExternalId=global_accounts[(accountID)]['eID'])
        return assumedRoleObject['Credentials']



    @staticmethod
    def callThreadedService(eID,env,role,svc,region):
        stsClient = boto3.client('sts')
        cred = awsConnect.assumedCredentials(stsClient,eID,env,role)
        session = boto3.Session(aws_access_key_id=cred['AccessKeyId'],
                                aws_secret_access_key=cred['SecretAccessKey'],
                                aws_session_token=cred['SessionToken'])
        client=session.client(svc,region)
        return (client,session)


    @staticmethod
    def awsClient(cred, svc, region):
        if cred:
            client = boto3.client(svc, region,
                                  aws_access_key_id=cred['AccessKeyId'],
                                  aws_secret_access_key=cred['SecretAccessKey'],
                                  aws_session_token=cred['SessionToken'])
        else:
            client = boto3.client(svc, region)
        return client

    @staticmethod
    def getAWSCredentials(self):
        pathtoaws = '/var/root/.aws/credentials'
        awskey = awssecretkey = None
        with open(pathtoaws) as f:
            for line in f:
                if "aws_access_key_id" in line:
                    awskey = line.replace("aws_access_key_id=", "")
                    awskey = awskey.replace("\n", "")
                    # print '   aws_access_key_id: %s'%(awskey)
                if "aws_secret_access_key" in line:
                    awssecretkey = line.replace("aws_secret_access_key=", "")
                    awssecretkey = awssecretkey.replace("\n", "")
                    # print '   aws_secret_access_key: %s'%(awssecretkey)

        output = [awskey, awssecretkey]
        return output